"""架空のサロン「Sample Hair Salon」のデモ用データを生成する。

本番の `src/models.py` のデータ構造（ReportSummary / CouponClickReport / RibbonDataSummary）と
同じ列構成・型の JSON を `demo_data/` に書き出す。実データは一切使わない。

    python demo_data/generate.py

固定シードなので、何度実行しても同じ結果になる。
"""

from __future__ import annotations

import calendar
import json
import random
from datetime import date
from pathlib import Path

SEED = 20260920
OUT_DIR = Path(__file__).resolve().parent

STORE_NAME = "Sample Hair Salon"
REPORT_MONTH = "2026-09"  # 直近月（月の途中のデータ）
UPDATED_AT = "2026/09/20"
CAPACITY_YEAR, CAPACITY_MONTH = 2026, 10  # 残キャパ表の対象月（来月分）

# 月ごとの季節係数（1月〜12月）。3月・8月・12月が繁忙期、1〜2月・6〜7月が閑散期。
SEASONAL = [0.82, 0.85, 1.12, 1.00, 0.98, 0.88, 0.86, 1.10, 1.02, 1.00, 0.97, 1.15]

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


def month_sequence_ending_at(report_month: str, count: int) -> list[str]:
    year, month = (int(p) for p in report_month.split("-"))
    periods = []
    for _ in range(count):
        periods.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(periods))


def build_series(rng: random.Random, periods: list[str], base_salon: float, base_area: float, noise: float):
    """季節変動付きの13か月系列を作る。自店はエリア平均より変動がやや大きい。"""
    salon, area = [], []
    for p in periods:
        month = int(p.split("-")[1])
        factor = SEASONAL[month - 1]
        area.append(round(base_area * (1 + (factor - 1) * 0.5) + rng.uniform(-noise, noise) * 0.4, 2))
        salon.append(round(base_salon * factor + rng.uniform(-noise, noise), 2))
    return salon, area


def build_report_summary(rng: random.Random) -> dict:
    periods = month_sequence_ending_at(REPORT_MONTH, 13)
    # ACRはエリア平均より高く、CVRはエリア平均よりやや低い（「クーポンの訴求を見直したい」という筋書き）
    acr_salon, acr_area = build_series(rng, periods, base_salon=24.0, base_area=21.5, noise=1.2)
    cvr_salon, cvr_area = build_series(rng, periods, base_salon=2.6, base_area=3.1, noise=0.25)

    def metric(series_salon: list[float], series_area: list[float]) -> dict:
        return {"period": periods[-1], "salon_value": series_salon[-1], "area_average": series_area[-1]}

    def series(series_salon: list[float], series_area: list[float]) -> dict:
        return {"periods": periods, "salon_values": series_salon, "area_averages": series_area}

    return {
        "report_month": REPORT_MONTH,
        "updated_at": UPDATED_AT,
        "store_name": STORE_NAME,
        "cvr": metric(cvr_salon, cvr_area),
        "acr": metric(acr_salon, acr_area),
        "cvr_series": series(cvr_salon, cvr_area),
        "acr_series": series(acr_salon, acr_area),
    }


# (カテゴリ, ラベル, クーポン名, 基準クリック数)。メニューごとの単価差はクーポン名の価格で表す。
COUPON_CATALOG = [
    ("特集", "初夏の新色カラー特集", "【新規】カット+透明感カラー ¥8,800", 46),
    ("特集", "初夏の新色カラー特集", "【新規】カット+フルカラー ¥7,700", 38),
    ("特集", "髪質改善特集", "【新規】カット+髪質改善トリートメント ¥11,000", 29),
    ("特集", "髪質改善特集", "【全員】髪質改善ストレート+カット ¥18,700", 12),
    ("特集", "メンズ特集", "【メンズ】カット+眉カット ¥4,400", 21),
    ("こだわり", "駅から徒歩3分", "【平日限定】カット ¥4,950", 17),
    ("こだわり", "レイヤーカットが得意", "【新規】レイヤーカット+ケアブロー ¥5,500", 24),
    ("こだわり", "ダメージレス施術", "【新規】カット+ハイライト ¥13,200", 9),
    ("ブログ", "秋色ヘアカタログ", "【ブログ限定】カット+アッシュカラー ¥8,250", 14),
    ("ブログ", "前髪カットのコツ", "【前髪カット】前髪のみ ¥1,100", 8),
]


def build_coupon_report(rng: random.Random) -> dict:
    prev_period = "2026-08"

    def snapshot(period: str, in_progress: bool, scale: float) -> dict:
        entries = []
        for category, label, coupon_name, base in COUPON_CATALOG:
            clicks = max(0, round(base * scale * rng.uniform(0.8, 1.2)))
            entries.append({"category": category, "label": label, "coupon_name": coupon_name, "clicks": clicks})
        return {"period": period, "is_in_progress": in_progress, "entries": entries}

    return {
        "current": snapshot(REPORT_MONTH, True, 0.62),  # 月の途中なので件数は少なめ
        "previous": snapshot(prev_period, False, 1.0),
    }


