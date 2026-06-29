import streamlit as st

from components.ui import inject_global_styles
from pages.order_pages.dashboard import render_dashboard
from pages.order_pages.data_check import render_data_check
from pages.order_pages.sku_analysis import render_sku_analysis
from pages.order_pages.trend_analysis import render_trend_analysis
from pages.order_pages.user_analysis import render_user_analysis
from services.analytics import build_daily, get_latest_context
from services.data_loader import prepare_data, read_file


st.set_page_config(page_title="OrderAnalyzer 订单分析平台", page_icon="📊", layout="wide")
inject_global_styles()


st.markdown('<div class="main-title">📊 OrderAnalyzer 订单分析平台</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">本地运行 · 数据不上传服务器 · 只统计支付成功订单 · V0.3 Foundation</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("数据导入")
    uploaded = st.file_uploader("上传订单 CSV / Excel", type=["csv", "xlsx", "xls"])
    st.caption("建议上传从店铺后台导出的订单明细。系统只在本机内存中分析。")
    st.divider()
    page = st.radio(
        "页面",
        ["Dashboard", "趋势分析", "SKU 分析", "用户分析", "数据检查"],
        label_visibility="collapsed",
    )

if not uploaded:
    st.markdown(
        '<div class="tip-box">请先在左侧上传订单 CSV / Excel。上传后会自动生成 Dashboard、趋势、SKU 和数据检查。</div>',
        unsafe_allow_html=True,
    )
    st.stop()

try:
    raw_df = read_file(uploaded)
    df, detected = prepare_data(raw_df)
except Exception as exc:
    st.error(f"文件解析失败：{exc}")
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

context = get_latest_context(daily, selected_skus)

if page == "Dashboard":
    render_dashboard(view_df, daily, context)
elif page == "趋势分析":
    render_trend_analysis(daily, context)
elif page == "SKU 分析":
    render_sku_analysis(df, context)
elif page == "用户分析":
    render_user_analysis(df, detected)
elif page == "数据检查":
    render_data_check(raw_df, df, detected)
