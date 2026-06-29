import plotly.express as px
import streamlit as st

from components.ui import fmt_date, fmt_money, metric_card, section
from services.analytics import build_trend_window, pct_change


def render_dashboard(df, daily, context):
    latest = context["latest"]
    previous = context["previous"]
    latest_date = context["latest_date"]
    target = context["target"]
    aov_delta, aov_kind, _ = pct_change(latest["客单价"], previous["客单价"])
    order_delta, order_kind, _ = pct_change(latest["订单数"], previous["订单数"])
    revenue_delta, revenue_kind, _ = pct_change(latest["收入"], previous["收入"])

    st.markdown(f"**当前分析对象：** {target}　　**最新订单日期：** {fmt_date(latest_date)}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("今日订单", f"{latest['订单数']:,} 单", delta=f"较前一日 {order_delta}", delta_kind=order_kind)
    with c2:
        metric_card("今日收入", fmt_money(latest["收入"]), delta=f"较前一日 {revenue_delta}", delta_kind=revenue_kind)
    with c3:
        metric_card("客单价", fmt_money(latest["客单价"]), delta=f"较前一日 {aov_delta}", delta_kind=aov_kind)
    with c4:
        metric_card("支付成功 SKU", f"{df['SKU'].nunique():,} 个", note="当前筛选范围内")

    section("最近 14 天订单趋势", "运营问题：最近两周订单量是在增长、下滑，还是只是单日波动？")
    trend = build_trend_window(daily, latest_date, 14)
    chart = trend.copy()
    chart["日期显示"] = chart["日期"].map(fmt_date)
    fig = px.line(chart, x="日期显示", y="订单数", markers=True, title="每日支付成功订单数")
    fig.update_layout(xaxis_title="日期", yaxis_title="订单数", height=340, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)

    section("运营摘要")
    st.success(
        f"{fmt_date(latest_date)}，{target} 支付成功订单 {latest['订单数']} 单，收入 {fmt_money(latest['收入'])}，"
        f"客单价 {fmt_money(latest['客单价'])}；较前一日订单 {order_delta}，收入 {revenue_delta}。"
    )
