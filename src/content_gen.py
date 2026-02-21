"""
コンテンツ生成エンジン
Claude API または Grok API を使って英語学習サービス比較記事を生成する

対応モデル:
  Claude (Anthropic): 日本語品質が高い。推奨。
  Grok (xAI):        OpenAI互換。安価な代替。
"""
import json
import time
from pathlib import Path
from typing import Any

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from src.seo_context import SEOContext


SERVICE_REVIEW_PROMPT = """あなたは英語教育業界に10年以上携わってきた専門ライターです。
以下のサービスについて、実際の利用者目線で誠実かつ詳しい解説記事を書いてください。

サービス名: {name}
カテゴリ: {category}
サービス概要: {description}
料金: {price_display}
主な特徴: {features}
おすすめ対象: {target}
アフィリエイト報酬: {commission}円（成果条件: {condition}）

## 記事要件
- 文字数: 2,500〜3,000字
- 文体: です・ます調、読みやすく親しみやすく
- トーン: 正直で信頼できる情報提供。過度な宣伝表現は使わない
- 実際の公開情報のみ使用。不明な点は「公式サイトで確認」と記載
- カテゴリが「英語コーチング」の場合は、オンライン英会話との違いを明確に説明すること

## 必須の構成（このまま使用してください）

# {name}の評判・口コミは？【特徴・料金・デメリットを徹底解説】

## {name}とは
（200字程度でサービスの概要を分かりやすく説明。英語コーチングの場合はオンライン英会話との違いを含める）

## {name}の料金プラン
（プラン別料金を分かりやすく説明。表形式を使用）

## {name}の特徴・強み
（3〜4つの強みを具体的に説明）

## {name}のデメリット・注意点
（正直に2〜3点。信頼性のために重要。コーチングの場合は高額なリスクも正直に記載）

## こんな人におすすめ・向いていない人
（具体的なペルソナで説明）

## 他サービスとの比較
（競合1〜2社と具体的に比較。料金・効果・サポート面を含める）

## 無料体験・カウンセリングについて
（申し込み方法と、体験時に確認すべきポイントを記載）

## よくある質問（FAQ）
Googleの「よくある質問」に出やすい形式でQ&A 5つ以上

## まとめ・総評
（正直な評価と、どんな人に向いているかをまとめる。無理な勧誘は不要）"""


HOW_TO_PROMPT = """あなたは英語学習に詳しいWebライターです。
以下のテーマで、読者が本当に役立てる実践的な記事を書いてください。

記事タイトル: {title}
対象読者: {target_reader}
メインキーワード: {target_keyword}
扱うべきトピック: {h2_topics}

## 記事要件
- 文字数: 2,000〜2,500字
- 文体: です・ます調、具体的で実践的
- 根拠やデータ・具体例を必ず含める（「〜と言われています」より「〜という調査では」）
- 読者の「あるある」な悩みに共感した上でアドバイスを提供する
- 記事内で自然に英語コーチングまたはオンライン英会話サービスへの言及を含める

## 必須の構成

# {title}

## はじめに
（読者の悩みに深く共感する導入。「あなただけじゃない」という安心感を与える）

（以下、{h2_topics} に基づいたH2見出しで展開。各セクションは400字以上）

## よくある質問（FAQ）
Googleの「People Also Ask（よくある質問）」に出やすい形式で5つ以上
Q: （質問文）
A: （50〜100字の簡潔な回答）

## まとめ
（記事の要点を箇条書きで整理。最後に「次のステップ」として具体的なアクションを促す）"""


