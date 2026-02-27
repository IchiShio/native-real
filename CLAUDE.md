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

## listening/ の問題量産パイプライン（2026-02-27実装）

### ファイル構成

| ファイル | 役割 |
|---|---|
| `listening/questions.js` | DATA配列（JavaScript Object記法・キーにクォートなし） |
| `listening/staging.json` | Claude出力の一時保存（gitignore済み） |
| `listening/batch_state.json` | Batch API投入状態の保存（gitignore済み） |
| `generate_questions.py` | Claude Sonnet 4.6 API → staging.json自動保存 |
| `add_questions.py` | staging.json → MP3生成 → questions.js追記 → git push |
| `check_batch.py` | Batch結果回収 → staging.json保存 → add_questions.py実行 |
| `get_prompt.py` | Claude.ai用プロンプト生成 → pbcopyでクリップボードコピー |

### 実行コマンド

```bash
cd /Users/yusuke/projects/claude/eikaiwa-hikaku

# 通常モード（即時・~69円/100問）
python3 generate_questions.py --count 100

# Batch モード（24時間以内・~35円/100問）
python3 generate_questions.py --count 100 --batch
# 翌日以降:
python3 check_batch.py

# 問題追加（staging.jsonに保存済みの場合）
python3 add_questions.py

# Claude.ai用プロンプト生成（手動フロー）
python3 get_prompt.py --count 100
```

### 設計メモ

- **axisフィールド**: speed / reduction / vocab / context / distractor（5軸難易度微差、問題内で均等分散）
- **BATCH_SIZE=30**: MAX_TOKENS=8192に収まる量。1リクエスト30問×複数リクエストで100問を達成
- **EXCLUDE_LIMIT=3000**: 直近3000問のみ除外リストに渡す（プロンプト最大~75,500トークン）。毎日100問ペースで約30日分
- **音声ローテーション**: AriaNeural / SoniaNeural / GuyNeural / NatashaNeural / RyanNeural の5種
- **`.env`**: `ANTHROPIC_API_KEY` が必要（generate_questions.py用）

### axis フィールドの経緯と状態（2026-02-27）

| 項目 | 内容 |
|---|---|
| 導入コミット | `6f12cd2` "Switch to Sonnet 4.6, add axis field for fine-grained difficulty" |
| 目的 | lv1-lv5 の5段階 × 5軸 = 25通りの細分化による適応型難易度の精度向上 |
| 既存問題への適用状態 | **適用済み**（460問・コミット `32eac3a`）vocab:140 / context:242 / distractor:74 / reduction:4 / speed:0 |
| 新規問題 | generate_questions.py / get_prompt.py のプロンプトに axis 生成指示を追加済み |

#### classify_axis.py（既存問題一括分類）

```bash
cd /Users/yusuke/projects/claude/eikaiwa-hikaku

# dry-run（最初の30問のみ・questions.js 非更新）
python3 classify_axis.py --dry-run

# 本番（全460問分類 → questions.js 更新）
python3 classify_axis.py
```

- **途中保存**: `listening/axis_cache.json`（gitignore 推奨）
- **再実行**: キャッシュ済みの問題はスキップして続きから処理
- **モデル**: デフォルト claude-sonnet-4-6

#### axis の定義

| axis | 内容 |
|---|---|
| `speed` | 発話が速い・詰まった話し方（"Didja hear that?" 等） |
| `reduction` | gonna/wanna/kinda/dunno/lemme 等の音変化・リンキング・脱落 |
| `vocab` | 低頻度語・イディオム・スラング・比喩表現 |
| `context` | 前後文脈・話者トーン・感情から正解を推論する必要がある |
| `distractor` | 誤答が非常に紛らわしく、表面的理解では正解できない |

## listening/ のプラン設計（2026-02-25更新）

### 無料・登録・プレミアムの区分け

| 機能 | 未登録 | メール登録済み | プレミアム |
|---|---|---|---|
| 1日の問題数 | 5問 | 15問 | 予定 |
| 難易度適応 | ✅ | ✅ | ✅ |
| ヒント機能 | ✅ | ✅ | ✅ |
| 苦手問題の自動復習 | ✅（無料の目玉） | ✅ | ✅ |
| 進捗ダッシュボード | ❌ | ❌ | 近日公開 |
| クロスデバイス同期 | ❌ | ❌ | 近日公開 |

### プレミアムプラン（Waitlist 方式）
- **価格**: ¥490/月（予定）
- **現状**: Waitlist 受付中（Google Forms で収集）→ 公開時に通知
- **Waitlist フォーム**: Google Forms（URLは実装時に記録）
- **Waitlist データ**: Google スプレッドシートに自動保存
- **Beehiiv との区分け**: Waitlist は Google Forms、ニュースレターは Beehiiv（Beehiiv 無料プランのため API タグ付け不可）
- **将来の進捗管理**: Firebase（Firestore）を予定（実装時期未定）

### 苦手問題の自動復習（未実装・次期実装予定）
- localStorage で不正解問題IDを蓄積
- 「苦手問題を復習する」ボタンで専用セッション開始
- 無料ユーザーへの差別化ポイントとして前面に出す

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

## アナリティクス・計測設定（2026-02-25設定）

### Google Tag Manager
- **コンテナID**: `GTM-PS9R9844`
- 全33ページの `<head>` および `<body>` 直後に設置済み
- タグ:
  - `GA4 - 設定`（Google タグ / All Pages）
  - `GA4 - クリック計測`（GA4イベント / 全リンククリック）
