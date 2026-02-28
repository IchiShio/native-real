#!/usr/bin/env python3
"""
check_batch.py - Batch API の結果を確認 → staging.json に保存 → add_questions.py を自動実行

Usage:
  python3 check_batch.py           # 状態確認 + 完了なら自動処理
  python3 check_batch.py --status  # 状態確認のみ（staging.json に保存しない）
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic がインストールされていません")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from lib import parse_response  # noqa: E402

REPO_ROOT = Path(__file__).parent
STAGING_JSON = REPO_ROOT / "listening" / "staging.json"
BATCH_STATE = REPO_ROOT / "listening" / "batch_state.json"


def deduplicate(questions):
    """text フィールドで重複を除去"""
    seen = set()
    unique = []
    for q in questions:
        t = q["text"].strip().lower()
        if t not in seen:
            seen.add(t)
            unique.append(q)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Batch API の結果確認・取得")
    parser.add_argument("--status", action="store_true", help="状態確認のみ（保存しない）")
    args = parser.parse_args()

    if not BATCH_STATE.exists():
        print("未処理の Batch ジョブがありません")
        print("先に python3 generate_questions.py --batch を実行してください")
        sys.exit(0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    state = json.loads(BATCH_STATE.read_text())
    batch_id = state["batch_id"]
    submitted_at = state.get("submitted_at", "不明")

    print(f"Batch ID: {batch_id}")
    print(f"投入日時: {submitted_at}")
    print(f"予定問題数: {state['count']} 問")
    print(f"モデル: {state.get('model', '不明')}")

    client = anthropic.Anthropic(api_key=api_key)

    # ステータス確認
    batch = client.messages.batches.retrieve(batch_id)
    status = batch.processing_status

    counts = batch.request_counts
    print(f"\n処理状況: {status}")
    print(f"  処理済み: {counts.succeeded} 件 / 全{counts.succeeded + counts.errored + counts.canceled + counts.expired} 件")
    if counts.errored:
        print(f"  エラー: {counts.errored} 件")

    if status != "ended":
        print("\nまだ処理中です。しばらく待ってから再度実行してください。")
        sys.exit(0)

    if args.status:
        print("\n--status モードのため保存をスキップします")
        sys.exit(0)

    # 結果取得
    print("\n結果を取得中...")
    all_questions = []
    error_count = 0

    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            raw = result.result.message.content[0].text
            questions = parse_response(raw, raise_on_error=False)
            all_questions.extend(questions)
            print(f"  {result.custom_id}: {len(questions)} 問 取得")
        else:
            error_count += 1
            print(f"  {result.custom_id}: ERROR ({result.result.type})", file=sys.stderr)

    if error_count:
        print(f"\nWARNING: {error_count} 件のリクエストが失敗しました")

    if not all_questions:
        print("ERROR: 有効な問題を取得できませんでした", file=sys.stderr)
        sys.exit(1)

    # 重複除去
    before = len(all_questions)
    all_questions = deduplicate(all_questions)
    removed = before - len(all_questions)
    if removed:
        print(f"\n重複除去: {removed} 問を除去（{before} → {len(all_questions)} 問）")

    # staging.json に保存
    STAGING_JSON.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n✅ {len(all_questions)} 問を listening/staging.json に保存しました")

    # batch_state.json を削除
    BATCH_STATE.unlink()
    print("✅ batch_state.json を削除しました")

    # add_questions.py を自動実行
    print("\nadd_questions.py を実行します...")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "add_questions.py")],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("ERROR: add_questions.py が失敗しました", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
