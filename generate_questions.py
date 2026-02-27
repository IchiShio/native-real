#!/usr/bin/env python3
"""
generate_questions.py - Claude API で問題を自動生成 → staging.json に保存

通常モード（即時・数分）:
  python3 generate_questions.py --count 100
  python3 generate_questions.py --count 100 --model claude-sonnet-4-6

axis 指定モード（特定の axis だけ集中生成）:
  python3 generate_questions.py --count 100 --axis-only speed,reduction
  python3 generate_questions.py --count 50 --axis-only speed

Batch モード（24時間以内・50%オフ）:
  python3 generate_questions.py --count 100 --batch
  python3 generate_questions.py --count 100 --batch --model claude-sonnet-4-6
  → 翌日: python3 check_batch.py
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic がインストールされていません")
    print("  pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

QUESTIONS_JS = Path(__file__).parent / "listening" / "questions.js"
STAGING_JSON = Path(__file__).parent / "listening" / "staging.json"
BATCH_STATE = Path(__file__).parent / "listening" / "batch_state.json"

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
BATCH_SIZE = 30

VALID_FIELDS = {"diff", "text", "ja", "answer", "choices", "expl", "kp"}
VALID_DIFFS = {"lv1", "lv2", "lv3", "lv4", "lv5"}

# exclude リストの上限（プロンプトサイズを 200K トークン以下に抑えるため）
# 1問 ≈ 25 tokens、200K / 25 ≈ 8,000問が限界。余裕をもって 3,000 問に制限。
EXCLUDE_LIMIT = 3000


def load_existing_texts():
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    texts = re.findall(r'\btext:\s*"((?:[^"\\]|\\.)*)"', content)
    # 直近 EXCLUDE_LIMIT 問のみ渡す（プロンプトサイズ抑制）
    if len(texts) > EXCLUDE_LIMIT:
        texts = texts[-EXCLUDE_LIMIT:]
    return texts


AXIS_DESCRIPTIONS = {
    "speed":      'speed    : 発話が速い・詰まった話し方（"Didja hear that?" "Gonna hafta leave." 等）',
    "reduction":  "reduction: gonna/wanna/kinda/dunno/lemme 等の音変化・リンキング・脱落",
    "vocab":      "vocab    : 低頻度語・イディオム・スラング・比喩表現",
    "context":    "context  : 前後の文脈・話者のトーン・感情から正解を推論する必要がある",
    "distractor": "distractor: 誤答が非常に紛らわしく、表面的な理解では正解できない",
}


def build_prompt(count, lv1, lv2, lv3, lv4, lv5, existing_texts, axis_only=None):
    existing_list = json.dumps(existing_texts, ensure_ascii=False, indent=2)

    if axis_only:
        per = count // len(axis_only)
        axis_lines = "\n".join(f"- {AXIS_DESCRIPTIONS[a]}" for a in axis_only)
        axis_instruction = (
            f"各問題に以下の axis のいずれかを割り当て、{count}問全体で均等に分散させること"
            f"（各約{per}問）：\n{axis_lines}"
        )
    else:
        axis_lines = "\n".join(f"- {d}" for d in AXIS_DESCRIPTIONS.values())
        axis_instruction = (
            f"各問題に以下のいずれかを1つ割り当て、{count}問全体で均等に分散させること（各約{count//5}問）：\n{axis_lines}"
        )

    return f"""以下のJSON形式でリスニングクイズの問題を{count}問生成してください。

## 難易度の内訳
- lv1（超簡単・日常の短い1文）: {lv1}問
- lv2（簡単）: {lv2}問
- lv3（普通）: {lv3}問
- lv4（難しい）: {lv4}問
- lv5（非常に難しい・速い/崩れた英語）: {lv5}問

## 難易度の微差（axis フィールド）
{axis_instruction}

## 出力形式（JSONのみ出力、他の文章は不要）
[
  {{
    "diff": "lv1〜lv5のいずれか",
    "axis": "speed | reduction | vocab | context | distractor のいずれか",
    "text": "英語音声スクリプト（ネイティブの自然な発話）",
    "ja": "日本語仮訳（短く自然に）",
    "answer": "何をしている/言っている場面かの日本語説明（15〜25字）",
    "choices": ["正解", "誤答1", "誤答2", "誤答3", "誤答4"],
    "expl": "なぜ正解なのかの日本語解説（1〜2文）",
    "kp": ["聴き取りのカギになるフレーズ1〜2個"]
  }}
]

