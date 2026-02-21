"""
GitHub Pages デプロイヤー
生成したサイトをGitHub Pagesに自動デプロイする
"""
import base64
import time
from pathlib import Path
from typing import Any

import requests


class GitHubDeployer:
    def __init__(self, config: dict[str, Any]) -> None:
        self.token = config["github_token"]
        self.username = config["github_username"]
        self.repo_name = config["repo_name"]
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.api_base = "https://api.github.com"

    def _get(self, path: str) -> requests.Response:
        return requests.get(f"{self.api_base}{path}", headers=self.headers, timeout=30)

    def _post(self, path: str, data: dict[str, Any]) -> requests.Response:
        return requests.post(
            f"{self.api_base}{path}", json=data, headers=self.headers, timeout=30
        )

    def _put(self, path: str, data: dict[str, Any]) -> requests.Response:
        return requests.put(
            f"{self.api_base}{path}", json=data, headers=self.headers, timeout=30
        )

    def ensure_repo_exists(self) -> None:
        """リポジトリが存在しない場合は作成"""
        res = self._get(f"/repos/{self.username}/{self.repo_name}")
        if res.status_code == 404:
            print(f"   リポジトリ '{self.repo_name}' を作成中...")
            data = {
                "name": self.repo_name,
                "description": "英語学習サービス比較サイト",
                "private": False,
                "auto_init": True,
            }
            res = self._post("/user/repos", data)
            if res.status_code not in (200, 201):
                raise RuntimeError(f"リポジトリ作成失敗: {res.text}")
            time.sleep(3)  # 作成完了を待つ
        elif res.status_code != 200:
            raise RuntimeError(f"GitHubアクセスエラー: {res.status_code} {res.text}")
        print(f"   リポジトリ確認OK: {self.username}/{self.repo_name}")

    def _get_file_sha(self, file_path: str) -> str | None:
        """既存ファイルのSHAを取得（更新時に必要）"""
        res = self._get(
            f"/repos/{self.username}/{self.repo_name}/contents/{file_path}"
        )
        if res.status_code == 200:
            return res.json().get("sha")
        return None

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        """ファイルをリポジトリにアップロード（作成または更新）"""
        content_bytes = local_path.read_bytes()
        content_b64 = base64.b64encode(content_bytes).decode()

        sha = self._get_file_sha(remote_path)
        data: dict[str, Any] = {
            "message": f"Update {remote_path}",
            "content": content_b64,
        }
        if sha:
            data["sha"] = sha

        res = self._put(
            f"/repos/{self.username}/{self.repo_name}/contents/{remote_path}", data
        )
        if res.status_code not in (200, 201):
            raise RuntimeError(f"ファイルアップロード失敗 ({remote_path}): {res.text}")

    def enable_pages(self) -> str:
        """GitHub Pagesを有効化してURLを返す"""
        # 既に有効かチェック
        res = self._get(f"/repos/{self.username}/{self.repo_name}/pages")
        if res.status_code == 200:
            return res.json().get("html_url", "")

        # 有効化
        data = {"source": {"branch": "main", "path": "/"}}
        res = self._post(
            f"/repos/{self.username}/{self.repo_name}/pages", data
        )
        if res.status_code in (200, 201):
            return res.json().get("html_url", "")

        # 既に有効な場合は409が返ることがある
        if res.status_code == 409:
            res2 = self._get(f"/repos/{self.username}/{self.repo_name}/pages")
            if res2.status_code == 200:
                return res2.json().get("html_url", "")

        # デフォルトURL
        return f"https://{self.username}.github.io/{self.repo_name}"

    def get_deployed_slugs(self, articles_path: str = "articles") -> list[str]:
        """GitHub リポジトリの articles/ フォルダを見てデプロイ済みスラッグを返す"""
        res = self._get(
            f"/repos/{self.username}/{self.repo_name}/contents/{articles_path}"
        )
        if res.status_code == 200:
            return [item["name"] for item in res.json() if item["type"] == "dir"]
        return []

    def deploy(self, site_dir: Path) -> str:
        """サイトディレクトリをGitHub Pagesにデプロイ"""
        self.ensure_repo_exists()

        # ファイル一覧を収集
        all_files = [f for f in site_dir.rglob("*") if f.is_file()]
        total = len(all_files)
        print(f"   {total} ファイルをアップロード中...")

        for i, file_path in enumerate(all_files, 1):
            relative = file_path.relative_to(site_dir)
            remote_path = str(relative).replace("\\", "/")
            if i % 10 == 0 or i == total:
                print(f"   [{i}/{total}] {remote_path}")
            self.upload_file(file_path, remote_path)
            time.sleep(0.3)  # API レート制限対策

        print("   GitHub Pages を有効化中...")
        site_url = self.enable_pages()
        print(f"   デプロイ完了: {site_url}")
        return site_url
