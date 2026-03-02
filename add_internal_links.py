#!/usr/bin/env python3
"""
内部リンク追加スクリプト v2
既存の関連記事セクション（pattern1/pattern2）に内部リンクを追記する
"""
import os
import re

BASE_DIR = '/Users/yusuke/projects/claude/native-real'
ARTICLES_DIR = os.path.join(BASE_DIR, 'articles')

# ---------- リンクマッピング ----------
ARTICLE_LINKS = {
    # TOEIC クラスター
    'toeic-600-study-plan': [
        ('/articles/toeic-short-intensive/', 'TOEIC3ヶ月で+100点！短期集中スコアアップ完全ガイド'),
        ('/articles/toeic-online-eikaiwa-strategy/', 'TOEIC800点超えのためのオンライン英会話活用戦略'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'toeic-900-study-plan': [
        ('/articles/toeic-600-study-plan/', 'TOEIC600点を目指す3ヶ月学習プラン【500点台からの完全ロードマップ】'),
        ('/articles/toeic-short-intensive/', 'TOEIC3ヶ月で+100点！短期集中スコアアップ完全ガイド'),
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'toeic-short-intensive': [
        ('/articles/toeic-600-study-plan/', 'TOEIC600点を目指す3ヶ月学習プラン【500点台からの完全ロードマップ】'),
        ('/articles/toeic-900-study-plan/', 'TOEIC900点を取るための6ヶ月学習プラン【700点台から逆算】'),
        ('/articles/toeic-online-eikaiwa-strategy/', 'TOEIC800点超えのためのオンライン英会話活用戦略'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'toeic-online-eikaiwa-strategy': [
        ('/articles/toeic-600-study-plan/', 'TOEIC600点を目指す3ヶ月学習プラン【500点台からの完全ロードマップ】'),
        ('/articles/toeic-short-intensive/', 'TOEIC3ヶ月で+100点！短期集中スコアアップ完全ガイド'),
        ('/articles/toeic-eikaiwa-combination/', 'TOEICとオンライン英会話を組み合わせる最強学習法'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'toeic-eikaiwa-combination': [
        ('/articles/toeic-online-eikaiwa-strategy/', 'TOEIC800点超えのためのオンライン英会話活用戦略'),
        ('/articles/toeic-600-study-plan/', 'TOEIC600点を目指す3ヶ月学習プラン【500点台からの完全ロードマップ】'),
        ('/articles/toeic-short-intensive/', 'TOEIC3ヶ月で+100点！短期集中スコアアップ完全ガイド'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'toeic-700-guide': [
        ('/articles/toeic-600-study-plan/', 'TOEIC600点を目指す3ヶ月学習プラン【500点台からの完全ロードマップ】'),
        ('/articles/toeic-800-guide/', 'TOEIC800点達成のための学習戦略と問題集選び'),
        ('/articles/toeic-online-eikaiwa-strategy/', 'TOEIC800点超えのためのオンライン英会話活用戦略'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'toeic-800-guide': [
        ('/articles/toeic-700-guide/', 'TOEIC700点の壁を突破する最短ルート完全ガイド'),
        ('/articles/toeic-900-study-plan/', 'TOEIC900点を取るための6ヶ月学習プラン【700点台から逆算】'),
        ('/articles/toeic-online-eikaiwa-strategy/', 'TOEIC800点超えのためのオンライン英会話活用戦略'),
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    # リスニングクラスター
    'english-listening-guide': [
        ('/articles/english-listening-study-guide/', '英語リスニング勉強法【初級〜上級別の完全プログラム】'),
        ('/articles/english-study-methods-guide/', '英語学習法の完全ガイド【目的別・レベル別の最適な方法】'),
        ('/prompts/shadow-script/', '【AIプロンプト】シャドーイング練習'),
    ],
    'english-listening-study-guide': [
        ('/articles/english-listening-guide/', '英語リスニングを上達させる完全ガイド'),
        ('/articles/english-pronunciation-guide/', '英語発音を改善する完全ガイド【ネイティブ発音への最短ルート】'),
        ('/prompts/shadow-script/', '【AIプロンプト】シャドーイング練習'),
        ('/prompts/vocabulary-study/', '【AIプロンプト】英単語学習'),
    ],
    # スピーキングクラスター
    'english-speaking-improvement': [
        ('/articles/english-speaking-daily-practice/', '英語スピーキングの毎日練習メニュー【続けられる5つのルーティン】'),
        ('/articles/english-speaking-fear/', '英語を話すのが怖い人のための克服法【心理的ブロックの外し方】'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
        ('/prompts/small-talk/', '【AIプロンプト】スモールトーク練習'),
    ],
    'english-speaking-daily-practice': [
        ('/articles/english-speaking-improvement/', '英語スピーキングを上達させる7つの方法'),
        ('/articles/english-speaking-fear/', '英語を話すのが怖い人のための克服法【心理的ブロックの外し方】'),
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
    ],
    'english-speaking-fear': [
        ('/articles/english-speaking-improvement/', '英語スピーキングを上達させる7つの方法'),
        ('/articles/english-speaking-daily-practice/', '英語スピーキングの毎日練習メニュー【続けられる5つのルーティン】'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
        ('/prompts/small-talk/', '【AIプロンプト】スモールトーク練習'),
    ],
    # 発音クラスター
    'english-pronunciation-guide': [
        ('/articles/japanese-english-pronunciation-guide/', '日本人が苦手な英語発音TOP10と克服法'),
        ('/articles/english-pronunciation-correction/', '英語発音矯正の方法【独学でできる実践トレーニング】'),
        ('/prompts/pronunciation-check/', '【AIプロンプト】発音チェック'),
        ('/prompts/shadow-script/', '【AIプロンプト】シャドーイング練習'),
    ],
    'japanese-english-pronunciation-guide': [
        ('/articles/english-pronunciation-guide/', '英語発音を改善する完全ガイド【ネイティブ発音への最短ルート】'),
        ('/articles/english-pronunciation-correction/', '英語発音矯正の方法【独学でできる実践トレーニング】'),
        ('/prompts/pronunciation-check/', '【AIプロンプト】発音チェック'),
    ],
    'english-pronunciation-correction': [
        ('/articles/english-pronunciation-guide/', '英語発音を改善する完全ガイド【ネイティブ発音への最短ルート】'),
        ('/articles/japanese-english-pronunciation-guide/', '日本人が苦手な英語発音TOP10と克服法'),
        ('/prompts/pronunciation-check/', '【AIプロンプト】発音チェック'),
        ('/prompts/shadow-script/', '【AIプロンプト】シャドーイング練習'),
    ],
    # 習慣化クラスター
    'english-habit-guide': [
        ('/articles/english-habit-morning-routine/', '朝の英語習慣で人生が変わる【社会人のための5分ルーティン】'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
        ('/prompts/diary-correction/', '【AIプロンプト】英語日記添削'),
    ],
    'english-habit-morning-routine': [
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
        ('/prompts/diary-correction/', '【AIプロンプト】英語日記添削'),
    ],
    'busy-worker-online-eikaiwa-guide': [
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
        ('/articles/english-habit-morning-routine/', '朝の英語習慣で人生が変わる【社会人のための5分ルーティン】'),
        ('/articles/online-eikaiwa-frequency-guide/', 'オンライン英会話の受講頻度はどれくらいが最適？'),
    ],
    # 学習メソッドクラスター
    'english-study-methods-guide': [
        ('/articles/eikaiwa-study-methods/', '英会話の勉強法【初心者から上級者まで】'),
        ('/articles/eikaiwa-practice-methods/', '英会話の練習方法【すぐ使える7つのテクニック】'),
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
    ],
    'eikaiwa-study-methods': [
        ('/articles/english-study-methods-guide/', '英語学習法の完全ガイド【目的別・レベル別の最適な方法】'),
        ('/articles/eikaiwa-practice-methods/', '英会話の練習方法【すぐ使える7つのテクニック】'),
    ],
    'eikaiwa-practice-methods': [
        ('/articles/eikaiwa-study-methods/', '英会話の勉強法【初心者から上級者まで】'),
        ('/articles/english-study-methods-guide/', '英語学習法の完全ガイド【目的別・レベル別の最適な方法】'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
    ],
    # AIクラスター
    'ai-eikaiwa-comparison': [
        ('/articles/ai-english-conversation-practice/', 'AIで英会話練習する方法【無料でスピーキング力UP】'),
        ('/articles/chatgpt-eikaiwa-guide/', 'ChatGPTで英会話練習する完全ガイド【プロンプト集付き】'),
        ('/articles/english-self-study-vs-eikaiwa/', '英語独学 vs 英会話スクール どっちが効果的？'),
    ],
    'ai-english-conversation-practice': [
        ('/articles/ai-eikaiwa-comparison/', 'AI英会話徹底比較【Claude vs ChatGPT vs Gemini】'),
        ('/articles/chatgpt-eikaiwa-guide/', 'ChatGPTで英会話練習する完全ガイド【プロンプト集付き】'),
        ('/articles/claude-prompt-english-learning/', 'Claude英語学習プロンプト10選【AIで英語力を伸ばす方法】'),
    ],
    'chatgpt-eikaiwa-guide': [
        ('/articles/ai-eikaiwa-comparison/', 'AI英会話徹底比較【Claude vs ChatGPT vs Gemini】'),
        ('/articles/chatgpt-eikaiwa-prompts/', 'ChatGPT英会話プロンプト20選【コピペOK】'),
        ('/articles/claude-prompt-english-learning/', 'Claude英語学習プロンプト10選【AIで英語力を伸ばす方法】'),
    ],
    'chatgpt-eikaiwa-prompts': [
        ('/articles/chatgpt-eikaiwa-guide/', 'ChatGPTで英会話練習する完全ガイド【プロンプト集付き】'),
        ('/articles/claude-prompt-english-learning/', 'Claude英語学習プロンプト10選【AIで英語力を伸ばす方法】'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
        ('/prompts/grammar-qa/', '【AIプロンプト】英文法Q&A'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
    ],
    'claude-prompt-english-learning': [
        ('/articles/chatgpt-eikaiwa-guide/', 'ChatGPTで英会話練習する完全ガイド【プロンプト集付き】'),
        ('/articles/ai-eikaiwa-comparison/', 'AI英会話徹底比較【Claude vs ChatGPT vs Gemini】'),
        ('/prompts/', 'AIプロンプト一覧｜目的別に使えるClaude英語プロンプト集'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
        ('/prompts/toeic-prep/', '【AIプロンプト】TOEIC対策'),
        ('/prompts/business-email/', '【AIプロンプト】ビジネスメール作成'),
        ('/prompts/diary-correction/', '【AIプロンプト】英語日記添削'),
    ],
    # コスト・比較クラスター
    'dmm-vs-nativecamp': [
        ('/articles/rarejob-vs-dmm/', 'レアジョブ vs DMM英会話 どっちがいい？徹底比較'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    'rarejob-vs-dmm': [
        ('/articles/dmm-vs-nativecamp/', 'DMM英会話 vs ネイティブキャンプ 徹底比較'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    'online-eikaiwa-cost-comparison': [
        ('/articles/eikaiwa-fee-comparison/', '英会話スクール・オンライン料金比較一覧【2024年最新】'),
        ('/articles/english-learning-cost-comparison/', '英語学習の費用を比較【オンライン英会話・コーチング・アプリ】'),
        ('/articles/free-online-eikaiwa-guide/', '無料・格安オンライン英会話おすすめ比較'),
    ],
    'eikaiwa-fee-comparison': [
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
        ('/articles/english-learning-cost-comparison/', '英語学習の費用を比較【オンライン英会話・コーチング・アプリ】'),
        ('/articles/free-trial-online-eikaiwa/', 'オンライン英会話の無料体験を活用する方法'),
    ],
    'english-learning-cost-comparison': [
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
        ('/articles/eikaiwa-fee-comparison/', '英会話スクール・オンライン料金比較一覧【2024年最新】'),
        ('/articles/english-coaching-cheap/', '月3万円以下の格安英語コーチングおすすめ比較'),
    ],
    'free-online-eikaiwa-guide': [
        ('/articles/free-trial-online-eikaiwa/', 'オンライン英会話の無料体験を活用する方法'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
        ('/articles/eikaiwa-app-free/', '無料英会話アプリのおすすめ比較'),
    ],
    'free-trial-online-eikaiwa': [
        ('/articles/free-online-eikaiwa-guide/', '無料・格安オンライン英会話おすすめ比較'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    # 属性別クラスター
    'adult-online-eikaiwa-guide': [
        ('/articles/40s-online-eikaiwa-guide/', '40代からのオンライン英会話おすすめ比較'),
        ('/articles/eikaiwa-for-workers/', '社会人の英会話スクール選び方【目的別おすすめ】'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
    ],
    '40s-online-eikaiwa-guide': [
        ('/articles/adult-online-eikaiwa-guide/', '社会人向けオンライン英会話おすすめ比較【目的別ランキング】'),
        ('/articles/senior-online-eikaiwa/', '50代・60代シニアのオンライン英会話おすすめ比較'),
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
    ],
    'senior-online-eikaiwa': [
        ('/articles/40s-online-eikaiwa-guide/', '40代からのオンライン英会話おすすめ比較'),
        ('/articles/adult-online-eikaiwa-guide/', '社会人向けオンライン英会話おすすめ比較【目的別ランキング】'),
    ],
    'junior-high-online-eikaiwa': [
        ('/articles/eikaiwa-for-high-school/', '高校生向けオンライン英会話おすすめ比較'),
        ('/articles/eiken-3kyuu-grammar/', '英検3級の文法対策【合格に必要な文法を完全マスター】'),
        ('/articles/eiken-4kyuu-guide/', '英検4級完全ガイド【合格するための勉強法と教材】'),
    ],
    'eikaiwa-for-high-school': [
        ('/articles/junior-high-online-eikaiwa/', '中学生向けオンライン英会話おすすめ比較'),
        ('/articles/eikaiwa-for-students/', '大学生向けオンライン英会話おすすめ比較'),
        ('/articles/eiken-2kyuu-interview/', '英検2級の面接対策【合格率を上げる7つのコツ】'),
    ],
    'eikaiwa-for-students': [
        ('/articles/eikaiwa-for-high-school/', '高校生向けオンライン英会話おすすめ比較'),
        ('/articles/eikaiwa-for-workers/', '社会人の英会話スクール選び方【目的別おすすめ】'),
        ('/articles/english-job-interview-prep/', '外資系・英語面接の完全対策ガイド'),
    ],
    'eikaiwa-for-workers': [
        ('/articles/adult-online-eikaiwa-guide/', '社会人向けオンライン英会話おすすめ比較【目的別ランキング】'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
    ],
    # コーチングクラスター
    'english-coaching-ranking': [
        ('/articles/english-coaching-vs-online-eikaiwa/', '英語コーチング vs オンライン英会話 どっちを選ぶ？'),
        ('/articles/english-coaching-worth-it/', '英語コーチングは本当に効果ある？コスパを徹底検証'),
        ('/articles/english-coaching-cheap/', '月3万円以下の格安英語コーチングおすすめ比較'),
    ],
    'english-coaching-vs-online-eikaiwa': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-worth-it/', '英語コーチングは本当に効果ある？コスパを徹底検証'),
    ],
    'english-coaching-worth-it': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-vs-online-eikaiwa/', '英語コーチング vs オンライン英会話 どっちを選ぶ？'),
        ('/articles/english-coaching-3months/', '英語コーチング3ヶ月でどこまで伸びる？体験談と効果'),
    ],
    'english-coaching-3months': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-worth-it/', '英語コーチングは本当に効果ある？コスパを徹底検証'),
    ],
    'english-coaching-cheap': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-learning-cost-comparison/', '英語学習の費用を比較【オンライン英会話・コーチング・アプリ】'),
    ],
    'english-coaching-individual': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-cheap/', '月3万円以下の格安英語コーチングおすすめ比較'),
    ],
    'eikaiwa-coaching-guide': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-vs-online-eikaiwa/', '英語コーチング vs オンライン英会話 どっちを選ぶ？'),
    ],
    # フレーズクラスター
    'english-phrases-collection': [
        ('/articles/eikaiwa-example-phrases/', '英会話でよく使う表現集【すぐ使えるフレーズ100選】'),
        ('/articles/eikaiwa-freetalk-topics/', '英会話フリートークのテーマ100選【ネタ切れ解消】'),
        ('/real-phrases/', 'ネイティブ英語フレーズ集（リアルフレーズ101選）'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
        ('/prompts/small-talk/', '【AIプロンプト】スモールトーク練習'),
    ],
    'eikaiwa-freetalk-topics': [
        ('/articles/english-phrases-collection/', 'よく使う英語フレーズ150選【シーン別完全集】'),
        ('/articles/eikaiwa-example-phrases/', '英会話でよく使う表現集【すぐ使えるフレーズ100選】'),
        ('/real-phrases/', 'ネイティブ英語フレーズ集（リアルフレーズ101選）'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
        ('/prompts/small-talk/', '【AIプロンプト】スモールトーク練習'),
    ],
    'travel-english-phrases': [
        ('/articles/travel-english-service-guide/', '旅行前に英語を身につけるおすすめサービス比較'),
        ('/articles/english-phrases-collection/', 'よく使う英語フレーズ150選【シーン別完全集】'),
        ('/prompts/travel-roleplay/', '【AIプロンプト】旅行英語ロールプレイ'),
    ],
    'eikaiwa-example-phrases': [
        ('/articles/english-phrases-collection/', 'よく使う英語フレーズ150選【シーン別完全集】'),
        ('/articles/eikaiwa-freetalk-topics/', '英会話フリートークのテーマ100選【ネタ切れ解消】'),
        ('/real-phrases/', 'ネイティブ英語フレーズ集（リアルフレーズ101選）'),
        ('/prompts/speaking-practice/', '【AIプロンプト】スピーキング練習'),
    ],
    # キャリアクラスター
    'english-job-interview-prep': [
        ('/articles/salary-up-english/', '英語力でどれだけ年収が上がる？実データで検証'),
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
        ('/articles/english-career-salary-impact/', '英語習得のキャリアへの影響【年収・昇進データ付き】'),
        ('/prompts/english-interview/', '【AIプロンプト】英語面接練習'),
    ],
    'salary-up-english': [
        ('/articles/english-job-interview-prep/', '外資系・英語面接の完全対策ガイド'),
        ('/articles/english-career-salary-impact/', '英語習得のキャリアへの影響【年収・昇進データ付き】'),
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
    ],
    'english-career-salary-impact': [
        ('/articles/salary-up-english/', '英語力でどれだけ年収が上がる？実データで検証'),
        ('/articles/english-job-interview-prep/', '外資系・英語面接の完全対策ガイド'),
        ('/articles/global-remote-work-english/', 'グローバルリモートワークに必要な英語力とは'),
    ],
    'global-remote-work-english': [
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
        ('/articles/english-career-salary-impact/', '英語習得のキャリアへの影響【年収・昇進データ付き】'),
        ('/prompts/business-email/', '【AIプロンプト】ビジネスメール作成'),
    ],
    'business-english-online-eikaiwa': [
        ('/articles/english-job-interview-prep/', '外資系・英語面接の完全対策ガイド'),
        ('/articles/salary-up-english/', '英語力でどれだけ年収が上がる？実データで検証'),
        ('/articles/bizmates-review-article/', 'Bizmatesの評判・口コミを徹底調査【ビジネス英語特化】'),
        ('/prompts/business-email/', '【AIプロンプト】ビジネスメール作成'),
        ('/prompts/english-interview/', '【AIプロンプト】英語面接練習'),
    ],
    'business-english-guide': [
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
        ('/prompts/business-email/', '【AIプロンプト】ビジネスメール作成'),
        ('/prompts/presentation-script/', '【AIプロンプト】プレゼン英語'),
        ('/prompts/english-interview/', '【AIプロンプト】英語面接練習'),
    ],
    # 英検クラスター
    'eiken-2kyuu-interview': [
        ('/articles/eiken-2kyuu-vocabulary/', '英検2級の重要単語・語彙対策【頻出1200語まとめ】'),
        ('/articles/eiken-2kyuu-writing/', '英検2級のライティング対策【合格点が取れる書き方】'),
        ('/articles/eiken-junni-interview/', '英検準2級の面接対策【合格率を上げる実践トレーニング】'),
        ('/prompts/eiken-writing/', '【AIプロンプト】英検ライティング対策'),
    ],
    'eiken-2kyuu-vocabulary': [
        ('/articles/eiken-2kyuu-interview/', '英検2級の面接対策【合格率を上げる7つのコツ】'),
        ('/articles/eiken-2kyuu-writing/', '英検2級のライティング対策【合格点が取れる書き方】'),
        ('/prompts/vocabulary-study/', '【AIプロンプト】英単語学習'),
    ],
    'eiken-2kyuu-writing': [
        ('/articles/eiken-2kyuu-interview/', '英検2級の面接対策【合格率を上げる7つのコツ】'),
        ('/articles/eiken-2kyuu-vocabulary/', '英検2級の重要単語・語彙対策【頻出1200語まとめ】'),
        ('/prompts/eiken-writing/', '【AIプロンプト】英検ライティング対策'),
        ('/prompts/writing-outline/', '【AIプロンプト】英語ライティング'),
    ],
    'eiken-3kyuu-grammar': [
        ('/articles/eiken-4kyuu-guide/', '英検4級完全ガイド【合格するための勉強法と教材】'),
        ('/articles/eiken-junni-interview/', '英検準2級の面接対策【合格率を上げる実践トレーニング】'),
        ('/prompts/grammar-qa/', '【AIプロンプト】英文法Q&A'),
    ],
    'eiken-4kyuu-guide': [
        ('/articles/eiken-3kyuu-grammar/', '英検3級の文法対策【合格に必要な文法を完全マスター】'),
        ('/prompts/grammar-qa/', '【AIプロンプト】英文法Q&A'),
    ],
    'eiken-junni-interview': [
        ('/articles/eiken-2kyuu-interview/', '英検2級の面接対策【合格率を上げる7つのコツ】'),
        ('/articles/eiken-junni-writing/', '英検準2級のライティング対策【合格点が取れる書き方】'),
        ('/articles/eiken-3kyuu-grammar/', '英検3級の文法対策【合格に必要な文法を完全マスター】'),
        ('/prompts/eiken-writing/', '【AIプロンプト】英検ライティング対策'),
    ],
    'eiken-junni-writing': [
        ('/articles/eiken-junni-interview/', '英検準2級の面接対策【合格率を上げる実践トレーニング】'),
        ('/articles/eiken-2kyuu-writing/', '英検2級のライティング対策【合格点が取れる書き方】'),
        ('/prompts/eiken-writing/', '【AIプロンプト】英検ライティング対策'),
        ('/prompts/writing-outline/', '【AIプロンプト】英語ライティング'),
    ],
    # サービスレビュー
    'rarejob-review': [
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
        ('/articles/rarejob-vs-dmm/', 'レアジョブ vs DMM英会話 どっちがいい？徹底比較'),
    ],
    'nativecamp-review-article': [
        ('/articles/dmm-vs-nativecamp/', 'DMM英会話 vs ネイティブキャンプ 徹底比較'),
        ('/articles/online-eikaiwa-frequency-guide/', 'オンライン英会話の受講頻度はどれくらいが最適？'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    'bizmates-review-article': [
        ('/articles/business-english-online-eikaiwa/', 'ビジネス英語に強いオンライン英会話おすすめ比較'),
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-job-interview-prep/', '外資系・英語面接の完全対策ガイド'),
    ],
    'progrit-review': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-worth-it/', '英語コーチングは本当に効果ある？コスパを徹底検証'),
        ('/articles/english-coaching-3months/', '英語コーチング3ヶ月でどこまで伸びる？体験談と効果'),
    ],
    'toraiz-review': [
        ('/articles/english-coaching-ranking/', '英語コーチングおすすめ7選【目的別に徹底比較】'),
        ('/articles/english-coaching-worth-it/', '英語コーチングは本当に効果ある？コスパを徹底検証'),
        ('/articles/english-coaching-3months/', '英語コーチング3ヶ月でどこまで伸びる？体験談と効果'),
    ],
    'cambly-review-article': [
        ('/articles/online-eikaiwa-philippines/', 'フィリピン人講師のオンライン英会話が人気な理由'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    'italki-review': [
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
        ('/articles/english-self-study-vs-eikaiwa/', '英語独学 vs 英会話スクール どっちが効果的？'),
    ],
    # 頻度・継続クラスター
    'online-eikaiwa-frequency-guide': [
        ('/articles/online-eikaiwa-once-a-week/', '週1回のオンライン英会話で効果はある？'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
        ('/articles/online-eikaiwa-not-continue-reasons/', 'オンライン英会話が続かない7つの理由と解決策'),
    ],
    'online-eikaiwa-once-a-week': [
        ('/articles/online-eikaiwa-frequency-guide/', 'オンライン英会話の受講頻度はどれくらいが最適？'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
    ],
    'online-eikaiwa-not-continue-reasons': [
        ('/articles/online-eikaiwa-frequency-guide/', 'オンライン英会話の受講頻度はどれくらいが最適？'),
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
    ],
    # その他
    'english-resume-prompt': [
        ('/prompts/writing-outline/', '【AIプロンプト】英語ライティング'),
        ('/prompts/english-interview/', '【AIプロンプト】英語面接練習'),
        ('/articles/english-job-interview-prep/', '外資系・英語面接の完全対策ガイド'),
    ],
    'travel-english-service-guide': [
        ('/articles/travel-english-phrases/', '旅行で使える英語フレーズ完全集【空港・ホテル・レストラン】'),
        ('/prompts/travel-roleplay/', '【AIプロンプト】旅行英語ロールプレイ'),
    ],
    'english-self-study-vs-eikaiwa': [
        ('/articles/ai-eikaiwa-comparison/', 'AI英会話徹底比較【Claude vs ChatGPT vs Gemini】'),
        ('/articles/english-learning-cost-comparison/', '英語学習の費用を比較【オンライン英会話・コーチング・アプリ】'),
    ],
    'english-drama-learning': [
        ('/articles/english-listening-guide/', '英語リスニングを上達させる完全ガイド'),
        ('/articles/english-pronunciation-guide/', '英語発音を改善する完全ガイド【ネイティブ発音への最短ルート】'),
        ('/prompts/shadow-script/', '【AIプロンプト】シャドーイング練習'),
    ],
    'english-vocabulary-guide': [
        ('/prompts/vocabulary-study/', '【AIプロンプト】英単語学習'),
        ('/prompts/idiom-study/', '【AIプロンプト】イディオム学習'),
        ('/real-phrases/', 'ネイティブ英語フレーズ集（リアルフレーズ101選）'),
    ],
    'english-learning-apps': [
        ('/articles/eikaiwa-app-comparison/', '英会話アプリ徹底比較TOP10【2024年版】'),
        ('/articles/english-study-apps/', '英語勉強アプリのおすすめ比較【無料・有料・ジャンル別】'),
        ('/articles/eikaiwa-app-free/', '無料英会話アプリのおすすめ比較'),
    ],
    'english-study-apps': [
        ('/articles/english-learning-apps/', 'おすすめ英語学習アプリ10選【目的別・レベル別比較】'),
        ('/articles/eikaiwa-app-comparison/', '英会話アプリ徹底比較TOP10【2024年版】'),
    ],
    'eikaiwa-app-comparison': [
        ('/articles/english-learning-apps/', 'おすすめ英語学習アプリ10選【目的別・レベル別比較】'),
        ('/articles/eikaiwa-app-free/', '無料英会話アプリのおすすめ比較'),
    ],
    'eikaiwa-app-free': [
        ('/articles/eikaiwa-app-comparison/', '英会話アプリ徹底比較TOP10【2024年版】'),
        ('/articles/free-online-eikaiwa-guide/', '無料・格安オンライン英会話おすすめ比較'),
    ],
    'kids-online-eikaiwa-guide': [
        ('/articles/kids-online-eikaiwa-effects/', '子どものオンライン英会話は効果ある？実証データで検証'),
    ],
    'kids-online-eikaiwa-effects': [
        ('/articles/kids-online-eikaiwa-guide/', '子ども向けオンライン英会話おすすめ比較'),
    ],
    'english-study-adult-worker': [
        ('/articles/adult-online-eikaiwa-guide/', '社会人向けオンライン英会話おすすめ比較【目的別ランキング】'),
        ('/articles/busy-worker-online-eikaiwa-guide/', '忙しい社会人がオンライン英会話を続ける方法【15分/日でOK】'),
        ('/articles/english-habit-guide/', '英語学習を習慣化するための完全ガイド'),
    ],
    'kyuufu-eikaiwa': [
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
        ('/articles/english-learning-cost-comparison/', '英語学習の費用を比較【オンライン英会話・コーチング・アプリ】'),
    ],
    'eikaiwa-textbooks': [
        ('/articles/eikaiwa-textbooks-comparison/', '英会話テキスト vs オンライン英会話 どっちで学ぶ？'),
        ('/articles/eikaiwa-self-study/', '英会話を独学で身につける方法【教材・方法・スケジュール】'),
    ],
    'eikaiwa-textbooks-comparison': [
        ('/articles/eikaiwa-textbooks/', '英会話に役立つ参考書・テキストおすすめ比較'),
        ('/articles/eikaiwa-self-study/', '英会話を独学で身につける方法【教材・方法・スケジュール】'),
    ],
    'eikaiwa-self-study': [
        ('/articles/eikaiwa-textbooks/', '英会話に役立つ参考書・テキストおすすめ比較'),
        ('/articles/english-self-study-vs-eikaiwa/', '英語独学 vs 英会話スクール どっちが効果的？'),
        ('/prompts/diary-correction/', '【AIプロンプト】英語日記添削'),
    ],
    'eikaiwa-beginner-guide': [
        ('/articles/eikaiwa-how-to-start/', 'オンライン英会話のはじめ方【初心者でも失敗しない手順】'),
        ('/articles/how-to-choose/', 'オンライン英会話の選び方【失敗しないための7つのポイント】'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    'eikaiwa-how-to-start': [
        ('/articles/eikaiwa-beginner-guide/', '英会話ゼロから始めるための完全ガイド'),
        ('/articles/how-to-choose/', 'オンライン英会話の選び方【失敗しないための7つのポイント】'),
        ('/articles/free-trial-online-eikaiwa/', 'オンライン英会話の無料体験を活用する方法'),
    ],
    'how-to-choose': [
        ('/articles/eikaiwa-how-to-start/', 'オンライン英会話のはじめ方【初心者でも失敗しない手順】'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
    'online-eikaiwa-philippines': [
        ('/articles/cambly-review-article/', 'Camblyの評判・口コミを徹底調査【ネイティブ講師専門】'),
        ('/articles/online-eikaiwa-cost-comparison/', 'オンライン英会話の月額料金を安い順に徹底比較'),
    ],
}


def process_article(slug, links):
    """1記事に内部リンクを追加する。戻り値: 追加件数"""
    file_path = os.path.join(ARTICLES_DIR, slug, 'index.html')
    if not os.path.exists(file_path):
        print(f'  [SKIP] ファイルが存在しない: {slug}')
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # パターン判定
    if 'class="related-articles"' in content:
        pattern = 1
    elif 'class="related-posts"' in content or 'related-posts__list' in content:
        pattern = 2
    else:
        print(f'  [SKIP] 関連記事セクションが見つからない: {slug}')
        return 0

    added = 0
    new_content = content

    for url, title in links:
        # 既存リンクチェック（href属性で検索）
        if f'href="{url}"' in new_content:
            continue

        if pattern == 1:
            new_li = f'<li><a href="{url}">{title}</a></li>'
            # related-articles div 内の </ul> の直前に挿入
            related_match = re.search(
                r'(<div class="related-articles">.*?</div>)',
                new_content,
                re.DOTALL
            )
            if related_match:
                section = related_match.group(1)
                # 最初の </ul> の直前に挿入
                new_section = section.replace('</ul>', f'{new_li}\n</ul>', 1)
                new_content = new_content.replace(section, new_section, 1)
                added += 1
        else:  # pattern == 2
            new_li = f'<li class="related-posts__item"><a href="{url}">{title}</a></li>'
            # related-posts section 内の </ul> の直前に挿入
            related_match = re.search(
                r'(<section class="related-posts">.*?</section>)',
                new_content,
                re.DOTALL
            )
            if related_match:
                section = related_match.group(1)
                new_section = section.replace('</ul>', f'{new_li}\n</ul>', 1)
                new_content = new_content.replace(section, new_section, 1)
                added += 1

    if added > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  [OK] {slug}: {added}件追加')
    else:
        print(f'  [NO-CHANGE] {slug}: 追加なし')

    return added


def main():
    total_added = 0
    processed = 0

    print('=== 内部リンク追加処理 開始 ===\n')

    for slug, links in ARTICLE_LINKS.items():
        added = process_article(slug, links)
        total_added += added
        processed += 1

    print(f'\n=== 処理完了 ===')
    print(f'処理記事数: {processed}')
    print(f'総追加リンク数: {total_added}')


if __name__ == '__main__':
    main()


# ---------- 旧バージョン: クラスター定義（未使用・参考用） ----------
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
