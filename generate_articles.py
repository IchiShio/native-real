#!/usr/bin/env python3
"""
記事生成スクリプト

native-real/articles/{slug}/index.html に直接書き出す。
APIキーは .env の ANTHROPIC_API_KEY から読み込む（ソースコードに書かないこと）。

使い方:
  python3 generate_articles.py            # 1件生成（デフォルト）
  python3 generate_articles.py --count 5  # 5件生成
  python3 generate_articles.py --list     # 未生成トピック一覧を表示
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# ─── APIキー読み込み（.env のみ。ソースコードに書かない） ───────────────
load_dotenv()
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("エラー: ANTHROPIC_API_KEY が .env に設定されていません")
    print("  .env ファイルに以下を追記してください:")
    print("  ANTHROPIC_API_KEY=sk-ant-api03-...")
    sys.exit(1)
# ─────────────────────────────────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent))
from tools.content_gen import generate_article

SITE_NAME = "英語学習サービス比較ナビ"
BASE_URL = "https://native-real.com"
GTM_ID = "GTM-PS9R9844"
TOPICS_PATH = Path("data/article_topics.json")
ARTICLES_DIR = Path("articles")
SITEMAP_PATH = Path("sitemap.xml")

CSS = """:root{--primary:#2563eb;--primary-light:#3b82f6;--primary-dark:#1d4ed8;--primary-pale:#eff6ff;--accent:#10b981;--accent-dark:#059669;--accent-pale:#ecfdf5;--text:#111827;--text-muted:#6b7280;--bg:#ffffff;--bg-gray:#f9fafb;--border:#e5e7eb;--shadow:0 1px 3px rgba(0,0,0,0.06),0 2px 8px rgba(0,0,0,0.04);--shadow-md:0 4px 16px rgba(0,0,0,0.08),0 8px 24px rgba(0,0,0,0.05);--radius:10px;--radius-lg:14px;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:"Inter","Noto Sans JP",-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic UI",sans-serif;letter-spacing:.01em;font-size:16px;line-height:1.9;color:var(--text);background:var(--bg);}
a{color:var(--primary);}a:hover{color:var(--primary-light);}
img{max-width:100%;height:auto;}
.container{max-width:1100px;margin:0 auto;padding:0 20px;}
.site-header{background:#fff;color:var(--text);padding:14px 0;position:sticky;top:0;z-index:100;box-shadow:0 1px 0 var(--border);}
.site-header .container{display:flex;align-items:center;justify-content:space-between;}
.site-header .logo{font-size:1rem;font-weight:700;color:var(--text);text-decoration:none;letter-spacing:.03em;}
.site-header .logo span{color:var(--primary);}
.site-header nav a{color:var(--text-muted);text-decoration:none;margin-left:24px;font-size:.88rem;border-bottom:2px solid transparent;padding-bottom:2px;transition:color .2s,border-color .2s;}
.site-header nav a:hover{color:var(--text);border-color:var(--primary);}
.hamburger{display:none;background:none;border:none;cursor:pointer;padding:4px;width:36px;height:36px;position:relative;z-index:102;}
.hamburger span{display:block;width:22px;height:2px;background:var(--text);margin:5px auto;border-radius:2px;transition:transform .3s,opacity .3s;}
.hamburger.active span:nth-child(1){transform:translateY(7px) rotate(45deg);}
.hamburger.active span:nth-child(2){opacity:0;}
.hamburger.active span:nth-child(3){transform:translateY(-7px) rotate(-45deg);}
.mobile-nav-overlay{display:none;position:fixed;inset:0;background:rgba(17,24,39,.95);z-index:101;flex-direction:column;align-items:center;justify-content:center;gap:24px;}
.mobile-nav-overlay.active{display:flex;}
.mobile-nav-overlay a{color:#fff;text-decoration:none;font-size:1.2rem;font-weight:600;padding:12px 24px;border-radius:var(--radius);transition:background .2s;}
.mobile-nav-overlay a:hover{background:rgba(255,255,255,.1);}
.breadcrumb{padding:12px 0;font-size:.82rem;color:var(--text-muted);}
.breadcrumb a{color:var(--text-muted);text-decoration:none;}
.breadcrumb a:hover{color:var(--primary);}
.breadcrumb span{margin:0 6px;color:var(--border);}
.article-layout{display:grid;grid-template-columns:1fr 300px;gap:40px;padding:40px 0;}
.article-content{min-width:0;}
.article-content h1{font-size:1.55rem;line-height:1.45;margin-bottom:20px;font-weight:800;}
.article-content h2{font-size:1.25rem;font-weight:700;margin:40px 0 16px;padding:13px 18px;background:var(--bg-gray);border-left:4px solid var(--primary);border-radius:0 var(--radius) var(--radius) 0;color:var(--text);}
.article-content h3{font-size:1.08rem;font-weight:700;margin:28px 0 12px;color:var(--primary);padding-left:12px;border-left:3px solid var(--accent);}
.article-content p{margin-bottom:16px;}
.article-content ul,.article-content ol{margin:16px 0 16px 24px;}
.article-content li{margin-bottom:8px;}
.article-content table{width:100%;border-collapse:collapse;margin:24px 0;font-size:.9rem;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);}
.article-content th{background:var(--primary);color:#fff;padding:11px 16px;text-align:left;font-weight:600;}
.article-content td{padding:11px 16px;border-bottom:1px solid var(--border);}
.article-content tr:nth-child(even) td{background:var(--bg-gray);}
.toc{background:var(--bg-gray);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:0 var(--radius-lg) var(--radius-lg) 0;padding:20px 24px;margin:24px 0 32px;}
.toc h4{font-size:.95rem;font-weight:700;margin-bottom:12px;color:var(--accent-dark);}
.toc ol{margin-left:20px;}
.toc li{margin-bottom:6px;font-size:.88rem;}
.toc a{color:var(--text-muted);text-decoration:none;}
.toc a:hover{color:var(--primary);}
.cta-box{background:linear-gradient(135deg,#059669,#10b981);color:#fff;border-radius:var(--radius-lg);padding:28px 32px;text-align:center;margin:36px 0;box-shadow:0 8px 24px rgba(5,150,105,.25);}
.cta-box h3{font-size:1.15rem;margin-bottom:10px;font-weight:700;color:#fff;border-left:none;padding-left:0;}
.cta-box p{opacity:.9;margin-bottom:20px;font-size:.93rem;}
.btn-primary{display:inline-block;background:var(--primary);color:#fff;padding:11px 20px;border-radius:var(--radius);font-weight:700;font-size:.88rem;text-decoration:none;text-align:center;white-space:nowrap;transition:background .2s,transform .15s;box-shadow:0 3px 10px rgba(37,99,235,.3);}
.btn-primary:hover{background:var(--primary-light);color:#fff;transform:translateY(-1px);}
.disclaimer{background:var(--bg-gray);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px;font-size:.78rem;color:var(--text-muted);margin-top:40px;line-height:1.7;}
.sidebar-widget{background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;margin-bottom:20px;box-shadow:var(--shadow);}
.sidebar-widget h4{font-size:.95rem;font-weight:700;margin-bottom:14px;color:var(--text);padding-bottom:10px;border-bottom:2px solid var(--bg-gray);}
.sidebar-service-item a{font-size:.88rem;text-decoration:none;color:var(--text);}
.sidebar-service-item a:hover{color:var(--primary);}
.sidebar-service-list{display:flex;flex-direction:column;gap:10px;}
.quiz-promo{position:relative;overflow:hidden;background:linear-gradient(135deg,#060C1B,#0f1a35);border:1px solid rgba(251,191,36,.25);border-radius:16px;padding:20px 24px;margin:32px 0;box-shadow:0 0 40px rgba(251,191,36,.07),0 4px 24px rgba(0,0,0,.25);}
.quiz-promo-orb{position:absolute;width:220px;height:220px;background:radial-gradient(circle,rgba(251,191,36,.13),transparent 70%);top:-60px;right:-40px;border-radius:50%;pointer-events:none;}
.quiz-promo-inner{position:relative;z-index:1;display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
.quiz-promo-icon{font-size:2rem;flex-shrink:0;line-height:1;}
.quiz-promo-body{flex:1;min-width:140px;}
.quiz-promo-title{color:rgba(255,255,255,.92);font-weight:700;font-size:.98rem;margin-bottom:4px;}
.quiz-promo-sub{color:rgba(255,255,255,.45);font-size:.78rem;}
.quiz-promo-btn{display:inline-block;background:linear-gradient(135deg,#F59E0B,#FBBF24);color:#1a1000 !important;font-weight:700;font-size:.86rem;padding:11px 22px;border-radius:10px;text-decoration:none;white-space:nowrap;box-shadow:0 4px 16px rgba(251,191,36,.28);transition:transform .18s ease,box-shadow .18s ease;flex-shrink:0;}
.quiz-promo-btn:hover{transform:translateY(-2px);box-shadow:0 6px 24px rgba(251,191,36,.42);color:#1a1000 !important;}
.quiz-promo-widget{position:relative;overflow:hidden;background:linear-gradient(135deg,#060C1B,#0f1a35) !important;border:1px solid rgba(251,191,36,.25) !important;}
.quiz-promo-widget .quiz-promo-orb{width:130px;height:130px;top:-30px;right:-20px;}
.quiz-promo-widget-label{font-size:.7rem;color:rgba(251,191,36,.85);font-weight:700;letter-spacing:.8px;text-transform:uppercase;position:relative;z-index:1;}
.quiz-promo-widget-title{color:rgba(255,255,255,.9);font-weight:700;font-size:.95rem;margin-top:8px;line-height:1.45;position:relative;z-index:1;}
.quiz-promo-widget-sub{color:rgba(255,255,255,.4);font-size:.75rem;margin-top:5px;position:relative;z-index:1;}
.quiz-promo-widget .quiz-promo-btn{width:100%;text-align:center;display:block;margin-top:14px;position:relative;z-index:1;}
.site-footer{background:#2c2520;color:rgba(255,255,255,.65);padding:48px 0 24px;margin-top:72px;font-size:.88rem;}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:32px;margin-bottom:32px;}
.site-footer h4{color:rgba(255,255,255,.9);font-size:.95rem;margin-bottom:14px;}
.site-footer ul{list-style:none;}
.site-footer li{margin-bottom:9px;}
.site-footer a{color:rgba(255,255,255,.6);text-decoration:none;transition:color .2s;}
.site-footer a:hover{color:#f0a080;}
.footer-bottom{border-top:1px solid rgba(255,255,255,.1);padding-top:20px;text-align:center;font-size:.78rem;color:rgba(255,255,255,.4);}
@media(max-width:768px){.site-header nav{display:none;}.hamburger{display:block;}.article-layout{grid-template-columns:1fr;}.sidebar{display:none;}.footer-grid{grid-template-columns:1fr;}}"""


# ─── Markdownシンプル変換 ────────────────────────────────────────────────────
def _md_to_html(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    in_ul = in_ol = in_table = False
    table_rows: list[str] = []

    def flush_list() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not table_rows:
            return
        out.append("<table>")
        for i, row in enumerate(table_rows):
            cols = [c.strip() for c in row.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            if i == 1 and all(re.match(r"[-:]+", c) for c in cols if c):
                continue
            out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cols) + "</tr>")
        out.append("</table>")
        table_rows.clear()
        in_table = False

    def inline(s: str) -> str:
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\*(.+?)\*", r"\1", s)
        return s

    for line in lines:
        if line.strip().startswith("|"):
            if not in_table:
                flush_list()
                in_table = True
            table_rows.append(line)
            continue
        if in_table:
            flush_table()

        if line.startswith("### "):
            flush_list()
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_list()
            h2text = inline(line[3:])
            anchor = re.sub(r"[^a-z0-9]", "-", h2text.lower())[:30]
            out.append(f'<h2 id="{anchor}">{h2text}</h2>')
        elif line.startswith("# "):
            # テンプレートにH1が既にあるためスキップ（重複防止）
            flush_list()
        elif line.startswith("- ") or line.startswith("* "):
            if not in_ul:
                flush_list()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif re.match(r"^\d+\. ", line):
            if not in_ol:
                flush_list()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(re.sub(r'^\\d+\\.\\s', '', line))}</li>")
        elif line.strip() == "":
            flush_list()
        else:
            flush_list()
            out.append(f"<p>{inline(line)}</p>")

    flush_list()
    if in_table:
        flush_table()
    return "\n".join(out)


def _extract_h2s(content: str) -> list[str]:
    return re.findall(r"^## (.+)$", content, re.MULTILINE)


# ─── HTMLビルド ───────────────────────────────────────────────────────────────
def build_html(article: dict) -> str:
    title = article["title"]
    meta_desc = article["meta_description"]
    slug = article["slug"]
    category = article["category"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    canonical = f"{BASE_URL}/articles/{slug}/"

    h2s = _extract_h2s(article["content"])
    toc_items = "\n".join(
        f'<li><a href="#{re.sub(r"[^a-z0-9]", "-", h.lower())[:30]}">{h}</a></li>'
        for h in h2s
    )
    toc_html = f'<div class="toc"><h4>目次</h4><ol>{toc_items}</ol></div>' if toc_items else ""
    content_html = _md_to_html(article["content"])

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": meta_desc,
        "datePublished": today,
        "publisher": {"@type": "Organization", "name": SITE_NAME},
    }, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google Tag Manager -->
  <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{GTM_ID}');</script>
  <!-- End Google Tag Manager -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <title>{title} | {SITE_NAME}</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">
{schema}
</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <!-- Google Tag Manager (noscript) -->
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
  <!-- End Google Tag Manager (noscript) -->
<header class="site-header">
  <div class="container">
    <a href="/" class="logo">{SITE_NAME}</a>
    <nav><a href="/">ランキング</a><a href="/articles/">学習コラム</a><a href="/real-phrases/">フレーズ集</a><a href="/listening/">リスニングクイズ</a><a href="/prompts/">AIプロンプト</a></nav>
    <button class="hamburger" aria-label="メニューを開く" onclick="document.querySelector('.hamburger').classList.toggle('active');document.querySelector('.mobile-nav-overlay').classList.toggle('active');document.body.style.overflow=document.querySelector('.mobile-nav-overlay').classList.contains('active')?'hidden':'';">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="mobile-nav-overlay" onclick="if(event.target===this||event.target.tagName==='A'){{this.classList.remove('active');document.querySelector('.hamburger').classList.remove('active');document.body.style.overflow='';}}">
  <a href="/">ランキング</a><a href="/articles/">学習コラム</a><a href="/real-phrases/">フレーズ集</a><a href="/listening/">リスニングクイズ</a><a href="/prompts/">AIプロンプト</a>
</div>
<div class="breadcrumb container">
  <a href="/">ホーム</a><span>›</span><a href="/articles/">学習コラム</a><span>›</span>{title[:30]}{"..." if len(title) > 30 else ""}
</div>
<div class="container">
  <div class="article-layout">
    <main class="article-content">
      <span style="display:inline-block;background:var(--primary-pale);color:var(--primary);font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:6px;margin-bottom:16px;">{category}</span>
      <h1>{title}</h1>
      {toc_html}
      {content_html}
      <div class="quiz-promo">
        <div class="quiz-promo-orb"></div>
        <div class="quiz-promo-inner">
          <div class="quiz-promo-icon">🎧</div>
          <div class="quiz-promo-body">
            <p class="quiz-promo-title">英語リスニング、今日の5問で実力チェック</p>
            <p class="quiz-promo-sub">732問・5段階レベル・完全無料 — 今すぐ聴き取りに挑戦できます</p>
          </div>
          <a href="/listening/" class="quiz-promo-btn">無料で試す →</a>
        </div>
      </div>
      <div class="disclaimer">
        ※本記事はアフィリエイト広告を含みます。料金・サービス内容は変更される場合があります。最新情報は各公式サイトでご確認ください。
      </div>
    </main>
    <aside class="sidebar">
      <div class="sidebar-widget quiz-promo-widget">
        <div class="quiz-promo-orb"></div>
        <p class="quiz-promo-widget-label">🎧 英語力診断</p>
        <p class="quiz-promo-widget-title">リスニングクイズで<br>実力チェック</p>
        <p class="quiz-promo-widget-sub">732問・無料・5段階レベル</p>
        <a href="/listening/" class="quiz-promo-btn">無料で試す →</a>
      </div>
      <div class="sidebar-widget">
        <h4>人気ランキング</h4>
        <div class="sidebar-service-list">
          <div class="sidebar-service-item"><a href="/services/dmm-eikaiwa/">DMM英会話</a></div>
          <div class="sidebar-service-item"><a href="/services/rarejob/">レアジョブ英会話</a></div>
          <div class="sidebar-service-item"><a href="/services/nativecamp/">ネイティブキャンプ</a></div>
        </div>
        <div style="margin-top:14px;">
          <a href="/" class="btn-primary" style="width:100%;display:block;text-align:center;">ランキングを見る</a>
        </div>
      </div>
    </aside>
  </div>
</div>
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>{SITE_NAME}</h4>
        <p>プロが選ぶオンライン英会話・英語アプリ徹底比較</p>
        <p style="margin-top:12px;">※当サイトはアフィリエイトリンクを含みます。</p>
      </div>
      <div>
        <h4>サービス一覧</h4>
        <ul>
          <li><a href="/services/dmm-eikaiwa/">DMM英会話</a></li>
          <li><a href="/services/rarejob/">レアジョブ英会話</a></li>
          <li><a href="/services/nativecamp/">ネイティブキャンプ</a></li>
          <li><a href="/services/cambly/">Cambly</a></li>
          <li><a href="/services/bizmates/">Bizmates</a></li>
          <li><a href="/services/progrit/">プログリット</a></li>
        </ul>
      </div>
      <div>
        <h4>コンテンツ</h4>
        <ul>
          <li><a href="/articles/">学習コラム一覧</a></li>
          <li><a href="/listening/">リスニングクイズ</a></li>
          <li><a href="/prompts/">AIプロンプト</a></li>
          <li><a href="/">ランキングTOP</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom"><p>© {datetime.now().year} {SITE_NAME}. All rights reserved.</p></div>
  </div>
</footer>
</body>
</html>"""


# ─── sitemap.xml 更新 ─────────────────────────────────────────────────────────
def update_sitemap(slug: str) -> None:
    if not SITEMAP_PATH.exists():
        return
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    url = f"{BASE_URL}/articles/{slug}/"

    # 既存チェック
    for u in root.findall(f"{{{ns}}}url"):
        loc = u.find(f"{{{ns}}}loc")
        if loc is not None and loc.text == url:
            return

    # 追加
    url_el = ET.SubElement(root, f"{{{ns}}}url")
    ET.SubElement(url_el, f"{{{ns}}}loc").text = url
    ET.SubElement(url_el, f"{{{ns}}}lastmod").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ET.SubElement(url_el, f"{{{ns}}}priority").text = "0.7"
    ET.indent(tree, space="  ")
    tree.write(str(SITEMAP_PATH), xml_declaration=True, encoding="UTF-8")


# ─── トピック管理 ─────────────────────────────────────────────────────────────
def load_topics() -> list[dict]:
    if not TOPICS_PATH.exists():
        print(f"エラー: {TOPICS_PATH} が見つかりません")
        sys.exit(1)
    with open(TOPICS_PATH, encoding="utf-8") as f:
        return json.load(f)["topics"]


def get_pending_topics(topics: list[dict]) -> list[dict]:
    return [t for t in topics if not (ARTICLES_DIR / t["slug"] / "index.html").exists()]


# ─── 引用リンク付与 ───────────────────────────────────────────────────────────
def _apply_citations(html_path: Path) -> None:
    """生成した記事に add_citations.py で引用リンクを自動付与する"""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "add_citations.py"), str(html_path.parent)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ⚠ add_citations エラー: {result.stderr[:200]}")
    elif result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            print(f"  {line}")


# ─── メイン ──────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="記事を生成してarticles/に書き出す")
    parser.add_argument("--count", type=int, default=1, help="生成件数（デフォルト: 1）")
    parser.add_argument("--list", action="store_true", help="未生成トピック一覧を表示して終了")
    args = parser.parse_args()

    topics = load_topics()
    pending = get_pending_topics(topics)

    if args.list:
        print(f"未生成トピック: {len(pending)} 件")
        for t in pending:
            print(f"  [{t['category']}] {t['title']}")
        return

    if not pending:
        print("すべてのトピックが生成済みです。data/article_topics.json に新しいトピックを追加してください。")
        return

    targets = pending[: args.count]
    print(f"=== 記事生成開始: {len(targets)} 件 ===")

    for i, topic in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] {topic['title'][:40]}...")
        try:
            article = generate_article(API_KEY, topic)

            # HTMLを直接書き出す
            out_dir = ARTICLES_DIR / article["slug"]
            out_dir.mkdir(parents=True, exist_ok=True)
            html = build_html(article)
            (out_dir / "index.html").write_text(html, encoding="utf-8")

            # sitemap更新
            update_sitemap(article["slug"])

            # 引用リンク自動付与
            _apply_citations(out_dir / "index.html")

            print(f"  ✅ articles/{article['slug']}/index.html を生成しました")
        except Exception as e:
            print(f"  ❌ 生成失敗: {e}")

    print(f"\n=== 完了 ===")
    print("次のステップ:")
    print("  1. python3 check_stats.py  # 統計・引用のチェック（引用リンク確認含む）")
    print("  2. git add articles/ sitemap.xml && git commit -m 'add: 記事X件追加' && git push")


if __name__ == "__main__":
    main()
