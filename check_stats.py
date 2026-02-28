#!/usr/bin/env python3
"""
publish前統計チェッカー

eikaiwa-hikaku の articles/ 以下のHTMLを走査し、
確認が必要な統計・引用表現をリストアップする。
また、citation_db.json に登録済みのソースが引用リンクなしで
使われている箇所も検出する（add_citations.py を実行すれば解消）。

使い方:
  # 全記事を検査
  python3 check_stats.py

  # 特定の記事フォルダを指定
  python3 check_stats.py articles/english-career-salary-impact
"""

import json
import re
import sys
from pathlib import Path

# native-real リポジトリのルート（このスクリプト自身の場所）
SITE_DIR = Path(__file__).parent
CITATION_DB_PATH = SITE_DIR / "data" / "citation_db.json"

# 要確認パターン（正規表現）
PATTERNS = [
    # 外部調査の数値引用
    (r"([\w・]+(?:調査|研究所|機関|協会|総研)).*?(\d+[%％])", "外部統計引用"),
    (r"によると.*?(\d+[%％])",                                  "「によると+%」"),
    (r"によれば.*?(\d+[%％])",                                  "「によれば+%」"),
    (r"に掲載された研究",                                        "ジャーナル引用"),
    (r"の研究(?:では|によると|によれば)",                         "研究者引用"),
    # FSI の誤用
    (r"FSI|Foreign Service Institute",                          "FSI引用（要確認）"),
    # 捏造されやすい組織
    (r"MMD研究所|エン・ジャパン|船井総研",                        "要注意組織名"),
    # 根拠なき具体数値
    (r"(?:約|平均)\d+[%％](?:向上|改善|増加|減少)",              "効果の具体%"),
    (r"\d+倍(?:と|に|が)(?:報告|示|確認)",                       "〇倍の引用"),
]

# 許容するパターン（これは無視）
ALLOWLIST_PATTERNS = [
    r"アフィリエイト",
    r"width|height|border|padding|margin|font|color|px|em|rem",
    r"display|position|flex|grid|background|opacity|z-index",
    r"border-radius|line-height|pointer|overflow",
]


def is_allowlisted(line: str) -> bool:
    return any(re.search(p, line) for p in ALLOWLIST_PATTERNS)


def check_file(html_path: Path) -> list[tuple[int, str, str]]:
    """1ファイルを検査して (行番号, マッチ理由, 行テキスト) のリストを返す"""
    hits = []
    text = html_path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        if is_allowlisted(line):
            continue
        for pattern, label in PATTERNS:
            if re.search(pattern, line):
                snippet = line.strip()[:120]
                hits.append((lineno, label, snippet))
                break  # 1行につき1件のみ報告
    return hits


def load_citation_keywords() -> list[tuple[str, str, str]]:
    """citation_db.json から (entry_id, label, pattern) のリストを返す"""
    try:
        with open(CITATION_DB_PATH, encoding="utf-8") as f:
            db = json.load(f)
    except FileNotFoundError:
        return []
    result = []
    for key, val in db.items():
        if key.startswith("_"):
            continue
        for kw in val.get("keywords", []):
            result.append((key, val["label"], kw))
    return result


def check_citation_links(
    html_path: Path, citation_entries: list[tuple[str, str, str]]
) -> list[tuple[str, str]]:
    """citation_db に登録済みのソースが <a> リンクなしで使われている箇所を検出する"""
    text = html_path.read_text(encoding="utf-8")
    flagged: set[str] = set()
    hits = []
    for entry_id, label, kw_pattern in citation_entries:
        if entry_id in flagged:
            continue
        try:
            m = re.search(kw_pattern, text)
            if not m:
                continue
            # マッチ位置が既に <a> タグ内かチェック（簡易判定）
            before = text[: m.start()]
            last_open_a = before.rfind("<a ")
            last_close_a = before.rfind("</a>")
            if last_open_a > last_close_a:
                continue  # 既にリンク済み
            flagged.add(entry_id)
            hits.append((label, m.group(0)[:60]))
        except re.error:
            pass
    return hits


def main():
    # 検査対象ディレクトリを決定
    if len(sys.argv) > 1:
        targets = [Path(sys.argv[1])]
    else:
        articles_dir = SITE_DIR / "articles"
        if not articles_dir.exists():
            print(f"Error: {articles_dir} が見つかりません")
            sys.exit(1)
        targets = sorted(articles_dir.iterdir())

    # HTMLファイルリストを作成（再利用するため）
    html_files: list[tuple[str, Path]] = []
    for target in targets:
        html = target / "index.html" if target.is_dir() else target
        if html.exists() and html.suffix == ".html":
            name = target.name if target.is_dir() else target.stem
            html_files.append((name, html))

    # ── 統計チェック ──────────────────────────────────────────────────────────
    total_hits = 0
    flagged_articles = []

    for name, html in html_files:
        hits = check_file(html)
        if hits:
            flagged_articles.append((name, hits))
            total_hits += len(hits)

    if not flagged_articles:
        print("✅ 要確認の統計・引用は見つかりませんでした。")
    else:
        print(f"⚠️  {len(flagged_articles)} 記事で {total_hits} 件の要確認箇所が見つかりました\n")
        print("=" * 70)

        for article_name, hits in flagged_articles:
            print(f"\n📄 {article_name}")
            for lineno, label, snippet in hits:
                print(f"  L{lineno:4d} [{label}]")
                print(f"         {snippet}")

        print("\n" + "=" * 70)
        print("\n確認方法:")
        print("  1. 上記箇所を WebSearch で検索して数値の正確性を確認")
        print("  2. 確認できなければ「〜とされています」等の定性表現に置換")
        print("  3. 修正後に再度このスクリプトを実行して件数が減ったか確認")
        print("\n許容される引用（そのまま使用可）:")
        print("  - サービス自社公開データ（「〇〇社公開データより」と明示）")
        print("  - 政府統計（国税庁・文科省・IIBC等）")
        print("  - 著名理論（Krashen・Ebbinghaus・Kuhl・Dweck等）——%なし")

    # ── 引用リンクチェック ────────────────────────────────────────────────────
    citation_entries = load_citation_keywords()
    if not citation_entries:
        return

    print("\n" + "=" * 70)
    print("🔗 引用リンクチェック（add_citations.py で自動付与可）")
    print("=" * 70)

    link_total = 0
    link_flagged: list[tuple[str, list[tuple[str, str]]]] = []

    for name, html in html_files:
        hits2 = check_citation_links(html, citation_entries)
        if hits2:
            link_flagged.append((name, hits2))
            link_total += len(hits2)

    if not link_flagged:
        print("✅ 全引用ソースにリンクが付与済みです。")
    else:
        print(f"\n⚠️  {len(link_flagged)} 記事で {link_total} 件の引用リンク未付与\n")
        for article_name, hits2 in link_flagged:
            print(f"  📄 {article_name}")
            for label, snippet in hits2:
                print(f"     [{label}] 「{snippet}」")
        print(f"\n  → python3 add_citations.py を実行してください")


if __name__ == "__main__":
    main()
