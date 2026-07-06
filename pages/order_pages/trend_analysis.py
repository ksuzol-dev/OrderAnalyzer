import re

import plotly.express as px
import streamlit as st

from components.ui import fmt_date, fmt_money, metric_card, section, style_chart
from services.analytics import build_trend_window


def render_trend_analysis(daily, context):
    latest_date = context["latest_date"]
    days_label = st.segmented_control("时间范围", ["最近14天", "最近30天", "最近60天"], default="最近30天")
    days = int(re.search(r"\d+", days_label).group())
    trend = build_trend_window(daily, latest_date, days)
    chart = trend.copy()
    chart["日期显示"] = chart["日期"].map(fmt_date)
    peak_order_day = trend.sort_values("订单数", ascending=False).iloc[0]
    peak_revenue_day = trend.sort_values("收入", ascending=False).iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("周期订单数", f"{int(trend['订单数'].sum()):,} 单", note=days_label, accent="#2563eb")
    with c2:
        metric_card("周期收入", fmt_money(trend["收入"].sum()), note=days_label, accent="#16a34a")
    with c3:
        metric_card("峰值订单日", fmt_date(peak_order_day["日期"]), note=f"{int(peak_order_day['订单数'])} 单", accent="#f97316")

    with st.container(border=True):
        section("订单趋势", "运营问题：选定周期内，订单数的高峰和低谷分别出现在哪几天？")
        order_fig = px.line(chart, x="日期显示", y="订单数", markers=True, title=f"{days_label}支付成功订单数")
        order_fig.update_traces(line_color="#2563eb", marker=dict(size=8))
        order_fig.update_layout(xaxis_title="日期", yaxis_title="订单数")
        st.plotly_chart(style_chart(order_fig, height=360), use_container_width=True)

    with st.container(border=True):
        section("收入趋势", "运营问题：收入变化是否和订单量同步，还是由客单价变化推动？")
        revenue_fig = px.bar(chart, x="日期显示", y="收入", title=f"{days_label}收入")
        revenue_fig.update_traces(marker_color="#16a34a")
        revenue_fig.update_layout(xaxis_title="日期", yaxis_title="收入")
        st.plotly_chart(style_chart(revenue_fig, height=360), use_container_width=True)
        st.markdown(f'<div class="small-muted">收入峰值出现在 {fmt_date(peak_revenue_day["日期"])}，收入 {fmt_money(peak_revenue_day["收入"])}。</div>', unsafe_allow_html=True)

    with st.container(border=True):
        section("每日数据表", "运营问题：具体是哪一天拉高或拖低了趋势？")
        table = trend.sort_values("日期", ascending=False).copy()
        table["日期"] = table["日期"].map(fmt_date)
        table["收入"] = table["收入"].map(fmt_money)
        table["客单价"] = table["客单价"].map(fmt_money)
        st.dataframe(table[["日期", "订单数", "收入", "客单价"]], use_container_width=True, hide_index=True)
