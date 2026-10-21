from __future__ import annotations

from .models import CouponClickReport, CouponClickSnapshot, MonthlyMetric, RibbonDataSummary
from .ribbon_data import summarize_weekday_hour_patterns


def _format_snapshot(snapshot: CouponClickSnapshot, description: str) -> str:
    lines = [f"{description}（{snapshot.period}）:"]
    if snapshot.is_in_progress:
        lines.append("  ※月の途中のデータです。件数が少ないのは正常なので、それ自体は指摘しないこと。")
    if not snapshot.entries:
        lines.append("  クリックデータなし")
        return "\n".join(lines)

    total_clicks = sum(e.clicks for e in snapshot.entries)
    lines.append(f"  合計クリック数: {total_clicks}件")
    ranked = sorted(snapshot.entries, key=lambda e: -e.clicks)[:15]
    for e in ranked:
        lines.append(f"  - [{e.category}] {e.coupon_name} （クリック数: {e.clicks}）")
    return "\n".join(lines)


def _format_coupon_section(coupon_report: CouponClickReport | None) -> str:
    if coupon_report is None:
        return ""
    parts = ["", "【クーポンのクリック実績（特集・こだわり・ブログ経由、参考情報）】"]
    parts.append(_format_snapshot(coupon_report.current, "今月"))
    if coupon_report.previous is not None:
        parts.append(_format_snapshot(coupon_report.previous, "直近の完了月"))
    return "\n".join(parts)


def _format_concept_section(store_concept: str | None) -> str:
    if not store_concept:
        return ""
    return f"\n\n【店舗のこだわり・方針（要約済み、参考情報）】\n{store_concept}"


def _format_ribbon_section(ribbon_data: RibbonDataSummary | None) -> str:
    if ribbon_data is None:
        return ""

    lines = ["", "【リボンデータ（年齢・性別・残キャパ状況、参考情報）】"]

    demo = ribbon_data.demographics
    age_text = " / ".join(f"{band}{pct:.1f}%" for band, pct in demo.age_pct.items())
    lines.append(f"年齢分布: {age_text}")
    lines.append(f"性別分布: 女性{demo.female_pct:.1f}% / 男性{demo.male_pct:.1f}%")

    def format_segments(segments) -> str:
        return ", ".join(f"{s.age_band}{s.gender}{s.percentage:.1f}%" for s in segments)

    if ribbon_data.top_segments.new_customer:
        lines.append(f"新規予約の年代×性別（上位）: {format_segments(ribbon_data.top_segments.new_customer)}")
    if ribbon_data.top_segments.repeat_customer:
        lines.append(
            f"リピート予約の年代×性別（上位）: {format_segments(ribbon_data.top_segments.repeat_customer)}"
        )

    if ribbon_data.capacity.status_ratio:
        ratio_text = " / ".join(
            f"{status}{pct:.1f}%" for status, pct in ribbon_data.capacity.status_ratio.items()
        )
        lines.append(f"残キャパ状況（営業時間内の割合）: {ratio_text}")

    busy_labels, slow_labels = summarize_weekday_hour_patterns(ribbon_data.capacity.slots)
    if busy_labels:
        lines.append(f"混雑しやすい曜日・時間帯（残キャパ20%未満が多い）: {', '.join(busy_labels)}")
    if slow_labels:
        lines.append(f"空きが出やすい曜日・時間帯（残キャパ50%以上が多い）: {', '.join(slow_labels)}")

    return "\n".join(lines)


def build_prompt(
    cvr: MonthlyMetric,
    acr: MonthlyMetric,
    coupon_report: CouponClickReport | None = None,
    store_concept: str | None = None,
    ribbon_data: RibbonDataSummary | None = None,
) -> str:
    """AIへ送信する想定のプロンプトを組み立てる（デモでは送信せず、画面表示のみ）。"""
    base = (
        f"対象月: {cvr.period}\n"
        f"CVR: 自店 {cvr.salon_value:.1f}% / 同プラン・同エリア平均 {cvr.area_average:.1f}%\n"
        f"ACR: 自店 {acr.salon_value:.1f}% / 同プラン・同エリア平均 {acr.area_average:.1f}%\n"
        "この数値をもとに、今月確認すべきポイントを教えてください。"
        "クーポンのクリック実績データがあれば、具体的にどのクーポンを推す・見直すべきかも"
        "確認候補として触れてください。"
        "混雑しやすい・空きが出やすい曜日や時間帯のデータがあれば、いつクーポンや"
        "訴求を強化すべきかも、曜日・時間帯とクーポン内容を結びつけた確認候補として"
        "触れてください。"
    )
    return (
        base
        + _format_concept_section(store_concept)
        + _format_ribbon_section(ribbon_data)
        + _format_coupon_section(coupon_report)
    )

