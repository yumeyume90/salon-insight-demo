from __future__ import annotations

from .models import RibbonCapacitySlot

_CAPACITY_CLOSED_STATUS = "営業時間外"
_CAPACITY_UNKNOWN_STATUS = "対象外"



def summarize_weekday_hour_patterns(
    slots: list[RibbonCapacitySlot], top_n: int = 3
) -> tuple[list[str], list[str]]:
    """曜日×時間帯（1時間単位）ごとに、月内で残キャパ20%未満／50%以上だった割合を集計し、
    特に傾向が強い上位N件を「土曜11時台」のようなラベルのリストとして返す。

    戻り値は (混雑しやすい時間帯のラベル一覧, 空きが出やすい時間帯のラベル一覧)。
    「今月の重点」に、いつ・どのクーポンを打ち出すべきかを考える材料として渡すためのもの。
    """
    business_slots = [s for s in slots if s.status not in (_CAPACITY_CLOSED_STATUS, _CAPACITY_UNKNOWN_STATUS)]
    if not business_slots:
        return [], []

    counts_by_key: dict[tuple[str, str], dict[str, int]] = {}
    for slot in business_slots:
        hour = slot.time_label.split(":")[0]
        key = (slot.weekday, hour)
        counts = counts_by_key.setdefault(key, {})
        counts[slot.status] = counts.get(slot.status, 0) + 1

    busy_scores = []
    slow_scores = []
    for (weekday, hour), counts in counts_by_key.items():
        total = sum(counts.values())
        label = f"{weekday}曜{hour}時台"
        busy_ratio = counts.get("残キャパ20%未満", 0) / total
        slow_ratio = counts.get("残キャパ50%以上", 0) / total
        if busy_ratio > 0:
            busy_scores.append((busy_ratio, label))
        if slow_ratio > 0:
            slow_scores.append((slow_ratio, label))

    busy_scores.sort(key=lambda item: item[0], reverse=True)
    slow_scores.sort(key=lambda item: item[0], reverse=True)

    busy_labels = [label for _, label in busy_scores[:top_n]]
    slow_labels = [label for _, label in slow_scores[:top_n]]
    return busy_labels, slow_labels

