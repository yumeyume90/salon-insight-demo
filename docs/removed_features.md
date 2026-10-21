# 本番から削除・置き換えたものの記録

公開デモ版（本セッション）で、本番（`salon-insight`）から外したもの・置き換えたものの一覧です。
本番のコードや実データはこのリポジトリに含めていません。

## 削除したもの

| 対象 | 本番での役割 | デモでの扱い |
|---|---|---|
| `src/sheets_store.py`、`streamlit_gsheets`（`st.connection("gsheets")`） | Google スプレッドシートへのレポート・こだわり設定の保存／読み込み | 丸ごと削除。保存はせず、こだわり欄は「保存されません」と表示 |
| `src/pdf_parser.py` | Salon Report PDF の解析（ACR・CVR・13か月推移） | 削除。`demo_data/*.json` の固定データで代替 |
| `src/coupon_clicks.py` | Salon Report PDF からクーポンのクリック実績を抽出 | 削除。`demo_data/coupon_report.json` で代替 |
| `src/ribbon_data.py` の PDF 解析部分（`parse_ribbon_pdf` ほか） | リボンデータ PDF（パスワード付き）の解析 | 削除。混雑時間帯の集計関数 `summarize_weekday_hour_patterns` のみ残した |
| `src/ai_diagnosis.py` の AI 呼び出し（`diagnose`、`summarize_concept`、リトライ処理、`_get_secret`） | Google Gemini による診断文・こだわり要約の生成 | 削除。`build_prompt` と `_format_*` のみ残した |
| `src/ai_diagnosis.py` のシステム指示文（`_SYSTEM_INSTRUCTION`、`_CONCEPT_SUMMARY_INSTRUCTION`） | AI に渡す指示文 | AI を呼ばないため持ち込まない |
| 依存 `google-genai`、`python-dotenv`、`st-gsheets-connection`、`pdfplumber`、`pypdfium2`、`pytest` | 上記機能のため | `requirements.txt` から除外 |
| `load_dotenv()` と `.env` | 環境変数の読み込み | 削除 |
| `.streamlit/secrets.toml`（および example） | API キー・スプレッドシート接続情報 | コピーしない。`.gitignore` で除外 |
| `_check_password()`、`APP_PASSWORD` | 共有パスワード認証 | 削除。ログイン画面は認証なしのデモ用 |
| PDF アップロードの処理、ファイルサイズ上限（`MAX_FILE_SIZE_BYTES`）、リボンデータのパスワード欄 | PDF の受け取り | アップロード欄は無効化、パスワード欄は削除。ファイルは保存・送信されない |
| `tests/`、`sample_data/`、`docs/`（本番側）、`PHASES.md` | テスト・実PDF・設計文書 | コピーしない（実データを含むため） |
| 本番の `.git` | 履歴（匿名化前のデータが残っている） | コピーしない。このフォルダは新規 `git init` |

## 置き換えたもの

| 本番 | デモ |
|---|---|
| Gemini による診断文 | `src/demo_content.py` の固定の診断文（数値・時間帯のみ架空データから差し込み）。「デモ用のサンプル出力です」と表示 |
| Gemini によるこだわり要約 | 入力をそのままプロンプトに使用 |
| 実 PDF の解析結果 | `demo_data/` の架空 JSON と、`demo_data/sample_pdfs/` の架空サンプル PDF |
| 店舗名 | 「Sample Hair Salon」 |

## 追加したもの

- ログイン画面（認証なし、demo / demo を表示）
- 全画面上部の「これはポートフォリオ用のデモです」バナーと、画面ごとの説明 1 行
- 「サンプルPDFで試す」ボタン、サンプル PDF のダウンロード、ダッシュボードの「ログイン画面に戻る」ボタン

## 残した外部通信

- `app.py` の CSS が Google Fonts（Zen Kaku Gothic New）を `@import` する。本番踏襲で、ユーザー判断により残した。
