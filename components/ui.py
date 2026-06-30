import pandas as pd
import streamlit as st


CSS = """
<style>
.stApp {background: #f5f7fb;}
.block-container {padding-top: 1.15rem; padding-bottom: 2.5rem; max-width: 1400px;}
[data-testid="stSidebar"] {background: #ffffff; border-right: 1px solid #e5e7eb;}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {color: #111827;}
div[data-testid="stVerticalBlock"] {gap: 0.75rem;}
.app-header {border: 1px solid #e5e7eb; border-radius: 8px; padding: 18px 20px; background: #ffffff; margin-bottom: 16px;}
.header-eyebrow {font-size: 12px; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 0; margin-bottom: 6px;}
.main-title {font-size: 28px; font-weight: 800; margin-bottom: 6px; color: #0f172a; line-height: 1.2;}
.sub-title {font-size: 14px; color: #64748b; margin-bottom: 10px;}
.header-chips {display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;}
.chip {display: inline-flex; align-items: center; border: 1px solid #dbe3ef; border-radius: 999px; padding: 4px 10px; color: #334155; background: #f8fafc; font-size: 12px;}
.metric-card {border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 18px; background: #ffffff; box-shadow: 0 1px 2px rgba(15,23,42,0.05); min-height: 128px; position: relative; overflow: hidden;}
.metric-card:before {content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--accent, #2563eb);}
.metric-title {font-size: 13px; color: #64748b; margin-bottom: 8px;}
.metric-value {font-size: 28px; font-weight: 800; color: #0f172a; line-height: 1.2;}
.metric-note {font-size: 12px; color: #64748b; margin-top: 7px;}
.delta-up {font-size: 13px; color: #15803d; margin-top: 8px;}
.delta-down {font-size: 13px; color: #b91c1c; margin-top: 8px;}
.delta-flat {font-size: 13px; color: #64748b; margin-top: 8px;}
.section-title {font-size: 18px; font-weight: 750; margin: 6px 0 4px 0; color: #0f172a;}
.question {font-size: 13px; color: #64748b; margin: 0 0 12px 0;}
.panel-note {font-size: 13px; color: #475569; line-height: 1.55;}
.tip-box {border: 1px solid #bfdbfe; background: #eff6ff; border-radius: 8px; padding: 14px 16px; color: #1e3a8a;}
.success-box {border: 1px solid #bbf7d0; background: #f0fdf4; border-radius: 8px; padding: 14px 16px; color: #166534;}
.warning-box {border: 1px solid #fed7aa; background: #fff7ed; border-radius: 8px; padding: 14px 16px; color: #9a3412;}
.placeholder-box {border: 1px dashed #cbd5e1; background: #ffffff; border-radius: 8px; padding: 18px; color: #334155;}
.status-ok {color: #15803d; font-weight: 700;}
.status-miss {color: #b91c1c; font-weight: 700;}
.small-muted {font-size: 12px; color: #64748b;}
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


def metric_card(title, value, note=None, delta=None, delta_kind="flat", accent="#2563eb"):
    delta_html = ""
    if delta is not None:
        cls = {"up": "delta-up", "down": "delta-down", "flat": "delta-flat"}.get(delta_kind, "delta-flat")
        delta_html = f'<div class="{cls}">{delta}</div>'
    note_html = f'<div class="metric-note">{note}</div>' if note else ""
    st.markdown(
        f'<div class="metric-card" style="--accent: {accent};"><div class="metric-title">{title}</div><div class="metric-value">{value}</div>{delta_html}{note_html}</div>',
        unsafe_allow_html=True,
    )


def page_header(title, subtitle=None, eyebrow="OrderAnalyzer", chips=None):
    subtitle_html = f'<div class="sub-title">{subtitle}</div>' if subtitle else ""
    chips_html = ""
    if chips:
        chips_html = '<div class="header-chips">' + "".join(f'<span class="chip">{chip}</span>' for chip in chips) + "</div>"
    st.markdown(
        f'<div class="app-header"><div class="header-eyebrow">{eyebrow}</div><div class="main-title">{title}</div>{subtitle_html}{chips_html}</div>',
        unsafe_allow_html=True,
    )


def section(title, question=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if question:
        st.markdown(f'<div class="question">{question}</div>', unsafe_allow_html=True)


def message_box(body, title=None, variant="info"):
    cls = {"info": "tip-box", "success": "success-box", "warning": "warning-box"}.get(variant, "tip-box")
    title_html = f"<strong>{title}</strong><br>" if title else ""
    st.markdown(f'<div class="{cls}">{title_html}{body}</div>', unsafe_allow_html=True)


def style_chart(fig, height=360):
    fig.update_layout(
        height=height,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(color="#334155"),
        title=dict(font=dict(size=16, color="#0f172a")),
        margin=dict(l=20, r=20, t=55, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e5e7eb")
    fig.update_yaxes(gridcolor="#eef2f7", zerolinecolor="#e5e7eb")
    return fig