def split_to_total(rng: random.Random, weights: list[float], total: float = 100.0) -> list[float]:
    """重みをもとに、合計がちょうど total になる小数1桁の配分を返す。"""
    jittered = [w * rng.uniform(0.95, 1.05) for w in weights]
    s = sum(jittered)
    values = [round(total * w / s, 1) for w in jittered]
    values[0] = round(values[0] + (total - sum(values)), 1)
    return values


def build_demographics(rng: random.Random) -> dict:
    female, male, unknown = split_to_total(rng, [71, 27, 2])
    age_labels = ["20代未満", "20代", "30代", "40代", "50代以上", "未設定"]
    age_values = split_to_total(rng, [8, 38, 31, 15, 7, 1])
    return {
        "female_pct": female,
        "male_pct": male,
        "unknown_gender_pct": unknown,
        "age_pct": dict(zip(age_labels, age_values)),
    }


def build_top_segments(rng: random.Random) -> dict:
    def top5(candidates: list[tuple[str, str, float]]) -> list[dict]:
        scored = [(band, gender, round(w * rng.uniform(0.92, 1.08), 1)) for band, gender, w in candidates]
        scored.sort(key=lambda item: -item[2])
        return [{"age_band": b, "gender": g, "percentage": p} for b, g, p in scored[:5]]

    # 新規は20代女性・30代女性が中心、リピートは30代・40代女性が厚い
    new_customer = top5(
        [
            ("20代", "女性", 24),
            ("30代", "女性", 17),
            ("20代", "男性", 8),
            ("40代", "女性", 7),
            ("30代", "男性", 6),
            ("20代未満", "女性", 5),
            ("50代以上", "女性", 3),
        ]
    )
    repeat_customer = top5(
        [
            ("30代", "女性", 26),
            ("20代", "女性", 19),
            ("40代", "女性", 13),
            ("30代", "男性", 7),
            ("50代以上", "女性", 5),
            ("20代", "男性", 4),
            ("40代", "男性", 3),
        ]
    )
    return {"new_customer": new_customer, "repeat_customer": repeat_customer}


def slot_status(rng: random.Random, weekday: str, hour: int, minute: int) -> str:
    """曜日・時間帯ごとの混み具合。土日と平日夜が埋まりやすく、平日昼が空きやすい。"""
    t = hour + minute / 60
    if weekday in ("土", "日"):
        busy = 0.62 if 10 <= t < 17 else 0.35
    elif weekday in ("金",):
        busy = 0.5 if t >= 17 else 0.2
    else:
        busy = 0.42 if t >= 18 else 0.1
    slow = 0.55 if weekday in ("火", "水", "木") and 11 <= t < 16 else 0.18
    r = rng.random()
    if r < busy:
        return "残キャパ20%未満"
    if r < busy + slow:
        return "残キャパ50%以上"
    return "残キャパ50%-20%"


def build_capacity(rng: random.Random) -> dict:
    days = calendar.monthrange(CAPACITY_YEAR, CAPACITY_MONTH)[1]
    times = [(h, m) for h in range(9, 21) for m in (0, 30)]  # 09:00〜20:30 の30分コマ
    slots = []
    for day in range(1, days + 1):
        d = date(CAPACITY_YEAR, CAPACITY_MONTH, day)
        weekday = WEEKDAYS[d.weekday()]
        for hour, minute in times:
            closed = weekday == "月" or hour >= 20 or (weekday in ("土", "日") and hour >= 19)
            status = "営業時間外" if closed else slot_status(rng, weekday, hour, minute)
            slots.append(
                {
                    "date": d.isoformat(),
                    "weekday": weekday,
                    "time_label": f"{hour:02d}:{minute:02d}",
                    "status": status,
                }
            )

    business = [s for s in slots if s["status"] != "営業時間外"]
    status_ratio = {}
    for status in ("残キャパ50%以上", "残キャパ50%-20%", "残キャパ20%未満"):
        count = sum(1 for s in business if s["status"] == status)
        status_ratio[status] = round(count / len(business) * 100, 1)
    return {"slots": slots, "status_ratio": status_ratio}


def write_json(name: str, data: dict) -> None:
    path = OUT_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.name}")


def main() -> None:
    rng = random.Random(SEED)
    write_json("report_summary.json", build_report_summary(rng))
    write_json("coupon_report.json", build_coupon_report(rng))
    write_json(
        "ribbon_data.json",
        {
            "demographics": build_demographics(rng),
            "top_segments": build_top_segments(rng),
            "capacity": build_capacity(rng),
        },
    )


if __name__ == "__main__":
    main()
