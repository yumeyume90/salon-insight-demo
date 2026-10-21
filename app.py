import html

import altair as alt
import pandas as pd
import streamlit as st

from src.ai_diagnosis import build_prompt
from src.demo_content import (
    SAMPLE_OUTPUT_NOTE,
    SAMPLE_PDFS,
    load_coupon_report,
    load_report_summary,
    load_ribbon_data,
    sample_diagnosis,
)
from src.models import ReportSummary


_SALON_COLOR = "#D36F84"
_AREA_AVERAGE_COLOR = "#9CA3AF"
_FEMALE_COLOR = "#eb6834"
_MALE_COLOR = "#2a78d6"
_HEADER_BG = "#A6455A"
_CARD_BORDER = "#ECD9DC"
_TEXT_COLOR = "#262220"
_TEXT_MUTED = "#8A7B7E"
_BADGE_POSITIVE_BG = "#E4F3E7"
_BADGE_POSITIVE_TEXT = "#2F7D4F"
_BADGE_NEGATIVE_BG = "#FBEAEC"
_BADGE_NEGATIVE_TEXT = "#B3261E"
_DEFAULT_TITLE = "Sample Hair Salon"
_FONT_STACK = "'Zen Kaku Gothic New', 'Noto Sans JP', sans-serif"

_TARGET_AGE_OPTIONS = ["10代", "20代", "30代", "40代", "50代以上"]
_TARGET_GENDER_OPTIONS = ["男性", "女性", "指名なし"]
_TARGET_OCCUPATION_OPTIONS = ["学生", "主婦", "OL", "自営業", "その他"]

_NAV_ITEMS = [("kpi", "KPI"), ("trend", "推移グラフ"), ("highlight", "今月の重点")]

_CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap');

html, body, [class*="css"] {{
    font-family: {_FONT_STACK} !important;
}}

div[data-testid="stMetric"] {{
    background-color: #FFFFFF;
    border: 1px solid {_CARD_BORDER};
    border-radius: 12px;
    padding: 16px 20px;
}}

