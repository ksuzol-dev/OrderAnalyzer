import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import fmt_date, metric_card, section, style_chart


def _valid_text(series, invalid_values=None):
    invalid = set(invalid_values or [])
    cleaned = series.fillna("").astype(str).str.strip()
    return cleaned[~cleaned.isin(["", "nan", "None", *invalid])]


def _unique_user_count(df):
    for column in ["vip_id", "user_id", "user_phone", "user_name"]:
        if column in df.columns:
            values = _valid_text(df[column])
            if not values.empty:
                return values.nunique(), column
    return df["订单编号"].nunique(), "订单编号"


def _has_vip_source_view(df):
    vip_count = _valid_text(df.get("vip_id", pd.Series(dtype=str))).nunique() if "vip_id" in df.columns else 0
    platform_count = (
        _valid_text(df.get("source_platform", pd.Series(dtype=str)), ["未识别来源"]).nunique()
        if "source_platform" in df.columns
        else 0
    )
    return vip_count > 0 or platform_count > 0


def _has_class_registration_view(df):
    registration_count = df["registration_time"].notna().sum() if "registration_time" in df.columns else 0
    class_count = (
        _valid_text(df.get("class_name", pd.Series(dtype=str)), ["未识别班级"]).nunique()
        if "class_name" in df.columns
        else 0
    )
    return registration_count > 0 or class_count > 0


def _value_counts(df, column, missing_label, invalid_values=None):
    if column not in df.columns:
        return pd.DataFrame(columns=[column, "用户数"])
    values = df[column].fillna(missing_label).astype(str).str.strip().replace("", missing_label)
    if invalid_values:
        values = values.replace({value: missing_label for value in invalid_values})
    counts = values.value_counts().reset_index()
    counts.columns = [column, "用户数"]
    return counts


def _add_share(counts):
    total = counts["用户数"].sum() if "用户数" in counts.columns else 0
    counts = counts.copy()
    counts["占比"] = counts["用户数"] / total * 100 if total else 0
    counts["占比显示"] = counts["占比"].map(lambda value: f"{value:.1f}%")
    return counts


def _render_vip_id_distribution(df):
    if "vip_id" not in df.columns:
        return
    vip_id_df = _value_counts(df, "vip_id", "未识别 VIP ID", ["未识别 VIP ID"])
    if vip_id_df.empty:
        return
    vip_id_df = _add_share(vip_id_df)
    top_row = vip_id_df.iloc[0]

    with st.container(border=True):
        section("VIP ID 占比分布", "运营问题：用户主要集中在哪些 VIP ID，是否存在明显的权益层级集中？")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("TOP VIP ID", str(top_row["vip_id"]), note="用户数最高", accent="#16a34a")
        with c2:
            metric_card("TOP VIP ID 用户数", f"{int(top_row['用户数']):,}", note="当前筛选范围", accent="#2563eb")
        with c3:
            metric_card("TOP VIP ID 占比", top_row["占比显示"], note="按支付用户行数计算", accent="#f97316")

        left, right = st.columns([1.2, 1])
        with left:
            fig = px.pie(vip_id_df, names="vip_id", values="用户数", title="VIP ID 用户占比", hole=0.42)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(style_chart(fig, height=380), use_container_width=True)
        with right:
            table = vip_id_df.rename(columns={"vip_id": "VIP ID"})
            st.dataframe(table[["VIP ID", "用户数", "占比显示"]], use_container_width=True, hide_index=True)


def _render_vip_source_analysis(df):
    section("VIP / 来源平台分析", "运营问题：用户主要来自哪些平台，不同 VIP 类型的用户结构是否健康？")
    vip_count = _valid_text(df["vip_id"]).nunique() if "vip_id" in df.columns else 0
    platform_df = _value_counts(df, "source_platform", "未识别来源", ["未识别来源"])
    type_df = _value_counts(df, "vip_type", "未识别类型")
    top_platform = platform_df.iloc[0]["source_platform"] if not platform_df.empty else "-"
    top_type = type_df.iloc[0]["vip_type"] if not type_df.empty else "-"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("VIP ID 数量", f"{vip_count:,}", note="按 vip_id 去重", accent="#16a34a")
    with c2:
        metric_card("来源平台数", f"{len(platform_df):,}", note=f"TOP：{top_platform}", accent="#2563eb")
    with c3:
        metric_card("VIP 类型数", f"{len(type_df):,}", note=f"TOP：{top_type}", accent="#7c3aed")
    with c4:
        metric_card("支付用户行数", f"{len(df):,}", note="当前筛选范围", accent="#f97316")

    _render_vip_id_distribution(df)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section("来源平台分布", "运营问题：主要获客来源在哪里？")
            fig = px.bar(platform_df, x="source_platform", y="用户数", title="来源平台用户数")
            fig.update_traces(marker_color="#2563eb")
            fig.update_layout(xaxis_title="来源平台", yaxis_title="用户数")
            st.plotly_chart(style_chart(fig, height=340), use_container_width=True)

    with right:
        with st.container(border=True):
            section("VIP 类型分布", "运营问题：用户集中在哪类 VIP？")
            fig = px.bar(type_df, x="vip_type", y="用户数", title="VIP 类型用户数")
            fig.update_traces(marker_color="#7c3aed")
            fig.update_layout(xaxis_title="VIP 类型", yaxis_title="用户数")
            st.plotly_chart(style_chart(fig, height=340), use_container_width=True)

    if "source_platform" in df.columns and "vip_type" in df.columns:
        with st.container(border=True):
            section("来源平台 x VIP 类型", "运营问题：不同渠道带来的 VIP 类型是否不同？")
            matrix = (
                df.assign(
                    source_platform=df["source_platform"].fillna("未识别来源").replace("", "未识别来源"),
                    vip_type=df["vip_type"].fillna("未识别类型").replace("", "未识别类型"),
                )
                .groupby(["source_platform", "vip_type"])
                .size()
                .reset_index(name="用户数")
            )
            fig = px.density_heatmap(matrix, x="source_platform", y="vip_type", z="用户数", histfunc="sum", title="渠道与 VIP 类型交叉分布")
            fig.update_layout(xaxis_title="来源平台", yaxis_title="VIP 类型")
            st.plotly_chart(style_chart(fig, height=360), use_container_width=True)
            st.dataframe(matrix.sort_values("用户数", ascending=False), use_container_width=True, hide_index=True)


