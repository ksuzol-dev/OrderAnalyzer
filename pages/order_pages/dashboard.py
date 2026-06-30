import plotly.express as px
import streamlit as st

from components.ui import fmt_date, fmt_money, fmt_percent, message_box, metric_card, section, style_chart
from services.analytics import build_trend_window, pct_change


def render_dashboard(df, daily, context):
    latest = context["latest"]
    previous = context["previous"]
    latest_date = context["latest_date"]
    target = context["target"]
    aov_delta, aov_kind, _ = pct_change(latest["客单价"], previous["客单价"])
    order_delta, order_kind, _ = pct_change(latest["订单数"], previous["订单数"])
    revenue_delta, revenue_kind, _ = pct_change(latest["收入"], previous["收入"])
    order_total = int(daily["订单数"].sum())
    revenue_total = float(daily["收入"].sum())
    top_sku = df.groupby("SKU").agg(订单数=("订单编号", "nunique"), 收入=("支付金额", "sum")).reset_index()
    top_sku = top_sku.sort_values(["收入", "订单数"], ascending=False)
    top_sku_name = top_sku.iloc[0]["SKU"] if not top_sku.empty else "-"
    top_sku_share = top_sku.iloc[0]["收入"] / revenue_total * 100 if revenue_total else 0

    st.markdown(
        f'<div class="small-muted">当前分析对象：<strong>{target}</strong>　最新订单日期：<strong>{fmt_date(latest_date)}</strong></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("最新日期订单", f"{latest['订单数']:,} 单", delta=f"较前一日 {order_delta}", delta_kind=order_kind, accent="#2563eb")
    with c2:
        metric_card("最新日期收入", fmt_money(latest["收入"]), delta=f"较前一日 {revenue_delta}", delta_kind=revenue_kind, accent="#16a34a")
    with c3:
        metric_card("客单价", fmt_money(latest["客单价"]), delta=f"较前一日 {aov_delta}", delta_kind=aov_kind, accent="#7c3aed")
    with c4:
        metric_card("支付成功 SKU", f"{df['SKU'].nunique():,} 个", note=f"累计 {order_total:,} 单", accent="#f97316")

    message_box(
        f"{fmt_date(latest_date)}，{target} 支付成功订单 {latest['订单数']} 单，收入 {fmt_money(latest['收入'])}，"
        f"客单价 {fmt_money(latest['客单价'])}；较前一日订单 {order_delta}，收入 {revenue_delta}。",
        title="运营摘要",
        variant="success" if order_kind != "down" and revenue_kind != "down" else "warning",
    )

    left, right = st.columns([2, 1])
    trend = build_trend_window(daily, latest_date, 14)
    chart = trend.copy()
    chart["日期显示"] = chart["日期"].map(fmt_date)
    with left:
        with st.container(border=True):
            section("最近 14 天订单趋势", "运营问题：最近两周订单量是在增长、下滑，还是只是单日波动？")
            fig = px.line(chart, x="日期显示", y="订单数", markers=True, title="每日支付成功订单数")
            fig.update_traces(line_color="#2563eb", marker=dict(size=8))
            fig.update_layout(xaxis_title="日期", yaxis_title="订单数")
            st.plotly_chart(style_chart(fig, height=360), use_container_width=True)
    with right:
        with st.container(border=True):
            section("SKU 快览", "运营问题：当前收入是否过度集中在单一 SKU？")
            st.markdown(f"**累计收入**  \n{fmt_money(revenue_total)}")
            st.markdown(f"**TOP SKU**  \n{top_sku_name}")
            st.markdown(f"**TOP SKU 收入占比**  \n{fmt_percent(top_sku_share)}")
            st.markdown(f'<div class="small-muted">当 TOP SKU 占比持续升高时，需要关注爆款依赖和库存风险。</div>', unsafe_allow_html=True)
