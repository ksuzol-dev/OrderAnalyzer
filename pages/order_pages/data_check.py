import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import fmt_date, metric_card, section, style_chart
from services.data_loader import FIELD_SPECS, REQUIRED_FIELDS, clean_money, is_success


def _field_table(detected):
    rows = []
    for field, candidates in FIELD_SPECS.items():
        raw_field = detected.get(field)
        required = field in REQUIRED_FIELDS
        rows.append(
            {
                "标准字段": field,
                "识别结果": raw_field or "未识别",
                "字段要求": "必需" if required else "可选",
                "状态": "已识别" if raw_field else ("缺失" if required else "未提供"),
                "候选字段": "、".join(candidates),
            }
        )
    return pd.DataFrame(rows)


def _quality_metrics(raw_df, df, detected):
    status_col = detected.get("支付状态")
    amount_col = detected.get("支付金额")
    time_col = detected.get("支付完成时间")
    success_raw = raw_df[status_col].apply(is_success) if status_col else pd.Series(False, index=raw_df.index)
    amount_issue_count = 0
    time_issue_count = 0
    if amount_col:
        amount_issue_count = int(raw_df.loc[success_raw, amount_col].apply(clean_money).eq(0).sum())
    if time_col:
        time_issue_count = int(pd.to_datetime(raw_df.loc[success_raw, time_col], errors="coerce").isna().sum())
    duplicate_count = int(df["订单编号"].duplicated().sum()) if "订单编号" in df.columns else 0
    return amount_issue_count, time_issue_count, duplicate_count


def render_data_check(raw_df, df, detected):
    section("数据检查", "运营问题：本次上传的数据是否足够完整，可以支撑看板判断？")
    recognized_count = sum(value is not None for value in detected.values())
    amount_issue_count, time_issue_count, duplicate_count = _quality_metrics(raw_df, df, detected)
    date_min = df["日期"].min() if "日期" in df.columns and not df.empty else None
    date_max = df["日期"].max() if "日期" in df.columns and not df.empty else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("原始行数", f"{len(raw_df):,}", note="上传文件总行数", accent="#2563eb")
    with c2:
        metric_card("支付成功行数", f"{len(df):,}", note="进入分析的数据", accent="#16a34a")
    with c3:
        metric_card("支付成功订单数", f"{df['订单编号'].nunique():,}", note="按订单编号去重", accent="#7c3aed")
    with c4:
        metric_card("识别字段数", f"{recognized_count}/{len(detected)}", note="必需字段需全部识别", accent="#f97316")

    c5, c6, c7 = st.columns(3)
    with c5:
        metric_card("金额为 0/未识别", f"{amount_issue_count:,} 行", note="支付成功行内", accent="#dc2626" if amount_issue_count else "#16a34a")
    with c6:
        metric_card("无效支付时间", f"{time_issue_count:,} 行", note="支付成功行内", accent="#dc2626" if time_issue_count else "#16a34a")
    with c7:
        metric_card("重复订单编号", f"{duplicate_count:,} 行", note="标准化后检查", accent="#dc2626" if duplicate_count else "#16a34a")

    if date_min and date_max:
        st.markdown(
            f'<div class="small-muted">订单日期范围：<strong>{fmt_date(date_min)}</strong> 至 <strong>{fmt_date(date_max)}</strong></div>',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        section("字段识别状态", "运营问题：系统是否识别到了分析所需字段？")
        st.dataframe(_field_table(detected), use_container_width=True, hide_index=True)

    status_col = detected.get("支付状态")
    if status_col:
        with st.container(border=True):
            section("支付状态分布", "运营问题：本次文件里有多少数据真正进入分析？")
            status_counts = raw_df[status_col].fillna("空值").astype(str).value_counts().reset_index()
            status_counts.columns = ["支付状态", "行数"]
            fig = px.bar(status_counts, x="支付状态", y="行数", title="原始文件支付状态分布")
            fig.update_traces(marker_color="#2563eb")
            fig.update_layout(xaxis_title="支付状态", yaxis_title="行数")
            st.plotly_chart(style_chart(fig, height=320), use_container_width=True)
            st.dataframe(status_counts, use_container_width=True, hide_index=True)

    with st.container(border=True):
        section("标准字段预览", "运营问题：进入看板的数据是否已经被正确标准化？")
        standard_columns = [
            "订单编号",
            "产品线",
            "商品ID",
            "商品名",
            "SKU",
            "SKU说明",
            "支付金额",
            "支付完成时间",
            "来源平台",
            "开通方式",
            "VIP ID",
            "VIP 名称",
            "VIP 类型",
            "source_platform",
            "product_line",
            "product_id",
            "product_name",
            "sku_key",
            "sku_label",
            "pay_type",
            "vip_id",
            "vip_name",
            "vip_type",
            "user_id",
            "user_name",
            "user_phone",
            "registration_time",
            "class_name",
        ]
        available_columns = [column for column in standard_columns if column in df.columns]
        st.dataframe(df[available_columns].head(50), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section("原始字段")
            st.dataframe({"字段名": list(raw_df.columns)}, use_container_width=True, hide_index=True)

    with right:
        with st.container(border=True):
            section("原始数据样例")
            st.dataframe(raw_df.head(50), use_container_width=True)