def _render_class_registration_analysis(df):
    section("注册时间 / 班级用户分析", "运营问题：用户注册增长如何，哪些班级用户最多？")
    user_count, user_key = _unique_user_count(df)
    registered = df[df["registration_time"].notna()].copy() if "registration_time" in df.columns else pd.DataFrame()
    class_df = _value_counts(df, "class_name", "未识别班级", ["未识别班级"])
    latest_registration = registered["registration_time"].max() if not registered.empty else None
    class_count = _valid_text(df.get("class_name", pd.Series(dtype=str)), ["未识别班级"]).nunique() if "class_name" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("用户数", f"{user_count:,}", note=f"按 {user_key} 去重", accent="#2563eb")
    with c2:
        metric_card("已识别注册时间", f"{len(registered):,} 行", note="可用于注册趋势", accent="#16a34a")
    with c3:
        metric_card("班级数量", f"{class_count:,}", note="已识别班级", accent="#7c3aed")
    with c4:
        metric_card("最新注册时间", fmt_date(latest_registration) if latest_registration is not None else "-", note="注册字段最大日期", accent="#f97316")

    if not registered.empty:
        with st.container(border=True):
            section("注册趋势", "运营问题：近期用户注册是在增长还是下降？")
            trend = registered.copy()
            trend["注册日期"] = trend["registration_time"].dt.date
            trend = trend.groupby("注册日期").size().reset_index(name="用户数").sort_values("注册日期")
            trend["日期显示"] = trend["注册日期"].map(fmt_date)
            fig = px.line(trend, x="日期显示", y="用户数", markers=True, title="每日注册用户数")
            fig.update_traces(line_color="#16a34a", marker=dict(size=8))
            fig.update_layout(xaxis_title="注册日期", yaxis_title="用户数")
            st.plotly_chart(style_chart(fig, height=360), use_container_width=True)
            st.dataframe(trend[["日期显示", "用户数"]].rename(columns={"日期显示": "注册日期"}), use_container_width=True, hide_index=True)

    with st.container(border=True):
        section("班级用户分布", "运营问题：哪些班级用户规模最大，需要重点跟进？")
        top_class = class_df.head(15)
        fig = px.bar(top_class, x="用户数", y="class_name", orientation="h", title="班级用户数 TOP15")
        fig.update_traces(marker_color="#7c3aed")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="用户数", yaxis_title="")
        st.plotly_chart(style_chart(fig, height=420), use_container_width=True)
        st.dataframe(class_df, use_container_width=True, hide_index=True)


def _render_user_detail(df):
    with st.container(border=True):
        section("用户明细预览", "运营问题：标准化后的用户字段是否符合预期？")
        columns = [
            "订单编号",
            "SKU",
            "source_platform",
            "pay_type",
            "vip_id",
            "vip_name",
            "vip_type",
            "user_id",
            "user_name",
            "user_phone",
            "registration_time",
            "class_name",
            "支付金额",
            "支付完成时间",
        ]
        available = [column for column in columns if column in df.columns]
        detail = df[available].head(100).copy()
        if "registration_time" in detail.columns:
            detail["registration_time"] = detail["registration_time"].astype(str).replace("NaT", "")
        st.dataframe(detail, use_container_width=True, hide_index=True)


def render_user_analysis(df, detected):
    user_like_columns = [column for column in df.columns if any(key in str(column) for key in ["用户", "客户", "买家", "手机号", "会员", "VIP", "班级", "注册"])]
    has_vip_source = _has_vip_source_view(df)
    has_class_registration = _has_class_registration_view(df)

    section("用户分析", "运营问题：根据当前表格式，拆分查看 VIP/来源平台或注册时间/班级用户。")
    mode_labels = []
    if has_vip_source:
        mode_labels.append("VIP / 来源平台")
    if has_class_registration:
        mode_labels.append("注册时间 / 班级用户")
    if not mode_labels:
        mode_labels.append("字段识别")

    selected_mode = st.segmented_control("用户分析视角", mode_labels, default=mode_labels[0])

    if selected_mode == "VIP / 来源平台":
        _render_vip_source_analysis(df)
    elif selected_mode == "注册时间 / 班级用户":
        _render_class_registration_analysis(df)
    else:
        st.info("当前表未识别到 VIP / 来源平台或注册时间 / 班级字段。请在数据检查页确认字段名称。")

    _render_user_detail(df)

    if user_like_columns:
        with st.container(border=True):
            section("已识别用户相关字段")
            st.dataframe({"字段名": user_like_columns}, use_container_width=True, hide_index=True)

    with st.expander("当前已识别订单字段"):
        st.json(detected)
