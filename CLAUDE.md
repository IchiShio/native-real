# CLAUDE.md - eikaiwa-hikaku

## プロジェクト概要

英会話サービス比較サイト（静的HTML）。GitHub Pages でホスティング。

## 構成

- `index.html` -- トップページ
- `articles/` -- SEO記事（英語学習ガイド、比較記事など）
- `services/` -- 各英会話サービスの個別ページ
- `assets/` -- 画像・CSS等の静的ファイル
- `CNAME` -- カスタムドメイン設定
- `sitemap.xml` / `robots.txt` -- SEO設定

## 作業ルール

- APIキー・シークレット情報は `.env` に記載し `.gitignore` で除外すること
- 記事・ドラフトは `drafts/` フォルダに保存すること（公開準備ができたら `articles/` に移動）
- 作業前に本ファイルと README.md を確認すること
- HTML変更後は `sitemap.xml` の更新要否を確認すること

## コンテンツ記法ルール

### `**太字**` 使用禁止

HTML ファイル内で `**text**` 形式のマークダウン記法を**一切使用しない**。

- 静的 HTML はマークダウンをレンダリングしないため、`**Kimini英会話**` のように `**` が文字列としてそのまま表示される
- テーブルセル・本文問わず禁止
- 強調が必要な場合は `<strong>text</strong>` または `<b>text</b>` タグを使うこと
