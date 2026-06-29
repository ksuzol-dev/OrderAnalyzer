import re
from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="OrderAnalyzer 订单分析平台", page_icon="📊", layout="wide")

CSS = """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1360px;}
[data-testid="stSidebar"] {background: #f8fafc;}
.main-title {font-size: 30px; font-weight: 800; margin-bottom: 4px;}
.sub-title {font-size: 14px; color: #64748b; margin-bottom: 18px;}
.card {border: 1px solid #e5e7eb; border-radius: 16px; padding: 18px 20px; background: #ffffff; box-shadow: 0 1px 3px rgba(15,23,42,0.06);} 
.card-title {font-size: 14px; color: #64748b; margin-bottom: 8px;}
.card-value {font-size: 30px; font-weight: 800; color: #0f172a; line-height: 1.2;}
.delta-up {font-size: 13px; color: #16a34a; margin-top: 8px;}
.delta-down {font-size: 13px; color: #dc2626; margin-top: 8px;}
.delta-flat {font-size: 13px; color: #64748b; margin-top: 8px;}
.section-title {font-size: 20px; font-weight: 750; margin: 20px 0 10px 0; color: #0f172a;}
.tip-box {border: 1px solid #dbeafe; background: #eff6ff; border-radius: 14px; padding: 14px 16px; color: #1e3a8a;}
hr {margin: 1rem 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def fmt_date(d):
    if pd.isna(d):
        return "-"
    d = pd.to_datetime(d).date() if not hasattr(d, "year") else d
    return f"{d.year}年{d.month}月{d.day}日"


def fmt_money(x):
    try:
        x = float(x)
    except Exception:
        x = 0
    return f"¥{x:,.0f}" if abs(x - round(x)) < 0.001 else f"¥{x:,.2f}"


def clean_money(v):
    if pd.isna(v):
        return 0.0
    s = str(v).replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else 0.0


def is_success(v):
    return "支付成功" in str(v)


def pct_change(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)
    if previous == 0 and current == 0:
        return "0%", "flat"
    if previous == 0:
        return "+100%", "up"
    p = (current - previous) / previous * 100
    sign = "+" if p >= 0 else ""
    kind = "up" if p > 0 else "down" if p < 0 else "flat"
    return f"{sign}{p:.1f}%", kind


def find_col(columns, candidates):
    for c in candidates:
        if c in columns:
            return c
    for col in columns:
        for c in candidates:
            if c.lower() in str(col).lower():
                return col
    return None


@st.cache_data(show_spinner=False)
def read_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="gbk")
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("目前只支持 CSV / Excel 文件")


def prepare_data(raw):
    cols = list(raw.columns)
    order_col = find_col(cols, ["订单编号", "订单号", "Id", "ID"])
    sku_col = find_col(cols, ["商品名", "SKU", "sku", "商品名称", "商品"])
    status_col = find_col(cols, ["支付状态", "订单状态", "状态"])
    amount_col = find_col(cols, ["支付金额", "实付金额", "金额", "订单金额"])
    time_col = find_col(cols, ["支付完成时间", "支付时间", "付款时间", "完成时间", "更新时间", "订单日期"])

    missing = []
    for label, col in [("订单编号", order_col), ("商品名/SKU", sku_col), ("支付状态", status_col), ("支付金额", amount_col), ("支付完成时间", time_col)]:
        if col is None:
            missing.append(label)
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))

    df = raw.copy()
    df = df[df[status_col].apply(is_success)].copy()
    df["订单编号"] = df[order_col].astype(str)
    df["SKU"] = df[sku_col].fillna("未命名商品").astype(str)
    df["支付金额"] = df[amount_col].apply(clean_money)
    df["支付完成时间"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["支付完成时间"])
    df["日期"] = df["支付完成时间"].dt.date
    return df, {"订单编号": order_col, "SKU": sku_col, "支付状态": status_col, "支付金额": amount_col, "支付完成时间": time_col}


def build_daily(df):
    if df.empty:
        return pd.DataFrame(columns=["日期", "订单数", "收入"])
    return df.groupby("日期").agg(订单数=("订单编号", "nunique"), 收入=("支付金额", "sum")).reset_index().sort_values("日期")


def day_stats(daily, d):
    row = daily[daily["日期"] == d]
    if row.empty:
        return {"日期": d, "订单数": 0, "收入": 0.0}
    return {"日期": d, "订单数": int(row.iloc[0]["订单数"]), "收入": float(row.iloc[0]["收入"])}


def card(title, value, compare_label=None, current=None, previous=None):
    delta_html = ""
    if compare_label is not None:
        pct, kind = pct_change(current, previous)
        cls = {"up": "delta-up", "down": "delta-down", "flat": "delta-flat"}[kind]
        delta_html = f'<div class="{cls}">{compare_label}：{pct}</div>'
    st.markdown(f'<div class="card"><div class="card-title">{title}</div><div class="card-value">{value}</div>{delta_html}</div>', unsafe_allow_html=True)


def plot_trend(daily, latest_date, days):
    start = latest_date - timedelta(days=days - 1)
    base = pd.DataFrame({"日期": pd.date_range(start, latest_date).date})
    trend = base.merge(daily, on="日期", how="left").fillna({"订单数": 0, "收入": 0})
    trend["日期显示"] = trend["日期"].map(fmt_date)
    fig1 = px.line(trend, x="日期显示", y="订单数", markers=True, title=f"最近{days}天订单数趋势")
    fig1.update_layout(xaxis_title="日期", yaxis_title="订单数", height=360, margin=dict(l=20, r=20, t=55, b=20))
    fig2 = px.bar(trend, x="日期显示", y="收入", title=f"最近{days}天收入趋势")
    fig2.update_layout(xaxis_title="日期", yaxis_title="收入", height=360, margin=dict(l=20, r=20, t=55, b=20))
    return fig1, fig2


st.markdown('<div class="main-title">📊 OrderAnalyzer 订单分析平台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">本地运行 · 数据不上传服务器 · 只统计支付成功订单 · MVP V0.2</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("数据导入")
    uploaded = st.file_uploader("上传订单导出文件", type=["csv", "xlsx", "xls"])
    st.caption("建议每天导出全量历史订单，再上传到这里分析。")
    st.divider()
    page = st.radio("页面", ["今日概览", "趋势分析", "SKU分析", "日期对比", "数据检查"], label_visibility="collapsed")

if not uploaded:
    st.markdown('<div class="tip-box">请先在左侧上传订单 CSV / Excel。上传后会自动生成运营看板。</div>', unsafe_allow_html=True)
    st.stop()

try:
    raw_df = read_file(uploaded)
    df, detected = prepare_data(raw_df)
except Exception as e:
    st.error(f"文件解析失败：{e}")
    st.stop()

if df.empty:
    st.warning("没有找到支付成功订单，请检查支付状态字段。")
    st.stop()

with st.sidebar:
    st.header("筛选")
    sku_options = sorted(df["SKU"].dropna().unique().tolist())
    selected_skus = st.multiselect("SKU / 商品", sku_options, default=[])
    if not selected_skus:
        st.caption("未选择时默认分析全部 SKU。")

view_df = df[df["SKU"].isin(selected_skus)].copy() if selected_skus else df.copy()
daily = build_daily(view_df)
if daily.empty:
    st.warning("当前筛选条件下没有支付成功订单。")
    st.stop()

latest_date = daily["日期"].max()
prev_date = latest_date - timedelta(days=1)
week_date = latest_date - timedelta(days=7)
month_date = latest_date - timedelta(days=30)
latest = day_stats(daily, latest_date)
prev = day_stats(daily, prev_date)
week = day_stats(daily, week_date)
month = day_stats(daily, month_date)
analysis_target = "全部 SKU" if not selected_skus else "、".join(selected_skus[:3]) + (" 等" if len(selected_skus) > 3 else "")

if page == "今日概览":
    st.markdown(f"**当前分析对象：** {analysis_target}　　**最新订单日期：** {fmt_date(latest_date)}")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("最新日期订单数", f"{latest['订单数']:,} 单", "较前一日", latest["订单数"], prev["订单数"])
    with c2:
        card("最新日期收入", fmt_money(latest["收入"]), "较前一日", latest["收入"], prev["收入"])
    with c3:
        card("较上周同日订单", pct_change(latest["订单数"], week["订单数"])[0], f"{fmt_date(week_date)} 订单", latest["订单数"], week["订单数"])
    with c4:
        card("较上月同日订单", pct_change(latest["订单数"], month["订单数"])[0], f"{fmt_date(month_date)} 订单", latest["订单数"], month["订单数"])

    st.markdown('<div class="section-title">核心对比</div>', unsafe_allow_html=True)
    compare = pd.DataFrame([
        {"对比项": "最新日期", "日期": fmt_date(latest_date), "订单数": latest["订单数"], "收入": fmt_money(latest["收入"])},
        {"对比项": "前一日", "日期": fmt_date(prev_date), "订单数": prev["订单数"], "收入": fmt_money(prev["收入"])},
        {"对比项": "上周同日", "日期": fmt_date(week_date), "订单数": week["订单数"], "收入": fmt_money(week["收入"])},
        {"对比项": "上月同日", "日期": fmt_date(month_date), "订单数": month["订单数"], "收入": fmt_money(month["收入"])},
    ])
    st.dataframe(compare, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">运营摘要</div>', unsafe_allow_html=True)
    order_pct, _ = pct_change(latest["订单数"], prev["订单数"])
    rev_pct, _ = pct_change(latest["收入"], prev["收入"])
    st.success(f"{fmt_date(latest_date)}，{analysis_target} 支付成功订单 {latest['订单数']} 单，收入 {fmt_money(latest['收入'])}；较前一日订单变化 {order_pct}，收入变化 {rev_pct}。")

    st.markdown('<div class="section-title">最近14天趋势</div>', unsafe_allow_html=True)
    fig1, fig2 = plot_trend(daily, latest_date, 14)
    st.plotly_chart(fig1, use_container_width=True)

elif page == "趋势分析":
    days = st.segmented_control("时间范围", ["最近14天", "最近30天", "最近60天"], default="最近30天")
    n = int(re.search(r"\d+", days).group())
    fig1, fig2 = plot_trend(daily, latest_date, n)
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)

elif page == "SKU分析":
    st.markdown('<div class="section-title">SKU 排行</div>', unsafe_allow_html=True)
    rank_range = st.selectbox("排行口径", ["最新日期", "最近7天", "最近30天", "全部数据"])
    if rank_range == "最新日期":
        rank_df = df[df["日期"] == latest_date]
    elif rank_range == "最近7天":
        rank_df = df[df["日期"] >= latest_date - timedelta(days=6)]
    elif rank_range == "最近30天":
        rank_df = df[df["日期"] >= latest_date - timedelta(days=29)]
    else:
        rank_df = df
    sku_rank = rank_df.groupby("SKU").agg(订单数=("订单编号", "nunique"), 收入=("支付金额", "sum")).reset_index().sort_values(["收入", "订单数"], ascending=False).head(20)
    sku_rank["收入"] = sku_rank["收入"].map(fmt_money)
    st.dataframe(sku_rank, use_container_width=True, hide_index=True)

    if len(sku_rank) > 0:
        chart_df = rank_df.groupby("SKU").agg(订单数=("订单编号", "nunique"), 收入=("支付金额", "sum")).reset_index().sort_values("收入", ascending=False).head(10)
        fig = px.bar(chart_df, x="收入", y="SKU", orientation="h", title="SKU 收入 TOP10")
        fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(fig, use_container_width=True)

elif page == "日期对比":
    st.markdown('<div class="section-title">自定义日期对比</div>', unsafe_allow_html=True)
    available_dates = sorted(daily["日期"].unique().tolist(), reverse=True)
    default_dates = [d for d in [latest_date, prev_date, week_date, month_date] if d in available_dates]
    selected_dates = st.multiselect("选择要对比的日期", available_dates, default=default_dates, format_func=fmt_date)
    rows = []
    for d in selected_dates:
        s = day_stats(daily, d)
        rows.append({"日期": fmt_date(d), "订单数": s["订单数"], "收入": fmt_money(s["收入"])})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "数据检查":
    st.markdown('<div class="section-title">数据概况</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        card("原始行数", f"{len(raw_df):,}")
    with c2:
        card("支付成功订单行数", f"{len(df):,}")
    with c3:
        card("SKU 数量", f"{df['SKU'].nunique():,}")
    st.write("已识别字段：")
    st.json(detected)
    st.write("原始数据样例：")
    st.dataframe(raw_df.head(50), use_container_width=True)
