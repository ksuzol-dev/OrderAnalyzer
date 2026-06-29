import pandas as pd
import streamlit as st


CSS = """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1380px;}
[data-testid="stSidebar"] {background: #f8fafc;}
.main-title {font-size: 30px; font-weight: 800; margin-bottom: 4px; color: #0f172a;}
.sub-title {font-size: 14px; color: #64748b; margin-bottom: 18px;}
.metric-card {border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 18px; background: #ffffff; box-shadow: 0 1px 2px rgba(15,23,42,0.05);}
.metric-title {font-size: 13px; color: #64748b; margin-bottom: 8px;}
.metric-value {font-size: 28px; font-weight: 800; color: #0f172a; line-height: 1.2;}
.metric-note {font-size: 12px; color: #64748b; margin-top: 7px;}
.delta-up {font-size: 13px; color: #15803d; margin-top: 8px;}
.delta-down {font-size: 13px; color: #b91c1c; margin-top: 8px;}
.delta-flat {font-size: 13px; color: #64748b; margin-top: 8px;}
.section-title {font-size: 19px; font-weight: 750; margin: 22px 0 10px 0; color: #0f172a;}
.question {font-size: 13px; color: #475569; margin: -4px 0 12px 0;}
.tip-box {border: 1px solid #dbeafe; background: #eff6ff; border-radius: 8px; padding: 14px 16px; color: #1e3a8a;}
.placeholder-box {border: 1px dashed #cbd5e1; background: #f8fafc; border-radius: 8px; padding: 18px; color: #334155;}
hr {margin: 1rem 0;}
</style>
"""


def inject_global_styles():
    st.markdown(CSS, unsafe_allow_html=True)


def fmt_date(value):
    if pd.isna(value):
        return "-"
    date_value = pd.to_datetime(value).date() if not hasattr(value, "year") else value
    return f"{date_value.year}年{date_value.month}月{date_value.day}日"


def fmt_money(value):
    try:
        number = float(value)
    except Exception:
        number = 0
    return f"¥{number:,.0f}" if abs(number - round(number)) < 0.001 else f"¥{number:,.2f}"


def fmt_percent(value):
    try:
        number = float(value)
    except Exception:
        number = 0
    return f"{number:.1f}%"


def metric_card(title, value, note=None, delta=None, delta_kind="flat"):
    delta_html = ""
    if delta is not None:
        cls = {"up": "delta-up", "down": "delta-down", "flat": "delta-flat"}.get(delta_kind, "delta-flat")
        delta_html = f'<div class="{cls}">{delta}</div>'
    note_html = f'<div class="metric-note">{note}</div>' if note else ""
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">{title}</div><div class="metric-value">{value}</div>{delta_html}{note_html}</div>',
        unsafe_allow_html=True,
    )


def section(title, question=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if question:
        st.markdown(f'<div class="question">{question}</div>', unsafe_allow_html=True)
