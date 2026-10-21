# Salon Insight Demo

美容室向けダッシュボード「Salon Insight」の、ポートフォリオ用の公開デモです。

> **このデモの表示データはすべて架空です。** サロン名は「Sample Hair Salon」で、実在の店舗・個人・数値は含みません。
> AI（生成AI）の API は呼びません。AI の出力部分は、事前に用意した固定のサンプルを表示します。

## 概要

Salon Report と来店者データ（リボンデータ）の PDF を読み込み、次を表示するアプリを想定したデモです。

- ACR・CVR の最新値と、エリア平均との差
- 13か月の推移グラフ
- 来店者の年代×性別の傾向（新規／リピート）
- 「今月の重点」（診断文）

## 機能

- **ログイン画面**: 認証は行わず、「デモとしてログイン」ボタンで進めます（ID/パスワードは demo / demo を表示するだけです）。
- **セットアップ画面**:
  - 「サンプルPDFで試す」を押すと、診断結果まで一気に表示します。
  - アップロード欄は無効で、ファイルは保存・送信されません。
  - サンプル PDF（架空）をダウンロードできます。
  - ターゲット層とお店のこだわりを入力できます。
  - 「プロンプトを確認する」で、AI に送る想定のプロンプトを表示します。入力内容に応じて変わります。
- **ダッシュボード画面**: KPI、13か月推移、顧客層、固定のサンプル診断文を表示します。

全画面の上部に「これはポートフォリオ用のデモです」の表示と、その画面の説明を 1 行出します。

## 技術

- Python 3.11 以上
- Streamlit、pandas、Altair（画面・グラフ）
- reportlab（サンプル PDF の生成のみ）

## 起動方法

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで http://localhost:8501 を開きます。API キーや外部サービスの設定は不要です。

なお、画面のフォント（Zen Kaku Gothic New）を表示するため、ブラウザが Google Fonts へフォントを取得しに行きます。アプリ側からデータが送信されることはありません。

## データの再生成

デモデータは固定シードで作っており、再生成しても同じ結果になります。

```bash
python demo_data/generate.py          # demo_data/*.json
python demo_data/make_sample_pdfs.py  # demo_data/sample_pdfs/*.pdf
```

## 画面の見方

- **KPI**: ACR・CVR の自店の値と、エリア平均との差（pt）。
- **13か月推移**: 自店とエリア平均の推移。3月・8月・12月が高く、1〜2月・6〜7月が低い季節変動を入れています。
- **顧客層**: 新規・リピート別の、年代×性別の上位 5 件。
- **今月の重点**: 固定のサンプル診断文です。「デモ用のサンプル出力です」と表示します。

## ディレクトリ構成

```
app.py                 画面（Streamlit）
src/models.py          データ構造
src/ai_diagnosis.py    プロンプト組み立て（AI は呼ばない）
src/ribbon_data.py     混雑時間帯の集計
src/demo_content.py    デモデータの読み込みと固定の診断文
demo_data/             架空データ（JSON）とサンプル PDF、生成スクリプト
```