## 制約
- text はネイティブが実際に使う自然な英語（略語・短縮形OK）
- axis の特性を text と choices の両方に反映させること
- choices は正解が1つ、残り4つは紛らわしい誤答
- choices の順序はランダムに（正解を先頭にしない）
- 既存テーマとの重複を避けること（テーマ例: 交通・飲食店・職場・家庭・天気・ショッピング・健康）
- JSON のみ出力（説明文・コードブロック記号不要）

## 既存問題リスト（重複禁止）
以下は既存問題の英文リストです。同じ英文・同じ場面・同じシチュエーションの問題は
絶対に作らないでください（完全一致だけでなく類似した場面も避けること）：

{existing_list}
"""


def parse_response(raw):
    """APIレスポンスの文字列を問題リストにパース・バリデーション"""
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        last_obj_end = raw.rfind("},")
        if last_obj_end > 0:
            try:
                questions = json.loads(raw[:last_obj_end + 1] + "\n]")
                print(f"  WARNING: レスポンスが途中で切れたため {len(questions)} 問のみ取得")
                return questions
            except json.JSONDecodeError:
                pass
        raise

    valid = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if VALID_FIELDS - set(q.keys()):
            continue
        if q.get("diff") not in VALID_DIFFS:
            continue
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 5:
            continue
        valid.append(q)
    return valid


def split_levels(total_lv, remaining, batch_count):
    total = sum(total_lv)
    if total == 0:
        return [0, 0, batch_count, 0, 0]
    batch = [round(x * batch_count / total) for x in total_lv]
    diff = batch_count - sum(batch)
    batch[2] = max(0, batch[2] + diff)
    return batch


def run_normal(client, model, count, lv, existing_texts, axis_only=None):
    """通常モード: 即時実行"""
    all_questions = []
    remaining_lv = list(lv)
    remaining = count
    batch_num = 1
    total_batches = -(-count // BATCH_SIZE)

    while remaining > 0:
        batch_count = min(remaining, BATCH_SIZE)
        bl = split_levels(remaining_lv, remaining, batch_count)
        bl1, bl2, bl3, bl4, bl5 = bl

        print(f"\n[{batch_num}/{total_batches}] {batch_count}問 "
              f"(lv1:{bl1} lv2:{bl2} lv3:{bl3} lv4:{bl4} lv5:{bl5}) 生成中...")

        exclude = existing_texts + [q["text"] for q in all_questions]
        prompt = build_prompt(batch_count, bl1, bl2, bl3, bl4, bl5, exclude, axis_only=axis_only)

        try:
            resp = client.messages.create(
                model=model, max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            questions = parse_response(resp.content[0].text)
            all_questions.extend(questions)
            print(f"  ✅ {len(questions)}問 取得（累計: {len(all_questions)}問）")
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            if all_questions:
                print(f"  取得済みの {len(all_questions)} 問を保存して終了します")
                break
            sys.exit(1)

        for i in range(5):
            remaining_lv[i] = max(0, remaining_lv[i] - bl[i])
        remaining -= batch_count
        batch_num += 1

    return all_questions


def run_batch(client, model, count, lv, existing_texts, axis_only=None):
    """Batch モード: ジョブ投入のみ（結果は check_batch.py で取得）"""
    if BATCH_STATE.exists():
        state = json.loads(BATCH_STATE.read_text())
        print(f"ERROR: 未処理のバッチが存在します (ID: {state['batch_id']})")
        print("  先に python3 check_batch.py を実行してください")
        sys.exit(1)

    # 全リクエストのプロンプトを一括作成
    requests = []
    remaining_lv = list(lv)
    remaining = count
    req_idx = 0

    while remaining > 0:
        batch_count = min(remaining, BATCH_SIZE)
        bl = split_levels(remaining_lv, remaining, batch_count)
        bl1, bl2, bl3, bl4, bl5 = bl

        prompt = build_prompt(batch_count, bl1, bl2, bl3, bl4, bl5, existing_texts, axis_only=axis_only)
        requests.append({
            "custom_id": f"req-{req_idx}",
            "params": {
                "model": model,
                "max_tokens": MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            },
            "_meta": {"count": batch_count, "lv": bl},  # 後で取り除く
        })

        for i in range(5):
            remaining_lv[i] = max(0, remaining_lv[i] - bl[i])
        remaining -= batch_count
        req_idx += 1

    # _meta は Anthropic API に渡さない
    api_requests = [
        {"custom_id": r["custom_id"], "params": r["params"]}
        for r in requests
    ]
    meta_map = {r["custom_id"]: r["_meta"] for r in requests}

    print(f"\nBatch API にジョブ投入中... ({len(api_requests)} リクエスト)")
    batch = client.messages.batches.create(requests=api_requests)

    state = {
        "batch_id": batch.id,
        "model": model,
        "count": count,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "requests": [
            {"custom_id": cid, **meta}
            for cid, meta in meta_map.items()
        ],
    }
    BATCH_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    print(f"✅ Batch 投入完了")
    print(f"   Batch ID: {batch.id}")
    print(f"   リクエスト数: {len(api_requests)} 件（合計 {count} 問）")
    print(f"   処理時間: 最大24時間")
    print(f"\n翌日以降に以下を実行してください:")
    print(f"  cd /Users/yusuke/projects/claude/eikaiwa-hikaku && python3 check_batch.py")


def main():
    parser = argparse.ArgumentParser(description="Claude API で問題を生成して staging.json に保存")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--lv1", type=int, default=None)
    parser.add_argument("--lv2", type=int, default=None)
    parser.add_argument("--lv3", type=int, default=None)
    parser.add_argument("--lv4", type=int, default=None)
    parser.add_argument("--lv5", type=int, default=None)
    parser.add_argument("--batch", action="store_true",
                        help="Batch API を使用（24時間以内・50%%オフ）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"使用モデル（デフォルト: {DEFAULT_MODEL}）")
    parser.add_argument("--axis-only", default=None,
                        help="生成する axis をカンマ区切りで指定（例: speed,reduction）")
    args = parser.parse_args()

    VALID_AXES = {"speed", "reduction", "vocab", "context", "distractor"}
    axis_only = None
    if args.axis_only:
        axis_only = [a.strip() for a in args.axis_only.split(",")]
        invalid = [a for a in axis_only if a not in VALID_AXES]
        if invalid:
            print(f"ERROR: 無効な axis: {invalid}")
            print(f"  有効な値: {sorted(VALID_AXES)}")
            sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        print("  .env ファイルに ANTHROPIC_API_KEY=your_key を追加してください")
        sys.exit(1)

    count = args.count
    default_ratios = [0.15, 0.25, 0.30, 0.20, 0.10]
    if any(x is not None for x in [args.lv1, args.lv2, args.lv3, args.lv4, args.lv5]):
        lv = [args.lv1 or 0, args.lv2 or 0, args.lv3 or 0, args.lv4 or 0, args.lv5 or 0]
    else:
        lv = [round(count * r) for r in default_ratios]
        lv[4] = count - sum(lv[:4])

    lv1, lv2, lv3, lv4, lv5 = lv
    mode = "Batch（50%オフ・24時間）" if args.batch else "通常（即時）"
    print(f"生成設定: {count}問 (lv1:{lv1} lv2:{lv2} lv3:{lv3} lv4:{lv4} lv5:{lv5})")
    print(f"モデル: {args.model}  モード: {mode}")
    if axis_only:
        print(f"axis 指定: {axis_only}（これらのみ生成）")

    existing_texts = load_existing_texts()
    print(f"既存問題数: {len(existing_texts)} 問")

    client = anthropic.Anthropic(api_key=api_key)

    if args.batch:
        run_batch(client, args.model, count, lv, existing_texts, axis_only=axis_only)
    else:
        all_questions = run_normal(client, args.model, count, lv, existing_texts, axis_only=axis_only)
        if not all_questions:
            print("ERROR: 問題を1問も生成できませんでした", file=sys.stderr)
            sys.exit(1)

        STAGING_JSON.write_text(
            json.dumps(all_questions, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n✅ {len(all_questions)}問 を listening/staging.json に保存しました")
        print("次のステップ:")
        print("  cd /Users/yusuke/projects/claude/eikaiwa-hikaku && python3 add_questions.py")


if __name__ == "__main__":
    main()
