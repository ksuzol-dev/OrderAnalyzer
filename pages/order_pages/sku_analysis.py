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


def render_sku_analysis(df, context, baseline_df=None):
    latest_date = context["latest_date"]
    with st.container(border=True):
        scope = st.selectbox("分析口径", ["最新日期", "最近7天", "最近30天", "全部数据"], index=2)
    scoped = _scope_df(df, latest_date, scope)
    baseline_scoped = _scope_df(baseline_df if baseline_df is not None else df, latest_date, scope)
    summary = sku_summary(scoped)

    if summary.empty:
        st.warning("当前口径下没有 SKU 数据。")
        return

    selected_orders = int(scoped["订单编号"].nunique()) if "订单编号" in scoped.columns else len(scoped)
    selected_revenue = float(scoped["支付金额"].sum()) if "支付金额" in scoped.columns else 0
    baseline_orders = int(baseline_scoped["订单编号"].nunique()) if "订单编号" in baseline_scoped.columns else len(baseline_scoped)
    baseline_revenue = float(baseline_scoped["支付金额"].sum()) if "支付金额" in baseline_scoped.columns else 0
    order_share = selected_orders / baseline_orders * 100 if baseline_orders else 0
    revenue_share = selected_revenue / baseline_revenue * 100 if baseline_revenue else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("筛选订单数", f"{selected_orders:,} 单", note=f"{scope} · 当前 SKU 合计", accent="#2563eb")
    with c2:
        metric_card("筛选收入", fmt_money(selected_revenue), note=f"{summary['SKU'].nunique():,} 个商品 ID", accent="#16a34a")
    with c3:
        metric_card("订单占总盘", fmt_percent(order_share), note=f"总盘 {baseline_orders:,} 单", accent="#f97316")
    with c4:
        metric_card("收入占总盘", fmt_percent(revenue_share), note=f"总盘 {fmt_money(baseline_revenue)}", accent="#7c3aed")

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
