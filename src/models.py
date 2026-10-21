from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MonthlyMetric:
    period: str
    salon_value: float
    area_average: float | None


@dataclass
class MonthlySeries:
    periods: list[str]
    salon_values: list[float]
    area_averages: list[float]


@dataclass
class ReportSummary:
    report_month: str
    updated_at: str
    cvr: MonthlyMetric
    acr: MonthlyMetric
    cvr_series: MonthlySeries
    acr_series: MonthlySeries
    store_name: str | None = None  # 画面表示専用。


@dataclass
class CouponClickEntry:
    category: str  # "特集" | "こだわり" | "ブログ"
    label: str  # 特集名・こだわり文言・ブログタイトル
    coupon_name: str
    clicks: int


@dataclass
class CouponClickSnapshot:
    period: str
    is_in_progress: bool
    entries: list[CouponClickEntry]


@dataclass
class CouponClickReport:
    current: CouponClickSnapshot
    previous: CouponClickSnapshot | None


@dataclass
class RibbonAgeGenderBreakdown:
    """リボンデータ1ページ目由来: 直近月の年齢・性別の分布（%、全区分を網羅）。"""

    female_pct: float
    male_pct: float
    unknown_gender_pct: float
    age_pct: dict[str, float]  # 例: {"20代未満": 20.0, "20代": 59.0, ...}


@dataclass
class RibbonAgeGenderSegment:
    """リボンデータ16ページ目由来: 年代×性別の1セグメント分（上位5件のうちの1件）。"""

    age_band: str
    gender: str
    percentage: float


@dataclass
class RibbonTopSegments:
    """リボンデータ16ページ目由来: 新規予約・リピート予約それぞれの上位5セグメント（自サロンのみ）。

    比較サロン平均の値はこの時点では保持しない（自サロンの診断に直接使う情報のみ扱う）。
    """

    new_customer: list[RibbonAgeGenderSegment]
    repeat_customer: list[RibbonAgeGenderSegment]


@dataclass
class RibbonCapacitySlot:
    """リボンデータ15ページ目由来: 日付・時間帯1コマ分の残キャパ状況。"""

    date: str  # 例: "2026-08-01"
    weekday: str  # 例: "土"
    time_label: str  # 例: "09:00"（30分単位の開始時刻）
    status: str  # "残キャパ50%以上" | "残キャパ50%-20%" | "残キャパ20%未満" | "営業時間外" | "対象外"


@dataclass
class RibbonCapacitySummary:
    """リボンデータ15ページ目由来: 残キャパ状況の集計結果。"""

    slots: list[RibbonCapacitySlot]
    status_ratio: dict[str, float]  # 営業時間内のコマ数に対する各ステータスの割合（%）


@dataclass
class RibbonDataSummary:
    """リボンデータPDFから抽出した情報一式。"""

    demographics: RibbonAgeGenderBreakdown
    top_segments: RibbonTopSegments
    capacity: RibbonCapacitySummary