class ContentGenerator:
    """
    Claude または Grok でコンテンツを生成する。

    provider="claude"  → Anthropic Claude（推奨。日本語品質が高い）
    provider="grok"    → xAI Grok（OpenAI互換。比較的安価）
    """

    PROVIDERS = {
        "claude": {
            "model": "claude-opus-4-6",
            "label": "Claude (Anthropic)",
        },
        "grok": {
            "model": "grok-3",
            "label": "Grok (xAI)",
            "base_url": "https://api.x.ai/v1",
        },
    }

    def __init__(self, api_key: str, provider: str = "claude") -> None:
        if provider not in self.PROVIDERS:
            raise ValueError(f"provider は 'claude' または 'grok' を指定してください")

        self.provider = provider
        self.model = self.PROVIDERS[provider]["model"]

        if provider == "claude":
            if not HAS_ANTHROPIC:
                raise ImportError("anthropic ライブラリが必要です: pip install anthropic")
            self._client_claude = anthropic.Anthropic(api_key=api_key)
        else:
            if not HAS_OPENAI:
                raise ImportError("openai ライブラリが必要です: pip install openai")
            self._client_openai = OpenAI(
                api_key=api_key,
                base_url=self.PROVIDERS[provider]["base_url"],
            )

        print(f"   AIモデル: {self.PROVIDERS[provider]['label']} ({self.model})")

        # SEO コンテキストを docs/seo/ から自動ロード
        self._seo = SEOContext()
        if self._seo.is_loaded():
            print(f"   SEOコンテキスト: {self._seo.summary()}")

    def _call_api(self, prompt: str, retry: int = 3) -> str:
        """API呼び出し（リトライ付き）"""
        for attempt in range(retry):
            try:
                if self.provider == "claude":
                    message = self._client_claude.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return message.content[0].text
                else:
                    # Grok (OpenAI互換)
                    response = self._client_openai.chat.completions.create(
                        model=self.model,
                        max_tokens=4096,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message.content or ""

            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "rate" in err_str or "429" in err_str
                if is_rate_limit:
                    wait = (attempt + 1) * 30
                    print(f"   レート制限。{wait}秒待機中...")
                    time.sleep(wait)
                elif attempt == retry - 1:
                    raise
                else:
                    print(f"   APIエラー（{attempt + 1}回目）: {e}。リトライ中...")
                    time.sleep(10)
        raise RuntimeError("APIの呼び出しに失敗しました")

    def generate_service_review(self, service: dict[str, Any]) -> dict[str, Any]:
        """サービスレビュー記事を生成"""
        features_str = "、".join(service["features"])
        category = service.get("category", "オンライン英会話")
        commission = service.get("affiliate_commission", 0)
        condition = service.get("affiliate_condition", "申込")

        prompt = SERVICE_REVIEW_PROMPT.format(
            name=service["name"],
            category=category,
            description=service["description"],
            price_display=service["price_display"],
            features=features_str,
            target=service["target"],
            commission=commission,
            condition=condition,
        )
        # SEO キーワードをプロンプトに注入
        prompt += self._seo.get_keyword_injection("service_review")
        content = self._call_api(prompt)

        title = f"{service['name']}の評判・口コミは？【特徴・料金・デメリットを徹底解説】"
        meta_desc = (
            f"{service['name']}の評判・料金・特徴を詳しく解説。"
            f"おすすめな人・向かない人も正直にレビュー。{service['price_display']}〜利用可能。"
        )[:155]

        return {
            "type": "service_review",
            "service_id": service["id"],
            "slug": service["slug"],
            "title": title,
            "meta_description": meta_desc,
            "content": content,
            "service_name": service["name"],
            "service_url": service["official_url"],
            "rating": service["rating"],
            "category": category,
            "affiliate_commission": commission,
        }

    def generate_how_to_article(self, topic: dict[str, Any]) -> dict[str, Any]:
        """ハウツー記事を生成"""
        h2_str = "・".join(topic["h2_topics"])
        prompt = HOW_TO_PROMPT.format(
            title=topic["title"],
            target_reader=topic["target_reader"],
            target_keyword=topic["target_keyword"],
            h2_topics=h2_str,
        )
        # SEO キーワード・Phase 2 戦略をプロンプトに注入
        prompt += self._seo.get_keyword_injection("how_to")
        content = self._call_api(prompt)

        meta_desc = (
            f"{topic['title'][:60]}。"
            f"{topic['target_reader']}向けに分かりやすく解説します。"
        )[:155]

        return {
            "type": "how_to",
            "slug": topic["slug"],
            "title": topic["title"],
            "meta_description": meta_desc,
            "content": content,
            "category": topic["category"],
            "target_keyword": topic["target_keyword"],
        }

    def generate_all(
        self,
        services_path: str = "data/services.json",
        topics_path: str = "data/topics.json",
        output_dir: str = "generated_content",
    ) -> list[dict[str, Any]]:
        """全記事を生成してJSONに保存"""
        output = Path(output_dir)
        output.mkdir(exist_ok=True)

        # キャッシュ確認（再実行時はスキップ）
        cache_file = output / "articles.json"
        if cache_file.exists():
            print("   既存の生成コンテンツを読み込み中...")
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)

        with open(services_path, encoding="utf-8") as f:
            services_data = json.load(f)
        with open(topics_path, encoding="utf-8") as f:
            topics_data = json.load(f)

        articles: list[dict[str, Any]] = []
        services = services_data["services"]
        topics = topics_data["how_to_articles"]

        total = len(services) + len(topics)
        current = 0

        # サービスレビュー記事
        print(f"\n   サービスレビュー記事を生成中 ({len(services)}件)...")
        for service in services:
            current += 1
            print(f"   [{current}/{total}] {service['name']} のレビューを生成中...")
            try:
                article = self.generate_service_review(service)
                articles.append(article)
                # 生成間隔（APIレート制限対策）
                time.sleep(3)
            except Exception as e:
                print(f"   警告: {service['name']} の生成に失敗しました: {e}")

        # ハウツー記事
        print(f"\n   ハウツー記事を生成中 ({len(topics)}件)...")
        for topic in topics:
            current += 1
            print(f"   [{current}/{total}] '{topic['title'][:30]}...' を生成中...")
            try:
                article = self.generate_how_to_article(topic)
                articles.append(article)
                time.sleep(3)
            except Exception as e:
                print(f"   警告: {topic['title'][:30]} の生成に失敗しました: {e}")

        # キャッシュ保存
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        print(f"\n   合計 {len(articles)} 件の記事を生成しました")
        return articles

    def generate_new_articles(
        self,
        count: int = 2,
        existing_slugs: list[str] | None = None,
        output_dir: str = "generated_content",
        deployer: Any = None,
    ) -> list[dict[str, Any]]:
        """週次更新用：新しい記事を生成

        Args:
            count: 今回生成する最大件数
            existing_slugs: ローカルキャッシュから得た生成済みスラッグ
            output_dir: 出力ディレクトリ（未使用、将来用）
            deployer: GitHubDeployer インスタンス。渡すと GitHub 上の
                      デプロイ済みスラッグも照合してスキップ漏れを防ぐ
        """
        with open("data/topics.json", encoding="utf-8") as f:
            topics_data = json.load(f)

        # ローカルキャッシュ由来のスラッグ
        skip = set(existing_slugs or [])

        # GitHub にデプロイ済みのスラッグを取得してマージ
        if deployer is not None:
            try:
                deployed = set(deployer.get_deployed_slugs())
                new_from_github = deployed - skip
                if new_from_github:
                    print(f"   GitHub確認: ローカルキャッシュにない既デプロイ記事 {len(new_from_github)} 件を検出 → スキップ対象に追加")
                else:
                    print(f"   GitHub確認: デプロイ済み {len(deployed)} 件 (ローカルと一致)")
                skip |= deployed
            except Exception as e:
                print(f"   警告: GitHub デプロイ済みスラッグ取得失敗 (ローカルキャッシュのみで判断): {e}")

        new_topics = [
            t for t in topics_data["how_to_articles"]
            if t["slug"] not in skip
        ]

        if not new_topics:
            print("   新しいトピックがありません")
            return []

        # SEO 優先度でソート（seo_priority フィールドがある場合: S > A > B > なし）
        priority_order = {"S": 0, "A": 1, "B": 2}
        new_topics.sort(key=lambda t: priority_order.get(t.get("seo_priority", ""), 9))

        articles = []
        for topic in new_topics[:count]:
            print(f"   '{topic['title'][:30]}...' を生成中...")
            article = self.generate_how_to_article(topic)
            articles.append(article)
            time.sleep(3)

        return articles
