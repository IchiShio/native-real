# CLAUDE.md - eikaiwa-hikaku

## プロジェクト概要

英会話サービス比較サイト（静的HTML）。GitHub Pages でホスティング。

## ホスティング・デプロイ

- **ドメイン**: `native-real.com`（`www` → `ichishio.github.io`）
- **ホスティング**: GitHub Pages（リポジトリ: `IchiShio/eikaiwa-hikaku`）
- **DNS**: A レコード → 185.199.108.153 等の GitHub Pages IPs
- **デプロイ**: `git push origin main` のみ（CI/CD なし、push 後に自動ビルド）
- **IchiShio/native-real**（Next.js）はアーカイブ済み・未使用（DNS は eikaiwa-hikaku を向いている）

## 構成

- `index.html` -- トップページ（診断ウィジェット・フィルタータブ・クイズ cross-promo 含む）
- `articles/index.html` -- 記事一覧（15記事・カテゴリフィルタータブ付き）
- `articles/` -- SEO記事（英語学習ガイド、比較記事など）
- `services/` -- 各英会話サービスの個別ページ
- `assets/ogp.png` -- OGP画像（1200×630px、Pillowで生成）
- `CNAME` -- カスタムドメイン設定（`native-real.com`）
- `sitemap.xml` / `robots.txt` -- SEO設定
- `listening/` -- 英語リスニングクイズ（455問・464 MP3・適応型難易度アルゴリズム）
- `privacy/index.html` -- プライバシーポリシーページ（特定電子メール法・個人情報保護法準拠、noindex）

## index.html の主な機能（2026-02-25更新）

- **診断ウィジェット**: 目標選択（コスパ/ビジネス/スキマ時間/ネイティブ）→ おすすめ表示 + フィルター自動適用
- **フィルタータブ**: すべて/コスパ重視/ビジネス英語/スキマ時間/ネイティブ講師（`data-tags` 属性でフィルタリング）
- **OGP**: `og:image` = `assets/ogp.png`、`twitter:card` = `summary_large_image`

## articles/index.html の主な機能（2026-02-25更新）

- **ヒーローセクション**: `.hero` クラス適用
- **カテゴリフィルタータブ**: すべて/学習法・継続/コーチング/お得情報/資格・キャリア/その他（`data-cat` 属性でフィルタリング）
- **ナビ**: リスニングクイズリンク追加、現在ページに `.active` クラス

## listening/ の構成

- 455問（beginner: 155 / intermediate: 139 / advanced: 161）
- 464 MP3ファイル（`audio/q001.mp3`〜）、5種音声ローテーション（AriaNeural/SoniaNeural/GuyNeural/NatashaNeural/RyanNeural）
- **適応型難易度アルゴリズム**（2026-02-24実装）:
  - intermediate（中級）からスタート
  - 連続2問正解 → 1段階上へ
  - 1問不正解 → 1段階下へ（即時）、不正解問題は新しいレベルのプールに再挿入
  - 難易度ラベルはユーザーに非表示
- **ヒント機能**（2026-02-24実装）:
  - 1回目の出題: ヒントなし
  - 不正解 → 再出題（2回目）: キーフレーズ（`kp`）をアンバー色パネルで表示
  - 再出題（3回目以降）: キーフレーズ + 解説（`expl`）を表示
  - `hintLevel` プロパティを問題オブジェクトに付与して管理（0=なし / 1=kp / 2=kp+expl）
- **日本語仮訳**（2026-02-25実装）:
  - 各問題に `ja` フィールド追加（Claude Haiku で生成）
  - 回答後のトランスクリプト欄に英文スクリプトの下に表示
