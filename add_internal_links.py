#!/usr/bin/env python3
"""
内部リンク自動挿入スクリプト
各記事の末尾（disclaimer divの直前）に「関連記事」セクションを追加する
"""
import json, re
from pathlib import Path

# ---------- クラスター定義 ----------
CLUSTERS = {
    "英会話入門・はじめかた": [
        "eikaiwa-beginner-guide",
        "eikaiwa-self-study",
        "eikaiwa-how-to-start",
        "adult-online-eikaiwa-guide",
        "online-eikaiwa-frequency-guide",
        "online-eikaiwa-not-recommended",
    ],
    "英語学習法（総合）": [
        "english-study-methods-guide",
        "english-vocabulary-guide",
        "eikaiwa-study-methods",
        "english-habit-morning-routine",
        "english-speaking-fear",
        "english-speaking-daily-practice",
        "english-study-adult-worker",
        "eikaiwa-practice-methods",
    ],
    "リスニング・発音・フレーズ": [
        "english-listening-guide",
        "english-pronunciation-guide",
        "english-drama-learning",
        "eikaiwa-example-phrases",
        "travel-english-phrases",
        "english-phrases-collection",
        "eikaiwa-freetalk-topics",
    ],
    "アプリ・ツール・AI": [
        "eikaiwa-app-comparison",
        "eikaiwa-app-free",
        "english-study-apps",
        "english-learning-apps",
        "chatgpt-eikaiwa-guide",
        "chatgpt-eikaiwa-prompts",
        "ai-english-conversation-practice",
        "ai-eikaiwa-comparison",
        "claude-prompt-english-learning",
    ],
    "英検": [
        "eiken-2kyuu-interview",
        "eiken-2kyuu-writing",
        "eiken-2kyuu-vocabulary",
        "eiken-3kyuu-grammar",
        "eiken-4kyuu-guide",
        "eiken-junni-interview",
        "eiken-junni-writing",
    ],
    "TOEIC": [
        "toeic-600-study-plan",
        "toeic-700-guide",
        "toeic-800-guide",
        "toeic-900-study-plan",
        "toeic-eikaiwa-combination",
    ],
    "社会人・ビジネス・キャリア": [
        "business-english-guide",
        "english-study-adult-worker",
        "eikaiwa-for-workers",
        "english-job-interview-prep",
        "salary-up-english",
        "global-remote-work-english",
        "english-resume-prompt",
    ],
    "サービス比較・料金・選び方": [
        "eikaiwa-fee-comparison",
        "english-learning-cost-comparison",
        "online-eikaiwa-not-recommended",
        "online-eikaiwa-philippines",
        "kyuufu-eikaiwa",
        "studysapuri-english-review",
        "eikaiwa-coaching-guide",
    ],
    "教材・独学": [
        "eikaiwa-textbooks",
        "eikaiwa-textbooks-comparison",
        "eikaiwa-self-study",
        "eikaiwa-practice-methods",
        "english-phrases-collection",
        "english-vocabulary-guide",
    ],
    "旅行英語": [
        "travel-english-phrases",
        "travel-english-service-guide",
        "eikaiwa-example-phrases",
        "english-phrases-collection",
    ],
    "学生・子供向け": [
        "eikaiwa-for-students",
        "eikaiwa-for-high-school",
        "eikaiwa-beginner-guide",
    ],
}

RELATED_HTML_STYLE = """
    <style>
      .related-articles{margin:32px 0 24px;padding:24px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;}
      .related-articles h3{font-size:1rem;font-weight:700;color:#1e293b;margin:0 0 14px;padding:0;border:none;}
      .related-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;}
      .related-list li a{color:#0369a1;text-decoration:none;font-size:.9rem;line-height:1.5;}
      .related-list li a:hover{text-decoration:underline;}
      .related-list li::before{content:"→ ";}
    </style>"""


def build_related_map(topics: list) -> dict:
    """slug → [related_slug, ...] のマップを構築（最大4件）"""
    slug_set = {t["slug"] for t in topics}
    slug_to_clusters: dict[str, list[str]] = {}
    for t in topics:
        slug_to_clusters[t["slug"]] = []
    for cluster_name, slugs in CLUSTERS.items():
        for s in slugs:
            if s in slug_to_clusters:
                slug_to_clusters[s].append(cluster_name)

    related_map: dict[str, list[str]] = {}
    for t in topics:
        slug = t["slug"]
        my_clusters = slug_to_clusters.get(slug, [])
        candidates: list[str] = []
        for c in my_clusters:
            for s in CLUSTERS[c]:
                if s != slug and s in slug_set and s not in candidates:
                    candidates.append(s)
        # 最大4件（同クラスター優先）
        related_map[slug] = candidates[:4]
    return related_map


def make_related_html(slug: str, related_slugs: list[str], slug_to_title: dict) -> str:
    items = ""
    for rs in related_slugs:
        title = slug_to_title.get(rs, rs)
        items += f'\n          <li><a href="/articles/{rs}/">{title}</a></li>'
    return f"""
      <div class="related-articles">
        <h3>関連記事</h3>
        <ul class="related-list">{items}
        </ul>
      </div>"""


def insert_related(html: str, related_html: str) -> tuple[str, bool]:
    """disclaimerの直前に挿入。既に存在する場合はスキップ。"""
    if 'class="related-articles"' in html:
        return html, False
    # disclaimer divの直前に挿入
    target = '<div class="disclaimer">'
    if target in html:
        return html.replace(target, related_html + "\n      " + target, 1), True
    # fallback: </main>の直前
    if "</main>" in html:
        return html.replace("</main>", related_html + "\n    </main>", 1), True
    return html, False


def inject_style(html: str) -> str:
    """<style>タグをhead内に追加（重複チェック）"""
    if "related-articles{" in html:
        return html
    return html.replace("</style>", RELATED_HTML_STYLE + "\n    </style>", 1)


def main():
    data = json.loads(Path("data/article_topics.json").read_text())
    topics = data["topics"]
    slug_to_title = {t["slug"]: t["title"] for t in topics}
    related_map = build_related_map(topics)

    articles_dir = Path("articles")
    updated = 0
    skipped = 0

    for t in topics:
        slug = t["slug"]
        html_path = articles_dir / slug / "index.html"
        if not html_path.exists():
            continue
        related_slugs = related_map.get(slug, [])
        if not related_slugs:
            skipped += 1
            continue

        html = html_path.read_text(encoding="utf-8")
        related_html = make_related_html(slug, related_slugs, slug_to_title)
        new_html, inserted = insert_related(html, related_html)
        if inserted:
            new_html = inject_style(new_html)
            html_path.write_text(new_html, encoding="utf-8")
            updated += 1
            print(f"  ✅ {slug}（{len(related_slugs)}件リンク）")
        else:
            skipped += 1

    print(f"\n完了: {updated}記事に関連記事を追加 / {skipped}記事はスキップ")


if __name__ == "__main__":
    main()
