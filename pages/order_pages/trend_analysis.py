import re

import plotly.express as px
import streamlit as st

from components.ui import fmt_date, fmt_money, section
from services.analytics import build_trend_window


def render_trend_analysis(daily, context):
    latest_date = context["latest_date"]
    days_label = st.segmented_control("时间范围", ["最近14天", "最近30天", "最近60天"], default="最近30天")
    days = int(re.search(r"\d+", days_label).group())
    trend = build_trend_window(daily, latest_date, days)
    chart = trend.copy()
    chart["日期显示"] = chart["日期"].map(fmt_date)

    section("订单趋势", "运营问题：选定周期内，订单数的高峰和低谷分别出现在哪几天？")
    order_fig = px.line(chart, x="日期显示", y="订单数", markers=True, title=f"{days_label}支付成功订单数")
    order_fig.update_layout(xaxis_title="日期", yaxis_title="订单数", height=360, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(order_fig, use_container_width=True)

    section("收入趋势", "运营问题：收入变化是否和订单量同步，还是由客单价变化推动？")
    revenue_fig = px.bar(chart, x="日期显示", y="收入", title=f"{days_label}收入")
    revenue_fig.update_layout(xaxis_title="日期", yaxis_title="收入", height=360, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(revenue_fig, use_container_width=True)

    section("每日数据表", "运营问题：具体是哪一天拉高或拖低了趋势？")
    table = trend.sort_values("日期", ascending=False).copy()
    table["日期"] = table["日期"].map(fmt_date)
    table["收入"] = table["收入"].map(fmt_money)
    table["客单价"] = table["客单价"].map(fmt_money)
    st.dataframe(table[["日期", "订单数", "收入", "客单价"]], use_container_width=True, hide_index=True)