- トリガー: `全リンククリック`（リンクのみ・全クリック）
- 変数: Click Element / Classes / ID / Target / Text / URL（有効化済み）
- イベントパラメータ: `click_url` / `click_text` / `click_classes`

### Google Analytics 4
- **測定ID**: `G-5B9WEBKYEP`
- プロパティ名: `native-real.com`
- GTM経由で配信（直接コード埋め込みなし）
- GA4でクリックデータを確認: レポート → エンゲージメント → イベント → `click`

### Google Search Console
- 認証: `index.html` の `google-site-verification` メタタグ（ドメイン全体に有効）
- サイトマップ: `https://native-real.com/sitemap.xml` 送信済み（30ページ検出）

### 新規ページを追加する際のチェックリスト
1. `sitemap.xml` に URL を追加（`noindex` ページは除く）
2. GTM スニペットは自動適用されるため追加作業不要（既設置済み）

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

---

## 記事執筆・統計引用ルール（2026-02-27 制定）

### 背景
affiliate-forge の `content_gen.py`（Claude API）が生成するコンテンツは統計・引用が全て未検証。
実在する組織名に架空の数字を付けたり、実在するURLに誤った数値を付けるケースが確認された。
**記事をpublishする前に必ず統計の検証ステップを実施すること。**

### 要注意パターン（捏造されやすい）

| パターン | 対処 |
|---|---|
| 「〇〇社の調査によれば XX%が〜」 | WebSearchで組織名＋内容を検索して一致確認 |
| 「〇〇研究者の研究では〜」（具体的%付き） | 研究者は実在しても内容が架空のことがある |
| 「〇〇誌（年・%・頻度）に掲載された研究」 | ジャーナル名が本物でも中身が捏造されやすい |
| 表の中の%値（アンケート出典が曖昧） | 出典が確認できなければ%列ごと削除 |
| FSI 2,200時間 | 英語話者→日本語の研究。日本人→英語への逆用は不正確 |

### 使用可能な引用パターン

- **企業自社公開データ**（プログリット等）: 「〇〇社公開データより」と明示すればOK
- **政府統計**（国税庁・文科省・IIBC）: 数値は正確に引用すること（IIBCは795点超 = 上位16%、20%ではない）
- **著名研究者の代表理論**（具体的%なし）: Krashen・Ebbinghaus・Patricia Kuhl・Carol Dweck・DeKeyser・Hartshorne et al. (2018) はOK
- **Lally et al. (2009)「習慣形成66日」**: European Journal of Social Psychology掲載、実在・正確
- **国際音声学協会「英語44音素・日本語22音素」**: 正確
- **ベネッセ「保護者の約6割が小学校英語活動に満足していない」**: 実在・正確（古いURLは `benesse.jp/berd/` へ301リダイレクト）
- **国税庁「民間給与実態統計調査」令和4年 平均年収458万円**: 実在・正確

### 検証手順
1. WebSearch で「組織名 + 統計内容」を検索
2. 確認できたら採用。できなければ汎用表現に置換
3. URLがある場合は WebFetch で実ページを確認し数値を照合
4. 確認できない統計は「〜とされています」「〜傾向があります」等の定性表現に置換

### 景表法対応
- CTAボックス内に `<div class="note">本記事はアフィリエイト広告を含みます。</div>` を設置するだけでOK
- 「著者が実際に受講したわけではありません」等の追加免責は不要

### 記事作成・publish フロー（2026-02-27 確定版）

```
[1] 生成（native-real に直接書き出し）
    cd ~/projects/claude/native-real
    python3 generate_articles.py --count 5   # 5件生成
    python3 generate_articles.py --list      # 未生成トピック一覧確認

[2] 統計チェック（必須・publishの前に必ず実行）
    python3 check_stats.py
    → 要確認箇所をリストアップ
    → WebSearch で疑わしいものを検証
    → 確認できないものは定性表現に置換
    → 再実行して残件が許容範囲か確認

[3] publish
    git add articles/ sitemap.xml && git commit -m "add: 記事X件追加" && git push

[4] X投稿（任意）
    x-scheduler の reply_url に記事URL設定 → 「要約を生成」→ 翌朝自動投稿
```

### 記事トピック管理

- トピック定義: `data/article_topics.json`（10件・4カテゴリ）
- Claude API ラッパー: `tools/content_gen.py`（claude-sonnet-4-6 使用）
- APIキー: `.env` の `ANTHROPIC_API_KEY`（ソースコードに書かない）
- 生成先: `articles/{slug}/index.html`（sitemap.xml も自動更新）

**check_stats.py の許容済み残件（スルーしてOK）**
- Zoltán Dörnyei・Patricia Kuhl・Carol Dweck・DeKeyser・Hartshorne et al.（全て実在の著名研究者）
- IIBC スコア分布・文科省「英語教育実施状況調査」（公的機関・実在）
- 「公式サイトによると〜」と明示された自社公開データ
- World English Online URL付き引用（URL実在・数値は「約8割」と訂正済み）
- 「検索練習効果」「分散学習効果」等の一般的な認知心理学概念（%なし）

### 2026-02-27 修正済み記事（参考）
affiliate-forge 生成の情報記事13本＋toraiz-review を検証・修正済み（計14本）。主な修正内容:
- FSI誤用（3記事）・捏造アンケート%値・未検証の組織統計・誤ったURL引用数値を全て置換
- 確認済みの引用（Hartshorne, Kuhl, Dweck, Lally, Krashen, プログリット自社データ等）はそのまま維持