- **メールゲート（Email Gate）**（2026-02-25実装）:
  - 定数: `EG_TRIGGER=5`（5問後に表示）、`FREE_DAILY_LIMIT=15`（登録後1日15問）
  - Beehiiv API: `https://api.beehiiv.com/v2/publications/pub_9b2ae59d-7a25-49f8-be58-793c82e4a498/subscriptions`
  - 登録済み判定: `localStorage.getItem('eg_registered')` が `'1'` かどうか
  - スキップ = その日の練習終了（`showMissionComplete()` を呼ぶ）
  - 未登録ユーザーは `freeMode=false`（メールゲートに到達させる）、登録後は `freeMode=true`（15問制限）
  - 同意文: `privacy/index.html` へのリンクを含む（特定電子メール法準拠）
- **フィロソフィーセクション**（2026-02-25実装）:
  - Steve Jobs スタイル、共感型セールスコピー（上から目線禁止）
  - `max-width: 620px`、`text-wrap: balance` で行均等化
  - クラス構成: `.philosophy-hook`（感情フック）→ `.philosophy-desc`（旧学習法の描写、薄色）→ `.philosophy-question`（大きな問いかけ）→ `.philosophy-insight`（洞察）→ `.philosophy-quote`（blockquote、ゴールドボーダー）→ `.philosophy-body` → `.philosophy-conclusion`

## listening/ のCSS設計（2026-02-25更新）

- **ブレークポイント**: base(mobile) / 640px(tablet) / 1024px(desktop 2カラム)
- **高さクエリ**: `@media (max-height: 700px)` — iPhone SE等の短い画面向け圧縮
- **タップ領域**: `opt-btn` / `next-btn` に `min-height: 44px`、`play-btn` に `min-height: 48px`、`reset-btn` に `min-height: 44px`（iOS HIG準拠）
- **デスクトップ**: 1024px以上で `.question-view.show` が `flex-direction: row`（音声カード左・選択肢右の2カラム）
- **loading timeout**: 400ms（ハードコードデータのため短縮、API接続時は実通信時間に合わせて変更）
- **回答後**: `nextBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' })` で自動スクロール

## アフィリエイト提携状況（2026-02-25更新）

### ASP: A8.net（メディアID: a25010338349）

| サービス | 状況 | 掲載ページ |
|---|---|---|
| レアジョブ英会話 | ✅ 提携済み・リンク設置済み | `services/rarejob/` |
| ネイティブキャンプ | ✅ 提携済み・リンク設置済み | `services/nativecamp/` |
| Cambly | ✅ 提携済み・リンク設置済み | `services/cambly/` |
| italki | ✅ 提携済み・リンク設置済み | `services/italki/` |
| 駅前留学NOVA | ✅ 提携済み・リンク設置済み | `services/nova/` |
| eスポーツ英会話 | ✅ 提携済み・リンク設置済み | `services/esports-eikaiwa/` |
| スタディサプリENGLISH | ✅ 提携済み・リンク設置済み | `services/studysapuri-english/` |
| Bizmates（オンライン英会話） | ✅ 提携済み・リンク設置済み | `services/bizmates/`、`index.html` |
| Bizmates Plus（コーチング） | ✅ 提携済み・リンク設置済み | `articles/english-coaching-ranking/`、`articles/english-coaching-vs-online-eikaiwa/` |
| DMM英会話 | ⏳ 審査中 | `services/dmm-eikaiwa/`（リンク未設置） |
| PROGRIT | ⏳ 審査中 | `services/progrit/`（リンク未設置） |
| トライズ | ⏳ 審査中 | `services/toraiz/`（リンク未設置） |
| THE ENGLISH COMPANY | ⏳ 審査中（別ASP） | `services/english-company/`（リンク未設置） |

### リンク設置ルール
- A8.netリンク形式: `https://px.a8.net/svt/ejp?a8mat={コード}`
- トラッキングピクセル: `<img border="0" width="1" height="1" src="https://www1X.a8.net/0.gif?a8mat={コード}" alt="">` をCTAボックス内に1つ設置
- CTAボタンとスティッキーCTAバーの両方を差し替えること
- `rel="nofollow noopener"` を必ず付与すること

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
