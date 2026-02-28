#!/usr/bin/env python3
"""
add_questions.py - staging.json の問題を自動処理して本番追加

処理フロー:
  1. listening/staging.json 読み込み・バリデーション
  2. 現在の questions.js から問題数を取得
  3. 各問題に audio フィールドを付与（q{existing+n}.mp3）
  4. edge-tts で MP3 生成
  5. questions.js 末尾の ]; の前に新問題を追記
  6. git add . && git commit && git push
  7. staging.json をクリア（空配列）
"""

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "listening" / "questions.js"
STAGING_JSON = REPO_ROOT / "listening" / "staging.json"
AUDIO_DIR = REPO_ROOT / "listening" / "audio"

# 5種音声ローテーション（edge-tts ボイス名）
VOICES = [
    "en-US-AriaNeural",      # US female
    "en-GB-SoniaNeural",     # UK female
    "en-US-GuyNeural",       # US male
    "en-AU-NatashaNeural",   # AU female
    "en-GB-RyanNeural",      # UK male
]

from lib import VALID_FIELDS, VALID_DIFFS


def load_staging():
    """staging.json を読み込んでバリデーション"""
    if not STAGING_JSON.exists():
        print(f"ERROR: {STAGING_JSON} が見つかりません", file=sys.stderr)
        sys.exit(1)

    content = STAGING_JSON.read_text(encoding="utf-8").strip()
    if not content or content == "[]":
        print("staging.json が空です。Claude.ai の出力を保存してから実行してください。")
        sys.exit(0)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: staging.json の JSON パースエラー: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("ERROR: staging.json はリスト形式である必要があります", file=sys.stderr)
        sys.exit(1)

    print(f"staging.json から {len(data)} 問を読み込みました")

    # バリデーション
    errors = []
    auto_fixed = []
    for i, q in enumerate(data):
        missing = VALID_FIELDS - set(q.keys())
        if missing:
            errors.append(f"  [{i}] 必須フィールドが不足: {missing}")
        if q.get("diff") not in VALID_DIFFS:
            errors.append(f"  [{i}] diff が不正: {q.get('diff')}")
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 5:
            errors.append(f"  [{i}] choices は5要素のリストが必要")
        if not isinstance(q.get("kp"), list) or len(q["kp"]) == 0:
            errors.append(f"  [{i}] kp は1要素以上のリストが必要")
        # answer === choices[0] を確認（最重要）
        # 設計: 正解は常に choices[0]。JS が表示時にシャッフルするため順番は問題なし。
        choices = q.get("choices", [])
        if isinstance(choices, list) and len(choices) > 0:
            if q.get("answer") != choices[0]:
                original = q.get("answer", "")
                # answer が choices 内に存在するならその位置と choices[0] をスワップ
                if original in choices:
                    idx = choices.index(original)
                    choices[0], choices[idx] = choices[idx], choices[0]
                    q["choices"] = choices
                    auto_fixed.append(f"  [{i}] choices をスワップ: choices[0]↔choices[{idx}]（answer=\"{original}\"）")
                else:
                    # choices に存在しない場合は choices[0] に上書き
                    q["answer"] = choices[0]
                    auto_fixed.append(f"  [{i}] answer を自動補正: \"{original}\" → \"{choices[0]}\"")

    if auto_fixed:
        print("WARNING: answer/choices 不整合を自動補正しました:")
        for msg in auto_fixed:
            print(msg)

    if errors:
        print("ERROR: バリデーションエラー:")
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    return data


def get_existing_count(content):
    """questions.js から現在の問題数を取得"""
    # audio フィールドで問題数を数える
    # questions.js は JavaScript オブジェクト記法（キーにクォートなし）
    count = len(re.findall(r'\baudio:', content))
    print(f"現在の問題数: {count} 問")
    return count


async def generate_audio_async(text, voice, output_path):
    """edge-tts で非同期 MP3 生成"""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def generate_audio(text, voice, output_path):
    """edge-tts で MP3 生成（同期ラッパー）"""
    asyncio.run(generate_audio_async(text, voice, output_path))


