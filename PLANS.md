# PLANS.md — Salon Insight 公開用デモ版 実装計画

本番（`../salon-insight`）をコピーして作る、ポートフォリオ用の公開デモ。進捗はタスクごとに `[ ]` → `[x]` で更新する。
原則は `CLAUDE.md` を参照。

## 目的

美容室向けダッシュボード（Streamlit）を、誰でもブラウザで触れる公開デモにする。
実在の店・個人・APIキーは一切含めない。AI APIは呼ばない。

## 調査結果（本番の実態）

- 画面は `setup` と `dashboard` の2状態。独立したログイン画面は無い（`APP_PASSWORD` がある場合のみ共有パスワード欄）。
- 入力は **PDF 2種類**（Salon Report、パスワード付きリボンデータ）。予約・顧客の表データ（CSV等）は無い。
- 解析結果は dataclass（`src/models.py`）: `ReportSummary` / `CouponClickReport` / `RibbonDataSummary`。
- AI呼び出しは `src/ai_diagnosis.py` の2か所: `diagnose()`（今月の重点）、`summarize_concept()`（こだわり要約）。`build_prompt()` はAI不使用。
- 「AIプロンプト生成画面」は独立画面ではなく、セットアップ画面の「プロンプトを確認する」ボタン。
- **本番の git 履歴に匿名化前の `reference_values.json` 等が残っている → `.git` はコピーしない（このフォルダは新規 `git init` 済み）。**

## スコープ

- やる: 上記を満たすデモ版の新規作成（このフォルダ内のみ）。
- やらない: 本番フォルダの変更、GitHubへのpush、実PDF・実データ・APIキーの複製、本番パーサーの再実装。

## タスク

- [x] T1 ダミーデータ生成（`demo_data/generate.py`、固定シード、再生成可）
  - 架空の `ReportSummary`（13か月 ACR/CVR 推移、季節変動）、`CouponClickReport`、`RibbonDataSummary`（年齢・性別の偏り、新規/リピート、曜日×時間帯の残キャパ）
  - 出力は `demo_data/*.json`。氏名等は含まない（含める場合は「顧客001」形式）
- [x] T2 サンプルPDF（reportlab、各ページに「架空のデモ用データ」）。解析結果は固定出力（JSON）を使い、「デモ用のサンプル出力です」と表示
  - `demo_data/make_sample_pdfs.py` → `demo_data/sample_pdfs/sample_salon_report.pdf`（2p）/ `sample_ribbon_data.pdf`（2p）。解析結果の固定出力は T1 の JSON をそのまま使う
  - 「デモ用のサンプル出力です」の画面表示は T4 で実装
- [x] T3 コピーと除去: `app.py` / `src/`（`models.py`, `ai_diagnosis.py` の `build_prompt` 部分）のみ。`sheets_store.py`、gsheets、dotenv、genai、pdf解析依存を削除。店舗名を「Sample Hair Salon」に
  - `src/models.py`（コメント1か所のみ修正）、`src/ai_diagnosis.py`（`build_prompt` と `_format_*` のみ）、`src/ribbon_data.py`（`summarize_weekday_hour_patterns` のみ）、`.streamlit/config.toml`（テーマのみ）
  - `app.py`: 描画ヘルパー・ダッシュボードは本番踏襲。パスワード・Sheets・PDF解析・AI呼び出しは削除。`_render_setup` は T4 までスタブ
- [x] T4 画面（`app.py` ＋ `src/demo_content.py`。AppTest でログイン→セットアップ→プロンプト確認→サンプル実行→ダッシュボードが例外なく動くことを確認。実ブラウザでの目視は T6）
  - 全画面上部に常時バナー「これはポートフォリオ用のデモです。表示データはすべて架空のものです」＋その画面の説明1行
  - ログイン画面（新規作成、本番と同トーン）: `st.info`「この画面はデモ用です。「デモとしてログイン」ボタンを押すとログインできます。」、ID/PWに demo/demo をあらかじめ表示、ボタンでセットアップ画面へ。認証処理・外部接続なし
  - セットアップ: 「サンプルPDFで試す」ボタン（押すと結果まで表示）、アップロード欄は無効化＋「デモではファイルは保存・送信されません」、パスワード欄は削除
  - 「プロンプトを確認する」は `build_prompt()` で実際に動かす（入力に応じて変化）
  - 「診断する」はAI非呼び出し。固定の診断文（本番トーン）＋小さく「デモ用のサンプル出力です」
  - こだわり要約はAIを使わず入力をそのまま使う
