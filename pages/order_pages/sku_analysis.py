from datetime import timedelta

import plotly.express as px
import streamlit as st

from components.ui import fmt_money, fmt_percent, section
from services.analytics import sku_summary


def _scope_df(df, latest_date, scope):
    if scope == "最新日期":
        return df[df["日期"] == latest_date]
    if scope == "最近7天":
        return df[df["日期"] >= latest_date - timedelta(days=6)]
    if scope == "最近30天":
        return df[df["日期"] >= latest_date - timedelta(days=29)]
    return df


def render_sku_analysis(df, context):
    latest_date = context["latest_date"]
    scope = st.selectbox("分析口径", ["最新日期", "最近7天", "最近30天", "全部数据"], index=2)
    scoped = _scope_df(df, latest_date, scope)
    summary = sku_summary(scoped)

    if summary.empty:
        st.warning("当前口径下没有 SKU 数据。")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("SKU 数量", f"{summary['SKU'].nunique():,}")
    with c2:
        st.metric("TOP1 收入占比", fmt_percent(summary.iloc[0]["收入占比"]))
    with c3:
        st.metric("TOP10 收入", fmt_money(summary.head(10)["收入"].sum()))

    section("SKU 订单数占比", "运营问题：订单主要集中在哪些 SKU，是否存在爆款依赖？")
    order_chart = summary.sort_values("订单数", ascending=False).head(10)
    fig_order = px.bar(order_chart, x="订单数占比", y="SKU", orientation="h", title=f"{scope} SKU 订单数占比 TOP10")
    fig_order.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig_order, use_container_width=True)

    section("SKU 收入占比", "运营问题：真正贡献收入的是哪些 SKU，和订单数排行是否一致？")
    revenue_chart = summary.sort_values("收入", ascending=False).head(10)
    fig_revenue = px.bar(revenue_chart, x="收入占比", y="SKU", orientation="h", title=f"{scope} SKU 收入占比 TOP10")
    fig_revenue.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig_revenue, use_container_width=True)

    section("SKU TOP10 明细", "运营问题：TOP SKU 的订单数、收入和占比是否健康？")
    table = summary.head(10).copy()
    table["收入"] = table["收入"].map(fmt_money)
    table["订单数占比"] = table["订单数占比"].map(fmt_percent)
    table["收入占比"] = table["收入占比"].map(fmt_percent)
    st.dataframe(table[["SKU", "订单数", "订单数占比", "收入", "收入占比"]], use_container_width=True, hide_index=True)
