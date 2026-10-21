"""デモ用の固定データの読み込みと、固定の診断文。AI・外部通信は使わない。"""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    CouponClickEntry,
    CouponClickReport,
    CouponClickSnapshot,
    MonthlyMetric,
    MonthlySeries,
    ReportSummary,
    RibbonAgeGenderBreakdown,
    RibbonAgeGenderSegment,
    RibbonCapacitySlot,
    RibbonCapacitySummary,
    RibbonDataSummary,
    RibbonTopSegments,
)
from .ribbon_data import summarize_weekday_hour_patterns

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_data"
SAMPLE_PDF_DIR = DEMO_DIR / "sample_pdfs"
SAMPLE_PDFS = [
    ("Salon Report（サンプル）", SAMPLE_PDF_DIR / "sample_salon_report.pdf"),
    ("リボンデータ（サンプル）", SAMPLE_PDF_DIR / "sample_ribbon_data.pdf"),
]

SAMPLE_OUTPUT_NOTE = "デモ用のサンプル出力です"


def _read(name: str) -> dict:
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


def _metric(d: dict) -> MonthlyMetric:
    return MonthlyMetric(d["period"], d["salon_value"], d["area_average"])


def _series(d: dict) -> MonthlySeries:
    return MonthlySeries(d["periods"], d["salon_values"], d["area_averages"])


def _snapshot(d: dict) -> CouponClickSnapshot:
    return CouponClickSnapshot(d["period"], d["is_in_progress"], [CouponClickEntry(**e) for e in d["entries"]])


def load_report_summary() -> ReportSummary:
    d = _read("report_summary.json")
    return ReportSummary(
        report_month=d["report_month"],
        updated_at=d["updated_at"],
        cvr=_metric(d["cvr"]),
        acr=_metric(d["acr"]),
        cvr_series=_series(d["cvr_series"]),
        acr_series=_series(d["acr_series"]),
        store_name=d["store_name"],
    )


def load_coupon_report() -> CouponClickReport:
    d = _read("coupon_report.json")
    return CouponClickReport(current=_snapshot(d["current"]), previous=_snapshot(d["previous"]))


def load_ribbon_data() -> RibbonDataSummary:
    d = _read("ribbon_data.json")
    segments = {k: [RibbonAgeGenderSegment(**s) for s in v] for k, v in d["top_segments"].items()}
    return RibbonDataSummary(
        demographics=RibbonAgeGenderBreakdown(**d["demographics"]),
        top_segments=RibbonTopSegments(**segments),
        capacity=RibbonCapacitySummary(
            slots=[RibbonCapacitySlot(**s) for s in d["capacity"]["slots"]],
            status_ratio=d["capacity"]["status_ratio"],
        ),
    )


def sample_diagnosis(summary: ReportSummary, coupon_report: CouponClickReport, ribbon: RibbonDataSummary) -> str:
    """固定の診断文（本番の診断文と同じトーン）。数値はサンプルデータから差し込むだけで、AIは使わない。"""
    cvr, acr = summary.cvr, summary.acr
    busy, slow = summarize_weekday_hour_patterns(ribbon.capacity.slots, top_n=2)
    top_coupon = max(coupon_report.previous.entries, key=lambda e: e.clicks)
    return (
        f"ACRは自店{acr.salon_value:.1f}%でエリア平均（{acr.area_average:.1f}%）を上回っており、"
        "クーポン・メニューページまで進んだ方の予約完了率は良好です。"
        f"一方でCVRは自店{cvr.salon_value:.1f}%とエリア平均（{cvr.area_average:.1f}%）をやや下回っているため、"
        "サロン情報ページからクーポン・メニューページへ進んでもらう導線（掲載写真やキャッチコピー、"
        "クーポンの見せ方）を確認してみてはいかがでしょうか。\n"
        f"直近の完了月で最もクリックが多かったのは「{top_coupon.coupon_name}」（{top_coupon.clicks}件）です。"
        f"{'・'.join(slow)}は空きが出やすい時間帯のため、このクーポンを重点的に訴求できないか"
        f"確認する余地があります。{'・'.join(busy)}は予約が埋まりやすいため、訴求の強化は優先度を下げて"
        "よいかもしれません。\n"
        "いずれも原因を断定するものではなく、数値から見た確認候補です。"
    )