- [x] T5 公開準備: `requirements.txt`（streamlit, pandas, altair, reportlab のみ）、`.gitignore`（.env, secrets*, 実データ類）、`README.md`（日本語・概要/機能/技術/画面の見方）
- [x] T6 動作確認: `streamlit run` でログイン→セットアップ→サンプル実行→ダッシュボードがエラーなく表示
  - Python 3.12 の新規venvに `requirements.txt` の固定版でインストールし、実ブラウザで確認。コンソール・サーバーログともエラー0件。Python 3.9 では streamlit 1.64.0 が入らない（3.11+ 前提）
- [x] T7 漏洩チェック（grep）: APIキー形式（`AIza` 等）、実PDFファイル名、本番の店舗名、`.env`/`secrets`、`genai`/`gsheets` 参照、`git log` に実データが無いこと
  - 完了条件のgrep: 0件／APIキー・メール・電話番号パターン: 0件／`.env`・secrets類のファイル: 無し／`git log`: コミット0件／本番の店舗名: 未提供のためパターン検索のみ
  - `app.py` の `@import` で Google Fonts を読み込む（本番踏襲）。ブラウザから外部へフォント取得リクエストが出るが、ユーザー判断で残す。README に注記済み
- [x] T8 最終報告: 作成ファイル一覧／本番との違い／grep結果／push・デプロイ手順（pushは実行しない）

## 完了条件

- `grep -rEi "AIza|GEMINI_API_KEY|genai|gsheets|service_account" .` が、説明文以外でヒットしない
- 本番の店舗名・実PDFファイル名がどこにも無い（店舗名はユーザー提供、未提供ならパターン検索のみで報告）
- `streamlit run app.py` で全画面が例外なく表示される
- AI API・外部通信のコードが存在しない

## 決定事項（仮定）

- 表データの「予約・顧客データ」は、PDF解析結果にあたるデータを架空化することで代替する
- サンプルPDFの解析は固定出力方式を採用（推奨案。パーサーを通す案は未採用）
- サンプルPDFは本番の2入力に対応させ2ファイル構成（Salon Report＋クーポン／リボンデータ）。日本語は reportlab 同梱の CID フォント（HeiseiKakuGo-W5）で外部フォント不要。PDFにパスワードは付けない（デモはパスワード欄を削除するため）

- `ai_diagnosis.py` の `_SYSTEM_INSTRUCTION` 等（AI用の指示文）はAIを呼ばないため持ち込まない。`coupon_clicks.py` / `pdf_parser.py` / 本番の `ribbon_data.py` 本体は丸ごと除外（`src/ribbon_data.py` は混雑集計関数のみ）

- T4: 「サンプルPDFで試す」と「診断する」は同じ動作（サンプルデータで診断結果まで表示）。アップロード欄は無効のため、データは常にサンプル。「プロンプトを確認する」は常に押せる。サンプルPDFはセットアップ画面からダウンロード可能。ログインのID/PWは demo/demo を表示するだけで検証しない。固定診断文の数値・時間帯はサンプルデータから差し込む（AI不使用）。ダッシュボードに「ログイン画面に戻る」ボタンを追加

- T7: Google Fonts の `@import` は削除せず残す（ユーザー判断）。完了条件の「外部通信のコードが存在しない」は、AI API・データ送信がないという意味で読み、フォント取得は例外とする

## 未確定・要確認

- 本番の店舗名（grep用）を提供してもらうか。未提供ならパターン検索のみ
- サンプルPDFを本番パーサーに通す方式に変更するか（現状は固定出力）
