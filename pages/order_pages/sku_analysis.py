from datetime import timedelta

import plotly.express as px
import streamlit as st

from components.ui import fmt_money, fmt_percent, metric_card, section, style_chart
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
    with st.container(border=True):
        scope = st.selectbox("分析口径", ["最新日期", "最近7天", "最近30天", "全部数据"], index=2)
    scoped = _scope_df(df, latest_date, scope)
    summary = sku_summary(scoped)

    if summary.empty:
        st.warning("当前口径下没有 SKU 数据。")
        return

    revenue_top10 = summary.head(10)["收入"].sum()
    concentration = revenue_top10 / summary["收入"].sum() * 100 if summary["收入"].sum() else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("SKU 数量", f"{summary['SKU'].nunique():,}", note=scope, accent="#2563eb")
    with c2:
        metric_card("TOP1 收入占比", fmt_percent(summary.iloc[0]["收入占比"]), note=summary.iloc[0]["SKU说明"], accent="#f97316")
    with c3:
        metric_card("TOP10 收入", fmt_money(revenue_top10), note="收入贡献", accent="#16a34a")
    with c4:
        metric_card("TOP10 集中度", fmt_percent(concentration), note="收入集中度", accent="#7c3aed")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section("SKU 订单数占比", "运营问题：订单主要集中在哪些 SKU，是否存在爆款依赖？")
            order_chart = summary.sort_values("订单数", ascending=False).head(10)
            fig_order = px.bar(order_chart, x="订单数占比", y="SKU说明", orientation="h", title=f"{scope} 商品 ID 订单数占比 TOP10")
            fig_order.update_traces(marker_color="#2563eb")
            fig_order.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="订单数占比", yaxis_title="")
            st.plotly_chart(style_chart(fig_order, height=420), use_container_width=True)

    with right:
        with st.container(border=True):
            section("SKU 收入占比", "运营问题：真正贡献收入的是哪些 SKU，和订单数排行是否一致？")
            revenue_chart = summary.sort_values("收入", ascending=False).head(10)
            fig_revenue = px.bar(revenue_chart, x="收入占比", y="SKU说明", orientation="h", title=f"{scope} 商品 ID 收入占比 TOP10")
            fig_revenue.update_traces(marker_color="#16a34a")
            fig_revenue.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="收入占比", yaxis_title="")
            st.plotly_chart(style_chart(fig_revenue, height=420), use_container_width=True)

    with st.container(border=True):
        section("SKU 全量明细", "运营问题：每个商品 ID 的订单数、收入和占比是否健康？")
        table = summary.copy()
        table["收入"] = table["收入"].map(fmt_money)
        table["订单数占比"] = table["订单数占比"].map(fmt_percent)
        table["收入占比"] = table["收入占比"].map(fmt_percent)
        st.dataframe(table[["商品ID", "商品名", "SKU", "订单数", "订单数占比", "收入", "收入占比"]], use_container_width=True, hide_index=True)
