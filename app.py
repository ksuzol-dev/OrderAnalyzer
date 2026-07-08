import streamlit as st

from components.ui import fmt_date, inject_global_styles, message_box, page_header
from pages.order_pages.ab_test_analysis import render_ab_test_analysis
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
    "导入订单 CSV / Excel 后，快速查看订单、收入、SKU、趋势、AB 测试和数据质量。",
    eyebrow="OrderAnalyzer · V0.3.11 AB Test Analysis",
    chips=["本地运行", "数据不上传服务器", "只统计支付成功订单"],
)

with st.sidebar:
    st.header("数据导入")
    uploaded = st.file_uploader("上传订单 CSV / Excel", type=["csv", "xlsx", "xls"])
    st.caption("建议上传从店铺后台导出的订单明细。系统只在本机内存中分析。")
    st.divider()
    page = st.radio(
        "页面",
        ["Dashboard", "趋势分析", "SKU 分析", "AB 测试", "用户分析", "数据检查"],
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
    available_dates = sorted(df["日期"].dropna().unique().tolist())
    min_date = available_dates[0]
    max_date = available_dates[-1]
    selected_date_range = st.date_input("日期范围", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected_date_range, tuple):
        if len(selected_date_range) < 2:
            st.info("请选择完整的开始日期和结束日期。")
            st.stop()
        start_date, end_date = selected_date_range
    else:
        start_date = selected_date_range
        end_date = selected_date_range
    if start_date > end_date:
        st.warning("开始日期不能晚于结束日期。")
        st.stop()

    date_df = df[(df["日期"] >= start_date) & (df["日期"] <= end_date)].copy()
    if date_df.empty:
        st.warning("当前日期范围内没有支付成功订单。")
        st.stop()
    st.caption(f"当前日期：{fmt_date(start_date)} 至 {fmt_date(end_date)}")

    product_line_options = sorted(date_df["产品线"].dropna().unique().tolist()) if "产品线" in date_df.columns else []
    selected_product_lines = st.multiselect("产品线", product_line_options, default=[])
    line_df = date_df[date_df["产品线"].isin(selected_product_lines)].copy() if selected_product_lines else date_df.copy()

    all_sku_options_df = sku_summary(df)
    all_sku_labels = dict(zip(all_sku_options_df["SKU"], all_sku_options_df["SKU说明"]))
    all_sku_keys = set(all_sku_options_df["SKU"].tolist())
    if "selected_skus" in st.session_state:
        st.session_state.selected_skus = [key for key in st.session_state.selected_skus if key in all_sku_keys]

    sku_options_df = sku_summary(line_df)
    current_sku_options = sku_options_df["SKU"].tolist()
    retained_sku_options = [
        key for key in st.session_state.get("selected_skus", []) if key not in current_sku_options and key in all_sku_keys
    ]
    sku_options = current_sku_options + retained_sku_options
    sku_labels = {**all_sku_labels, **dict(zip(sku_options_df["SKU"], sku_options_df["SKU说明"]))}
    selected_skus = st.multiselect(
        "商品ID / 商品名",
        sku_options,
        default=[],
        format_func=lambda key: sku_labels.get(key, key),
        key="selected_skus",
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
context = get_latest_context(daily, selected_sku_labels, selected_product_lines, (start_date, end_date))

if page == "Dashboard":
    render_dashboard(view_df, daily, context)
elif page == "趋势分析":
    render_trend_analysis(daily, context)
elif page == "SKU 分析":
    render_sku_analysis(view_df, context, baseline_df=line_df)
elif page == "AB 测试":
    render_ab_test_analysis(view_df, context)
elif page == "用户分析":
    render_user_analysis(view_df, detected)
elif page == "数据检查":
    render_data_check(raw_df, df, detected)
