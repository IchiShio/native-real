"""
週次自動更新スクリプト
毎週月曜9:00にlaunchdから自動実行される
新記事を2件生成してGitHub Pagesを更新する
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.content_gen import ContentGenerator
from src.github_deploy import GitHubDeployer
from src.site_builder import SiteBuilder


def load_config() -> dict:
    load_dotenv()
    config_path = Path("config.json")
    config: dict = {}
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    # シークレットは .env から上書き
    for env_key, field in [
        ("CLAUDE_API_KEY", "claude_api_key"),
        ("GITHUB_TOKEN", "github_token"),
        ("UNSPLASH_ACCESS_KEY", "unsplash_access_key"),
    ]:
        val = os.getenv(env_key)
        if val:
            config[field] = val
    if not config.get("claude_api_key") and not config.get("github_token"):
        print("エラー: .env にAPIキーが設定されていません。.env.example を参考に .env を作成してください。")
        sys.exit(1)
    return config


def load_existing_articles() -> list[dict]:
    cache = Path("generated_content/articles.json")
    if not cache.exists():
        return []
    with open(cache, encoding="utf-8") as f:
        return json.load(f)


def save_articles(articles: list[dict]) -> None:
    Path("generated_content").mkdir(exist_ok=True)
    with open("generated_content/articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def main() -> None:
    print("=== AffiliateForge 週次更新 ===")

    config = load_config()
    existing = load_existing_articles()
    existing_slugs = [a["slug"] for a in existing]

    print(f"既存記事数: {len(existing)}")

    # 新しい記事を2件生成
    print("新しい記事を生成中...")
    provider = config.get("ai_provider", "claude")
    api_key = config.get(f"{provider}_api_key", "")
    generator = ContentGenerator(api_key, provider=provider)
    deployer = GitHubDeployer(config)
    new_articles = generator.generate_new_articles(
        count=2,
        existing_slugs=existing_slugs,
        deployer=deployer,
    )

    if not new_articles:
        print("新しいトピックがありません。スキップします。")
        return

    all_articles = existing + new_articles
    save_articles(all_articles)
    print(f"記事を追加しました ({len(new_articles)}件)")

    # サイト再ビルド
    print("サイトを再構築中...")
    builder = SiteBuilder(config, all_articles)
    site_dir = builder.build()

    # デプロイ
    print("GitHub Pagesを更新中...")
    deployer = GitHubDeployer(config)
    site_url = deployer.deploy(site_dir)

    print(f"\n完了! サイト: {site_url}")
    print(f"総記事数: {len(all_articles)}")


if __name__ == "__main__":
    main()
