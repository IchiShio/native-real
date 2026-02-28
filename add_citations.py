#!/usr/bin/env python3
"""
引用リンク自動付与スクリプト

data/citation_db.json の検証済みURLを使い、articles/ 以下のHTMLに
引用リンクを自動で付与する。

動作仕様:
  - <a>, <style>, <script> タグの内部テキストは変更しない
  - 各引用ソースは記事内で最初のマッチ1箇所のみにリンクを付与（過剰リンク防止）
  - すでに <a href> でラップされている箇所はスキップ

使い方:
  python3 add_citations.py                # 全記事に適用
  python3 add_citations.py --dry-run      # プレビュー（ファイル更新なし）
  python3 add_citations.py articles/english-career-salary-impact  # 特定記事のみ
  python3 add_citations.py --verify       # citation_db.json の全URLを疎通確認
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

SITE_DIR = Path(__file__).parent
CITATION_DB_PATH = SITE_DIR / "data" / "citation_db.json"
ARTICLES_DIR = SITE_DIR / "articles"

# HTMLタグの正規表現（script/style ブロックを含む）
_TAG_RE = re.compile(r"(<[^>]+>)", re.DOTALL)
_OPEN_A_RE = re.compile(r"^<a\b", re.IGNORECASE)
_CLOSE_A_RE = re.compile(r"^</a\s*>$", re.IGNORECASE)
_OPEN_STYLE_RE = re.compile(r"^<style\b", re.IGNORECASE)
_CLOSE_STYLE_RE = re.compile(r"^</style\s*>$", re.IGNORECASE)
_OPEN_SCRIPT_RE = re.compile(r"^<script\b", re.IGNORECASE)
_CLOSE_SCRIPT_RE = re.compile(r"^</script\s*>$", re.IGNORECASE)


def load_citation_db() -> list[dict]:
    """citation_db.json を読み込み、適用可能なエントリのリストを返す"""
    with open(CITATION_DB_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    entries = []
    for key, val in raw.items():
        if key.startswith("_"):
            continue  # README等のメタキーはスキップ
        entries.append({"id": key, **val})
    return entries


def apply_citations_to_text(text: str, entries: list[dict], applied: set[str]) -> tuple[str, list[str]]:
    """
    テキストノードに引用リンクを付与する。
    applied: このファイルで既にリンク付与済みのエントリID集合（更新される）
    """
    changes = []
    for entry in entries:
        if entry["id"] in applied:
            continue  # 既にこの記事でリンク済み → スキップ
        url = entry["url"]
        label = entry["label"]
        for kw_pattern in entry["keywords"]:
            try:
                m = re.search(kw_pattern, text)
                if m:
                    matched_text = m.group(0)
                    link = f'<a href="{url}" target="_blank" rel="noopener">{matched_text}</a>'
                    text = text[:m.start()] + link + text[m.end():]
                    applied.add(entry["id"])
                    changes.append(f"  [{entry['id']}] 「{matched_text[:40]}」→ {url}")
                    break  # このエントリは1パターンマッチで終了
            except re.error as e:
                print(f"  ⚠ 正規表現エラー [{entry['id']}] '{kw_pattern}': {e}", file=sys.stderr)
    return text, changes


def apply_citations_to_html(html: str, entries: list[dict]) -> tuple[str, list[str]]:
    """
    HTML全体に引用リンクを付与する。
    <a>, <style>, <script> の内部テキストは変更しない。
    """
    parts = _TAG_RE.split(html)
    depth_a = 0
    depth_style = 0
    depth_script = 0
    applied: set[str] = set()
    result = []
    all_changes = []

    for part in parts:
        if _TAG_RE.match(part):
            # タグ部分：ネスト深度を更新
            if _OPEN_A_RE.match(part):
                depth_a += 1
            elif _CLOSE_A_RE.match(part):
                depth_a = max(0, depth_a - 1)
            elif _OPEN_STYLE_RE.match(part):
                depth_style += 1
            elif _CLOSE_STYLE_RE.match(part):
                depth_style = max(0, depth_style - 1)
            elif _OPEN_SCRIPT_RE.match(part):
                depth_script += 1
            elif _CLOSE_SCRIPT_RE.match(part):
                depth_script = max(0, depth_script - 1)
            result.append(part)
        else:
            # テキストノード
            if depth_a > 0 or depth_style > 0 or depth_script > 0:
                result.append(part)
            else:
                new_part, changes = apply_citations_to_text(part, entries, applied)
                result.append(new_part)
                all_changes.extend(changes)

    return "".join(result), all_changes


def process_file(html_path: Path, entries: list[dict], dry_run: bool) -> int:
    """
    1ファイルを処理。変更件数を返す。
    """
    original = html_path.read_text(encoding="utf-8")
    new_html, changes = apply_citations_to_html(original, entries)

    if not changes:
        return 0

    article_name = html_path.parent.name
    print(f"\n📄 {article_name}")
    for c in changes:
        print(c)

    if not dry_run and new_html != original:
        html_path.write_text(new_html, encoding="utf-8")

    return len(changes)


def verify_urls(entries: list[dict]) -> None:
    """citation_db.json の全URLを疎通確認する"""
    print("🔍 citation_db.json の全URLを疎通確認中...\n")
    ok = 0
    ng = 0
    for entry in entries:
        url = entry["url"]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                status = res.status
            if status == 200:
                print(f"  ✅ [{entry['id']}] {url}")
                ok += 1
            else:
                print(f"  ⚠ [{entry['id']}] HTTP {status}: {url}")
                ng += 1
        except Exception as e:
            print(f"  ❌ [{entry['id']}] ERROR {e}: {url}")
            ng += 1
    print(f"\n結果: {ok}件OK / {ng}件NG")
    if ng > 0:
        print("❌ NGのURLは citation_db.json を更新してください。")
        sys.exit(1)
    else:
        print("✅ 全URL疎通確認済み")


def main() -> None:
    parser = argparse.ArgumentParser(description="記事に引用リンクを自動付与する")
    parser.add_argument("target", nargs="?", help="特定記事フォルダのパス（省略時は全記事）")
    parser.add_argument("--dry-run", action="store_true", help="変更内容をプレビュー（ファイル更新なし）")
    parser.add_argument("--verify", action="store_true", help="citation_db.json の全URLを疎通確認する")
    args = parser.parse_args()

    entries = load_citation_db()

    if args.verify:
        verify_urls(entries)
        return

    # 対象ディレクトリを決定
    if args.target:
        targets = [Path(args.target)]
    else:
        targets = sorted(ARTICLES_DIR.iterdir())

    if args.dry_run:
        print("🔍 ドライラン（ファイルは更新しません）\n")

    total_files = 0
    total_changes = 0

    for target in targets:
        html = target / "index.html" if target.is_dir() else target
        if not html.exists() or html.suffix != ".html":
            continue
        if html.parent.name == "articles" and html.name == "index.html":
            continue  # 記事一覧ページはスキップ

        n = process_file(html, entries, dry_run=args.dry_run)
        if n > 0:
            total_files += 1
            total_changes += n

    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"[ドライラン] {total_files} 記事 / {total_changes} 箇所にリンク付与予定")
        print("実際に適用するには --dry-run を外して再実行してください。")
    else:
        print(f"✅ 完了: {total_files} 記事 / {total_changes} 箇所にリンク付与しました")


if __name__ == "__main__":
    main()