.step-heading {{
    font-size: 1.1rem;
    font-weight: 600;
    color: {_TEXT_COLOR};
    margin: 0.75rem 0 0.5rem;
}}
</style>
"""


def _nav_html(interactive: bool) -> str:
    buttons = []
    for i, (anchor, label) in enumerate(_NAV_ITEMS):
        safe_label = html.escape(label)
        if interactive and i == 0:
            style = (
                "border:none; border-radius:999px; padding:7px 18px; font-size:13px; "
                f"font-weight:700; background:#FFFFFF; color:{_HEADER_BG}; text-decoration:none;"
            )
            buttons.append(f'<a href="#{anchor}" style="{style}">{safe_label}</a>')
        elif interactive:
            style = (
                "border:none; border-radius:999px; padding:7px 18px; font-size:13px; "
                "background:transparent; color:rgba(255,255,255,0.85); text-decoration:none;"
            )
            buttons.append(f'<a href="#{anchor}" style="{style}">{safe_label}</a>')
        else:
            style = "border-radius:999px; padding:7px 18px; font-size:13px; color:rgba(255,255,255,0.7);"
            buttons.append(f"<span style=\"{style}\">{safe_label}</span>")
    return (
        '<nav style="display:flex; gap:4px; background:rgba(255,255,255,0.15); '
        f'border-radius:999px; padding:4px;">{"".join(buttons)}</nav>'
    )


def _header_html(title: str, interactive: bool) -> str:
    safe_title = html.escape(title)
    return (
        f'<div style="background-color:{_HEADER_BG}; height:64px; display:flex; '
        f'align-items:center; justify-content:space-between; padding:0 32px; '
        f'border-radius:8px; margin-bottom:24px;">'
        f'<span style="color:#FFFFFF; font-size:19px; font-weight:700;">{safe_title}</span>'
        f"{_nav_html(interactive)}"
        f"</div>"
    )


def _trend_chart(periods: list[str], salon_values: list[float], area_averages: list[float], y_title: str):
    df = pd.DataFrame(
        {
            "年月": periods * 2,
            "系列": ["自店"] * len(periods) + ["同エリア平均"] * len(periods),
            "値": list(salon_values) + list(area_averages),
        }
    )
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("年月:N", title="年月"),
            y=alt.Y("値:Q", title=y_title),
            color=alt.Color(
                "系列:N",
                title="系列",
                scale=alt.Scale(domain=["自店", "同エリア平均"], range=[_SALON_COLOR, _AREA_AVERAGE_COLOR]),
            ),
        )
    )


def _legend_html(entries: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
        f'background:{color};margin-right:5px;"></span>{html.escape(label)}</span>'
        for color, label in entries
    )
    return f'<div style="display:flex; gap:14px; font-size:12px; color:{_TEXT_MUTED};">{items}</div>'


def _render_trend_card(title: str, periods, salon_values, area_averages, y_title: str) -> None:
    with st.container(border=True):
        col_title, col_legend = st.columns([2, 3])
        with col_title:
            st.markdown(f'<div style="font-size:14px; font-weight:700;">{html.escape(title)}</div>', unsafe_allow_html=True)
        with col_legend:
            st.markdown(
                f'<div style="display:flex; justify-content:flex-end;">'
                f'{_legend_html([(_SALON_COLOR, "自店"), (_AREA_AVERAGE_COLOR, "同エリア平均")])}</div>',
                unsafe_allow_html=True,
            )
        st.altair_chart(
            _trend_chart(periods, salon_values, area_averages, y_title), use_container_width=True
        )


def _demographics_chart(segments) -> alt.LayerChart:
    df = pd.DataFrame(
        {
            "label": [f"{s.age_band} {s.gender}" for s in segments],
            "percentage": [s.percentage for s in segments],
            "性別": [s.gender for s in segments],
        }
    )
    base = alt.Chart(df).encode(
        x=alt.X("label:N", sort=None, title=None),
        y=alt.Y("percentage:Q", title="割合（%）"),
    )
    bars = base.mark_bar().encode(
        color=alt.Color(
            "性別:N",
            scale=alt.Scale(domain=["女性", "男性"], range=[_FEMALE_COLOR, _MALE_COLOR]),
            legend=None,
        )
    )
    labels = base.mark_text(dy=-8, fontWeight="bold").encode(text=alt.Text("percentage:Q", format=".1f"))
    return bars + labels


def _render_demographics_card(top_segments) -> None:
    with st.container(border=True):
        col_title, col_legend = st.columns([2, 3])
        with col_title:
            st.markdown(
                '<div style="font-size:14px; font-weight:700;">顧客層（年代×性別、実績上位）</div>',
                unsafe_allow_html=True,
            )
        with col_legend:
            st.markdown(
                f'<div style="display:flex; justify-content:flex-end;">'
                f'{_legend_html([(_FEMALE_COLOR, "女性"), (_MALE_COLOR, "男性")])}</div>',
                unsafe_allow_html=True,
            )
        st.caption(
            "※ 年代×性別の完全な組み合わせ集計はPDFに含まれていないため、実績が多い上位5件のみを表示しています。"
        )
        if top_segments.new_customer:
            st.caption("新規予約")
            st.altair_chart(_demographics_chart(top_segments.new_customer), use_container_width=True)
        if top_segments.repeat_customer:
            st.caption("リピート予約")
            st.altair_chart(_demographics_chart(top_segments.repeat_customer), use_container_width=True)
        if not top_segments.new_customer and not top_segments.repeat_customer:
            st.caption("表示できる年代×性別データがありませんでした。")


def _kpi_card_html(label: str, value: float, area_average: float) -> str:
    delta = value - area_average
    if delta >= 0:
        badge_bg, badge_text, arrow = _BADGE_POSITIVE_BG, _BADGE_POSITIVE_TEXT, "&#8593;"
    else:
        badge_bg, badge_text, arrow = _BADGE_NEGATIVE_BG, _BADGE_NEGATIVE_TEXT, "&#8595;"
    return (
        f'<div style="flex:1; background:#FFFFFF; border:1px solid {_CARD_BORDER}; '
        f'border-radius:12px; padding:20px 22px;">'
        f'<div style="font-size:13px; color:{_TEXT_MUTED}; margin-bottom:10px;">{html.escape(label)}</div>'
        f'<div style="font-size:38px; font-weight:700; margin-bottom:10px;">{value:.1f}%</div>'
        f'<div style="display:inline-block; background:{badge_bg}; color:{badge_text}; font-size:12px; '
        f'font-weight:600; padding:4px 10px; border-radius:999px;">{arrow} {delta:+.1f}pt（対エリア平均）</div>'
        f"</div>"
    )


def _highlight_text_html(message: str) -> str:
    safe_message = html.escape(message).replace("\n", "<br>")
    return f'<div style="color:{_TEXT_COLOR}; font-size:13px; line-height:1.7;">{safe_message}</div>'


def _build_focus_text(target_ages, target_genders, target_occupations) -> str:
    """ターゲット層の選択（年齢層・性別・職業）を、プロンプトに使う1つの文章にまとめる。"""
    parts = []
    if target_ages:
        parts.append(f"ターゲット年齢層: {'・'.join(target_ages)}")
    if target_genders:
        parts.append(f"性別: {'・'.join(target_genders)}")
    if target_occupations:
        parts.append(f"職業: {'・'.join(target_occupations)}")
    return "、".join(parts)


def _demo_banner(description: str) -> None:
    """全画面の上部に表示する、デモであることの明示＋その画面の説明1行。"""
    st.warning("これはポートフォリオ用のデモです。表示データはすべて架空のものです")
    st.caption(description)


def _render_login() -> None:
    _demo_banner("ログイン画面です。認証処理は行わず、ボタンひとつでセットアップ画面へ進みます。")
    st.markdown(_header_html(_DEFAULT_TITLE, interactive=False), unsafe_allow_html=True)
    st.info("この画面はデモ用です。「デモとしてログイン」ボタンを押すとログインできます。")
    st.text_input("ID", value="demo", key="login_id")
    st.text_input("パスワード", value="demo", type="password", key="login_password")
    if st.button("デモとしてログイン", type="primary"):
        st.session_state["view"] = "setup"
        st.rerun()


def _run_demo(concept_text: str, focus_text: str, run_diagnosis: bool) -> None:
    """サンプルデータで結果を組み立てる。診断文は固定で、AIは呼ばない。"""
    ss = st.session_state
    summary = load_report_summary()
    coupon_report = load_coupon_report()
    ribbon_data = load_ribbon_data()

    # こだわり要約はAIを使わず、入力をそのまま使う
    concept_summary = " ".join(part for part in (concept_text.strip(), focus_text.strip()) if part)
    prompt = build_prompt(
        summary.cvr, summary.acr, coupon_report, store_concept=concept_summary, ribbon_data=ribbon_data
    )

    if not run_diagnosis:
        with st.expander("AIに送信する想定のプロンプトの内容（デモでは送信されません）", expanded=True):
            st.code(prompt, language="text")
        return

    ss["dashboard"] = {
        "summary": summary,
        "message": sample_diagnosis(summary, coupon_report, ribbon_data),
        "note": SAMPLE_OUTPUT_NOTE,
        "ribbon_data": ribbon_data,
    }
    ss["view"] = "dashboard"
    st.rerun()


def _render_setup() -> None:
    ss = st.session_state
    _demo_banner(
        "データ読み込み画面です。サンプルPDFで試すと、ダッシュボードまで一気に表示されます。"
    )
    st.markdown(_header_html(_DEFAULT_TITLE, interactive=False), unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:22px; font-weight:700; margin-bottom: 0.5rem;">データを読み込んで診断する</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '<div style="font-size:15px; font-weight:700; margin-bottom:14px;">1. Salon Report PDFと'
            "リボンデータ（PDF）を読み込みます。</div>",
            unsafe_allow_html=True,
        )
        st.file_uploader("Salon Report PDFをアップロード", type=["pdf"], key="salon_pdf_uploader", disabled=True)
        st.file_uploader("リボンデータ（PDF）をアップロード", type=["pdf"], key="ribbon_pdf_uploader", disabled=True)
        st.caption("デモではファイルは保存・送信されません（アップロード欄は無効です）。")
        run_sample = st.button("サンプルPDFで試す", type="primary")
        st.caption("架空のサンプルPDFの内容で、診断結果まで表示します。サンプルPDF自体は下から確認できます。")
        for label, path in SAMPLE_PDFS:
            st.download_button(f"{label}をダウンロード", path.read_bytes(), file_name=path.name, key=path.name)

    with st.container(border=True):
        st.markdown(
            '<div style="font-size:15px; font-weight:700; margin-bottom:16px;">2. ターゲット層とお店の'
            "こだわりを入力してください。</div>",
            unsafe_allow_html=True,
        )
        st.caption("ターゲット年齢層")
        target_ages = st.pills(
            "ターゲット年齢層", _TARGET_AGE_OPTIONS, selection_mode="multi", key="target_ages", label_visibility="collapsed"
        )
        st.caption("性別")
        target_genders = st.pills(
            "性別", _TARGET_GENDER_OPTIONS, selection_mode="multi", key="target_genders", label_visibility="collapsed"
        )
        st.caption("職業")
        target_occupations = st.pills(
            "職業", _TARGET_OCCUPATION_OPTIONS, selection_mode="multi", key="target_occupations", label_visibility="collapsed"
        )
        with st.expander("お店のこだわり・方針を編集（レイヤーカットなど）"):
            strengths_input = st.text_area("お店のこだわり・方針", key="concept_strengths", label_visibility="collapsed")
            st.caption("デモでは入力内容は保存されません。")

        col_diagnose, col_prompt = st.columns(2)
        with col_diagnose:
            run_diagnosis = st.button("診断する")
        with col_prompt:
            show_prompt = st.button("プロンプトを確認する")
        st.caption(
            "「診断する」を押すと、ダッシュボードに「今月の重点」を表示します（デモでは固定のサンプル文です）。"
            "「プロンプトを確認する」は、入力内容に応じて変わる送信予定のプロンプトを表示します。"
        )

    focus_text = _build_focus_text(target_ages, target_genders, target_occupations)
    if run_sample or run_diagnosis:
        _run_demo(strengths_input, focus_text, run_diagnosis=True)
    elif show_prompt:
        _run_demo(strengths_input, focus_text, run_diagnosis=False)


def _render_dashboard() -> None:
    ss = st.session_state
    data = ss.get("dashboard")
    if data is None:
        ss["view"] = "setup"
        st.rerun()
        return

    summary: ReportSummary = data["summary"]
    ribbon_data = data["ribbon_data"]

    _demo_banner("ダッシュボード画面です。ACR・CVRの推移、顧客層、固定のサンプル診断文を表示します。")
    header_title = summary.store_name or _DEFAULT_TITLE
    st.markdown(_header_html(header_title, interactive=True), unsafe_allow_html=True)

    st.markdown('<div id="kpi"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:13px; color:{_TEXT_MUTED}; margin-bottom:12px;">'
        f"{html.escape(summary.report_month)} 月号のデータ（データ最終更新日: "
        f"{html.escape(summary.updated_at)}）</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="display:flex; gap:16px;">'
        + _kpi_card_html("ACR（自店）", summary.acr.salon_value, summary.acr.area_average)
        + _kpi_card_html("CVR（自店）", summary.cvr.salon_value, summary.cvr.area_average)
        + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div id="trend"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:18px; font-weight:700; margin:22px 0 4px;">13か月推移</div>', unsafe_allow_html=True)
    _render_trend_card(
        "ACR", summary.acr_series.periods, summary.acr_series.salon_values, summary.acr_series.area_averages, "ACR（%）"
    )
    _render_trend_card(
        "CVR", summary.cvr_series.periods, summary.cvr_series.salon_values, summary.cvr_series.area_averages, "CVR（%）"
    )

    if ribbon_data is not None:
        _render_demographics_card(ribbon_data.top_segments)

    if st.button("詳細設定・データ更新", use_container_width=True):
        ss["view"] = "setup"
        st.rerun()
    st.caption("ターゲット層・こだわり設定の変更や、サンプルの再実行はこちら")

    st.markdown('<div id="highlight"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div style="font-size:14px; font-weight:700; margin-bottom:8px;">今月の重点</div>', unsafe_allow_html=True)
        st.markdown(_highlight_text_html(data["message"]), unsafe_allow_html=True)
        st.caption(data["note"])
    if st.button("ログイン画面に戻る"):
        ss["view"] = "login"
        st.rerun()


st.set_page_config(page_title="Sample Hair Salon - Salon Insight Demo", layout="wide")
st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

st.session_state.setdefault("view", "login")

view = st.session_state["view"]
if view == "dashboard":
    _render_dashboard()
elif view == "setup":
    _render_setup()
else:
    _render_login()
