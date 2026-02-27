"""
記事コンテンツ生成モジュール
Claude API を使って記事本文（Markdown）を生成する。

APIキーは呼び出し元（generate_articles.py）が .env から読み込んで渡す。
このファイルにAPIキーを書かないこと。
"""
from __future__ import annotations

from typing import Any

import anthropic

MODEL = "claude-sonnet-4-6"

ARTICLE_PROMPT = """\
あなたは英語学習・転職・AI活用の専門ライターです。
以下の条件で日本語のSEO記事を執筆してください。

タイトル: {title}
メインキーワード: {target_keyword}
想定読者: {target_reader}
カテゴリ: {category}
構成（H2見出し）: {h2_topics}

【執筆ルール】
- 各H2セクションは400字以上
- 統計・数値は確認済みのものだけ使用。不確かな場合は「〜とされています」等の定性表現にする
- **太字**（マークダウン記法）は使わない。強調は文脈で表現する
- 景表法対応：CTAには「本記事はアフィリエイト広告を含みます」を添える
- アフィリエイトリンクは不要（URLは書かない）
- 文体：丁寧語（です・ます調）、読者に寄り添うトーン
- 出力はMarkdown形式（H2: ##、H3: ###）

まず100字程度のリード文を書き、その後H2見出しで展開してください。
"""

META_PROMPT = """\
以下の記事タイトルと内容に基づき、SEOメタディスクリプションを1文（120〜140字）で生成してください。
タイトル: {title}
カテゴリ: {category}
想定読者: {target_reader}
H2構成: {h2_topics}

メタディスクリプションのみ出力してください（説明文不要）。
"""


def generate_article(api_key: str, topic: dict[str, Any]) -> dict[str, Any]:
    """
    1記事分のコンテンツを生成して返す。

    引数:
        api_key: Anthropic APIキー（.envから取得済みのもの）
        topic: data/article_topics.json の1エントリ

    返り値:
        {slug, title, meta_description, content, category}
    """
    client = anthropic.Anthropic(api_key=api_key)
    h2_str = "・".join(topic["h2_topics"])

    # 本文生成
    content_msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": ARTICLE_PROMPT.format(
                title=topic["title"],
                target_keyword=topic["target_keyword"],
                target_reader=topic["target_reader"],
                category=topic["category"],
                h2_topics=h2_str,
            ),
        }],
    )
    content = content_msg.content[0].text.strip()

    # メタディスクリプション生成
    meta_msg = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": META_PROMPT.format(
                title=topic["title"],
                category=topic["category"],
                target_reader=topic["target_reader"],
                h2_topics=h2_str,
            ),
        }],
    )
    meta_desc = meta_msg.content[0].text.strip()

    return {
        "slug": topic["slug"],
        "title": topic["title"],
        "meta_description": meta_desc,
        "content": content,
        "category": topic["category"],
    }
