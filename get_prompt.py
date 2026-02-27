#!/usr/bin/env python3
"""
get_prompt.py - Claude.ai 用プロンプト生成スクリプト

Usage:
  python3 get_prompt.py --count 100
  python3 get_prompt.py --count 100 --lv1 15 --lv2 25 --lv3 30 --lv4 20 --lv5 10
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

QUESTIONS_JS = Path(__file__).parent / "listening" / "questions.js"


def load_existing_texts():
    """questions.js から既存の text フィールド一覧を取得"""
    if not QUESTIONS_JS.exists():
        print(f"ERROR: {QUESTIONS_JS} が見つかりません", file=sys.stderr)
        sys.exit(1)

    content = QUESTIONS_JS.read_text(encoding="utf-8")

    # text フィールドを正規表現で抽出
    # questions.js は JavaScript オブジェクト記法（キーにクォートなし）
    texts = re.findall(r'\btext:\s*"((?:[^"\\]|\\.)*)"', content)
    if not texts:
        # シングルクォートの場合も試みる
        texts = re.findall(r"\btext:\s*'((?:[^'\\]|\\.)*)'", content)

    return texts


def build_prompt(count, lv1, lv2, lv3, lv4, lv5, existing_texts):
    """Claude.ai 用プロンプトを生成"""

    existing_list = json.dumps(existing_texts, ensure_ascii=False, indent=2)

    prompt = f"""以下のJSON形式でリスニングクイズの問題を{count}問生成してください。

## 難易度の内訳
- lv1（超簡単・日常の短い1文）: {lv1}問
- lv2（簡単）: {lv2}問
- lv3（普通）: {lv3}問
- lv4（難しい）: {lv4}問
- lv5（非常に難しい・速い/崩れた英語）: {lv5}問

## 難易度の微差（axis フィールド）
各問題に以下のいずれかを1つ割り当て、{count}問全体で均等に分散させること（各約{count//5}問）：
- speed    : 発話が速い・詰まった話し方（"Didja hear that?" "Gonna hafta leave." 等）
- reduction: gonna/wanna/kinda/dunno/lemme 等の音変化・リンキング・脱落
- vocab    : 低頻度語・イディオム・スラング・比喩表現
- context  : 前後の文脈・話者のトーン・感情から正解を推論する必要がある
- distractor: 誤答が非常に紛らわしく、表面的な理解では正解できない

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
- 既存テーマとの重複を避けてください（テーマ例: 交通・飲食店・職場・家庭・天気・ショッピング・健康）
- JSON のみ出力（説明文・コードブロック記号不要）

## 既存問題リスト（重複禁止）
以下は既存問題の英文リストです。同じ英文・同じ場面・同じシチュエーションの問題は
絶対に作らないでください（完全一致だけでなく類似した場面も避けること）：

{existing_list}
"""
    return prompt


def copy_to_clipboard(text):
    """macOS の pbcopy でクリップボードにコピー"""
    try:
        process = subprocess.Popen(
            ["pbcopy"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.communicate(input=text.encode("utf-8"))
        return True
    except Exception as e:
        print(f"pbcopy エラー: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Claude.ai 用プロンプト生成")
    parser.add_argument("--count", type=int, default=100, help="生成問題数（デフォルト: 100）")
    parser.add_argument("--lv1", type=int, default=None, help="lv1 問題数")
    parser.add_argument("--lv2", type=int, default=None, help="lv2 問題数")
    parser.add_argument("--lv3", type=int, default=None, help="lv3 問題数")
    parser.add_argument("--lv4", type=int, default=None, help="lv4 問題数")
    parser.add_argument("--lv5", type=int, default=None, help="lv5 問題数")
    args = parser.parse_args()

    count = args.count

    # デフォルトのレベル分布（合計 = count に按分）
    # 100問: lv1=15, lv2=25, lv3=30, lv4=20, lv5=10
    default_ratios = [0.15, 0.25, 0.30, 0.20, 0.10]

    if args.lv1 is not None or args.lv2 is not None or args.lv3 is not None \
            or args.lv4 is not None or args.lv5 is not None:
        # 個別指定がある場合は指定値を使用（未指定は 0）
        lv1 = args.lv1 or 0
        lv2 = args.lv2 or 0
        lv3 = args.lv3 or 0
        lv4 = args.lv4 or 0
        lv5 = args.lv5 or 0
        total = lv1 + lv2 + lv3 + lv4 + lv5
        if total != count:
            print(f"WARNING: 各レベルの合計 ({total}) が --count ({count}) と一致しません")
    else:
        # デフォルト按分
        lv1 = round(count * default_ratios[0])
        lv2 = round(count * default_ratios[1])
        lv3 = round(count * default_ratios[2])
        lv4 = round(count * default_ratios[3])
        lv5 = count - lv1 - lv2 - lv3 - lv4  # 残りを lv5 に

    print(f"既存問題を読み込み中: {QUESTIONS_JS}")
    existing_texts = load_existing_texts()
    print(f"既存問題数: {len(existing_texts)} 問")

    print(f"\n生成設定: {count}問 (lv1:{lv1} lv2:{lv2} lv3:{lv3} lv4:{lv4} lv5:{lv5})")

    prompt = build_prompt(count, lv1, lv2, lv3, lv4, lv5, existing_texts)

    if copy_to_clipboard(prompt):
        print("\n✅ プロンプトをクリップボードにコピーしました。")
        print("   Claude.ai に貼り付けて実行してください。")
        print("   出力された JSON を listening/staging.json に保存してから、")
        print("   python3 add_questions.py を実行してください。")
    else:
        print("\nプロンプト（手動コピーしてください）:")
        print("=" * 60)
        print(prompt)


if __name__ == "__main__":
    main()
