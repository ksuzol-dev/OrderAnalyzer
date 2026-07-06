import streamlit as st

from components.ui import inject_global_styles, message_box, page_header
from pages.order_pages.dashboard import render_dashboard
from pages.order_pages.data_check import render_data_check
from pages.order_pages.sku_analysis import render_sku_analysis
from pages.order_pages.trend_analysis import render_trend_analysis
from pages.order_pages.user_analysis import render_user_analysis
from services.analytics import build_daily, get_latest_context, sku_summary
from services.data_loader import prepare_data, read_file


st.set_page_config(page_title="OrderAnalyzer 订单分析平台", page_icon="📊", layout="wide")
inject_global_styles()


page_header(
    "订单运营分析平台",
    "导入订单 CSV / Excel 后，快速查看订单、收入、SKU、趋势和数据质量。",
    eyebrow="OrderAnalyzer · V0.3.6 Product ID Core SKU",
    chips=["本地运行", "数据不上传服务器", "只统计支付成功订单"],
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
    message_box(
        "请先在左侧上传订单 CSV / Excel。上传后会自动生成 Dashboard、趋势、SKU 和数据检查。",
        title="等待导入数据",
        variant="info",
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
    product_line_options = sorted(df["产品线"].dropna().unique().tolist()) if "产品线" in df.columns else []
    selected_product_lines = st.multiselect("产品线", product_line_options, default=[])
    line_df = df[df["产品线"].isin(selected_product_lines)].copy() if selected_product_lines else df.copy()

    sku_options_df = sku_summary(line_df)
    sku_options = sku_options_df["SKU"].tolist()
    sku_labels = dict(zip(sku_options_df["SKU"], sku_options_df["SKU说明"]))
    selected_skus = st.multiselect(
        "商品ID / 商品名",
        sku_options,
        default=[],
        format_func=lambda key: sku_labels.get(key, key),
    )
    if not selected_product_lines:
        st.caption("未选择产品线时默认分析全部产品线。")
    if not selected_skus:
        st.caption("未选择时默认分析全部 SKU。")

view_df = line_df[line_df["SKU"].isin(selected_skus)].copy() if selected_skus else line_df.copy()
daily = build_daily(view_df)

if daily.empty:
    st.warning("当前筛选条件下没有支付成功订单。")
    st.stop()

selected_sku_labels = [sku_labels.get(key, key) for key in selected_skus]
context = get_latest_context(daily, selected_sku_labels, selected_product_lines)

if page == "Dashboard":
    render_dashboard(view_df, daily, context)
elif page == "趋势分析":
    render_trend_analysis(daily, context)
elif page == "SKU 分析":
    render_sku_analysis(view_df, context)
elif page == "用户分析":
    render_user_analysis(df, detected)
elif page == "数据检查":
    render_data_check(raw_df, df, detected)
