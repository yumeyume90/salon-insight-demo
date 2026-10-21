"""デモ用のサンプルPDFを生成する（reportlab）。

`demo_data/*.json`（generate.py の出力）を表に起こして PDF にする。
すべてのページ上部に「架空のデモ用データ」と明記する。実PDFは使わない。

    python demo_data/generate.py
    python demo_data/make_sample_pdfs.py

出力: demo_data/sample_pdfs/sample_salon_report.pdf, sample_ribbon_data.pdf
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = DATA_DIR / "sample_pdfs"
FONT = "HeiseiKakuGo-W5"  # reportlab 同梱の日本語CIDフォント（外部フォント不要）
NOTICE = "架空のデモ用データ（Sample Hair Salon）"

pdfmetrics.registerFont(UnicodeCIDFont(FONT))

TITLE = ParagraphStyle("title", fontName=FONT, fontSize=16, leading=22, spaceAfter=6)
BODY = ParagraphStyle("body", fontName=FONT, fontSize=10, leading=15)
HEAD = ParagraphStyle("head", fontName=FONT, fontSize=12, leading=18, spaceBefore=8, spaceAfter=4)


def load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def draw_notice(canvas, doc) -> None:
    """全ページ共通のヘッダー・フッター。"""
    canvas.saveState()
    canvas.setFont(FONT, 9)
    canvas.setFillColor(colors.HexColor("#b42318"))
    canvas.drawString(20 * mm, A4[1] - 12 * mm, f"【{NOTICE}】")
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"{NOTICE} - {canvas.getPageNumber()}")
    canvas.restoreState()


def table(rows: list[list], col_widths: list[float] | None = None) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), FONT, 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f6")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c4ccd6")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def build_doc(path: Path, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        str(path), pagesize=A4, title=title, author="Salon Insight Demo",
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=22 * mm, bottomMargin=18 * mm,
    )


def make_salon_report(path: Path) -> None:
    report, coupon = load("report_summary.json"), load("coupon_report.json")
    story = [
        Paragraph("サロンレポート（サンプル）", TITLE),
        Paragraph(f"{report['store_name']} / 対象月 {report['report_month']} / 更新日 {report['updated_at']}", BODY),
        Paragraph("主要指標", HEAD),
        table(
            [
                ["指標", "自店", "エリア平均"],
                ["CVR（%）", report["cvr"]["salon_value"], report["cvr"]["area_average"]],
                ["ACR（%）", report["acr"]["salon_value"], report["acr"]["area_average"]],
            ],
            [60 * mm, 40 * mm, 40 * mm],
        ),
        Paragraph("直近13か月の推移", HEAD),
    ]
    rows = [["月", "CVR 自店", "CVR エリア", "ACR 自店", "ACR エリア"]]
    cvr, acr = report["cvr_series"], report["acr_series"]
    for i, period in enumerate(cvr["periods"]):
        rows.append([period, cvr["salon_values"][i], cvr["area_averages"][i], acr["salon_values"][i], acr["area_averages"][i]])
    story.append(table(rows, [30 * mm] + [30 * mm] * 4))

    story.append(PageBreak())
    story.append(Paragraph("クーポン別クリック数（サンプル）", TITLE))
    for key, heading in (("current", "今月（月の途中）"), ("previous", "前月")):
        snap = coupon[key]
        story.append(Paragraph(f"{heading}：{snap['period']}", HEAD))
        rows = [["区分", "ラベル", "クーポン名", "クリック"]]
        rows += [[e["category"], e["label"], e["coupon_name"], e["clicks"]] for e in snap["entries"]]
        story.append(table(rows, [18 * mm, 42 * mm, 90 * mm, 18 * mm]))
    build_doc(path, "Sample Salon Report").build(story, onFirstPage=draw_notice, onLaterPages=draw_notice)


def make_ribbon_data(path: Path) -> None:
    ribbon = load("ribbon_data.json")
    demo, segs, cap = ribbon["demographics"], ribbon["top_segments"], ribbon["capacity"]
    story = [
        Paragraph("来店者データ・残キャパ（サンプル）", TITLE),
        Paragraph("性別・年齢構成", HEAD),
        table(
            [["項目", "割合（%）"], ["女性", demo["female_pct"]], ["男性", demo["male_pct"]], ["不明", demo["unknown_gender_pct"]]]
            + [[f"年齢 {k}", v] for k, v in demo["age_pct"].items()],
            [60 * mm, 40 * mm],
        ),
    ]
    for key, heading in (("new_customer", "新規客 上位セグメント"), ("repeat_customer", "リピート客 上位セグメント")):
        story.append(Paragraph(heading, HEAD))
        rows = [["年代", "性別", "割合（%）"]] + [[s["age_band"], s["gender"], s["percentage"]] for s in segs[key]]
        story.append(table(rows, [40 * mm, 30 * mm, 30 * mm]))

    story.append(PageBreak())
    story.append(Paragraph("残キャパ比率（来月・営業時間内）", TITLE))
    story.append(table([["状態", "比率（%）"]] + [[k, v] for k, v in cap["status_ratio"].items()], [60 * mm, 40 * mm]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("曜日別の残キャパ20%未満コマ数", HEAD))
    counts: dict[str, int] = {}
    for s in cap["slots"]:
        if s["status"] == "残キャパ20%未満":
            counts[s["weekday"]] = counts.get(s["weekday"], 0) + 1
    order = ["月", "火", "水", "木", "金", "土", "日"]
    story.append(table([["曜日", "コマ数"]] + [[w, counts.get(w, 0)] for w in order], [60 * mm, 40 * mm]))
    build_doc(path, "Sample Ribbon Data").build(story, onFirstPage=draw_notice, onLaterPages=draw_notice)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    make_salon_report(OUT_DIR / "sample_salon_report.pdf")
    make_ribbon_data(OUT_DIR / "sample_ribbon_data.pdf")
    print("wrote sample PDFs to", OUT_DIR)


if __name__ == "__main__":
    main()