def format_question_js(q):
    """問題オブジェクトを questions.js 形式の1行文字列に変換"""
    choices_str = json.dumps(q["choices"], ensure_ascii=False)
    kp_str = json.dumps(q["kp"], ensure_ascii=False)

    def esc(s):
        return (s.replace("\\", "\\\\")
                 .replace('"', '\\"')
                 .replace("\n", "\\n")
                 .replace("\r", "\\r")
                 .replace("\t", "\\t"))

    axis_part = f', axis: "{esc(q["axis"])}"' if q.get("axis") else ""

    return (
        f'  {{ diff: "{q["diff"]}"{axis_part}, text: "{esc(q["text"])}", ja: "{esc(q["ja"])}", '
        f'answer: "{esc(q["answer"])}", choices: {choices_str}, '
        f'audio: "{esc(q["audio"])}", '
        f'expl: "{esc(q["expl"])}", kp: {kp_str} }}'
    )


def append_to_questions_js(content, new_questions):
    """questions.js の末尾 ]; の前に新問題を追記"""
    # ファイル末尾の ]; を正規表現で探す（文字列内の ]; に誤マッチしないよう末尾固定）
    m = re.search(r'\];\s*$', content)
    if not m:
        print("ERROR: questions.js に ]; が見つかりません", file=sys.stderr)
        sys.exit(1)
    last_bracket_pos = m.start()

    # 最後の問題の末尾（,がない場合は追加）
    before = content[:last_bracket_pos].rstrip()
    if before and not before.endswith(","):
        before += ","

    new_lines = ",\n".join(format_question_js(q) for q in new_questions)
    new_content = before + "\n" + new_lines + "\n];\n"

    QUESTIONS_JS.write_text(new_content, encoding="utf-8")


def git_commit_push(n_added, total):
    """git add . && git commit && git push"""
    cmds = [
        ["git", "-C", str(REPO_ROOT), "add", "."],
        [
            "git", "-C", str(REPO_ROOT),
            "commit", "-m",
            f"Add {n_added} questions (total: {total})"
        ],
        ["git", "-C", str(REPO_ROOT), "push"],
    ]

    for cmd in cmds:
        print(f"$ {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        if result.stdout:
            print(result.stdout.rstrip())


def main():
    # edge-tts が使えるか確認
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("ERROR: edge-tts がインストールされていません")
        print("  pip3 install edge-tts")
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. staging.json 読み込み
    staging = load_staging()

    # 2. questions.js を読み込み（以降で2回使うため1回だけ読む）
    if not QUESTIONS_JS.exists():
        print(f"ERROR: {QUESTIONS_JS} が見つかりません", file=sys.stderr)
        sys.exit(1)
    questions_js_content = QUESTIONS_JS.read_text(encoding="utf-8")
    existing_count = get_existing_count(questions_js_content)

    # 3. audio フィールドを付与
    for i, q in enumerate(staging):
        q_num = existing_count + i + 1
        # ゼロパディング: 1-9 → q1、10-99 → q10、100以上 → q100 など（拡張子なし）
        q["audio"] = f"audio/q{q_num}.mp3"

    # 4. MP3 生成
    print(f"\n音声生成開始: {len(staging)} 問")
    for i, q in enumerate(staging):
        voice = VOICES[i % len(VOICES)]
        q_num = existing_count + i + 1
        audio_filename = f"q{q_num}.mp3"
        audio_path = AUDIO_DIR / audio_filename

        if audio_path.exists():
            print(f"  [{i+1}/{len(staging)}] スキップ（既存）: {audio_filename}")
            continue

        print(f"  [{i+1}/{len(staging)}] 生成中: {audio_filename} ({voice})")
        print(f"    \"{q['text'][:50]}{'...' if len(q['text']) > 50 else ''}\"")

        try:
            generate_audio(q["text"], voice, audio_path)
            print(f"    ✅ 生成完了")
        except Exception as e:
            print(f"    ERROR: 音声生成失敗: {e}", file=sys.stderr)
            sys.exit(1)

    # 5. questions.js に追記
    print(f"\nquestions.js に {len(staging)} 問を追記中...")
    append_to_questions_js(questions_js_content, staging)
    total = existing_count + len(staging)
    print(f"✅ 追記完了（{existing_count} → {total} 問）")

    # 6. git commit & push
    print("\ngit commit & push...")
    git_commit_push(len(staging), total)
    print("✅ push 完了")

    # 7. staging.json をクリア
    STAGING_JSON.write_text("[]\n", encoding="utf-8")
    print("✅ staging.json をクリアしました")

    print(f"\n🎉 完了！ 問題数: {existing_count} → {total} 問")


if __name__ == "__main__":
    main()
