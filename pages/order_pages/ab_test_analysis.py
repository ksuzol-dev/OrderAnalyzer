import re

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import fmt_money, fmt_percent, metric_card, section, style_chart


DIGITS = [str(value) for value in range(10)]
ODD_DIGITS = ["1", "3", "5", "7", "9"]
EVEN_DIGITS = ["0", "2", "4", "6", "8"]


def _last_digit(value):
    if pd.isna(value):
        return ""
    digits = re.findall(r"\d", str(value).strip())
    return digits[-1] if digits else ""


def _group_name(digit, a_digits, b_digits):
    if digit in a_digits:
        return "A 方案"
    if digit in b_digits:
        return "B 方案"
    return "未分组"


def _build_ab_summary(df, a_digits, b_digits):
    test_df = df.copy()
    test_df["用户ID尾数"] = test_df["user_id"].map(_last_digit) if "user_id" in test_df.columns else ""
    test_df["实验组"] = test_df["用户ID尾数"].map(lambda digit: _group_name(digit, a_digits, b_digits))

    grouped = (
        test_df.groupby("实验组")
        .agg(订单量=("订单编号", "nunique"), 订单金额=("支付金额", "sum"), 用户数=("user_id", "nunique"))
        .reset_index()
    )
    for name in ["A 方案", "B 方案", "未分组"]:
        if name not in grouped["实验组"].tolist():
            grouped = pd.concat(
                [grouped, pd.DataFrame([{"实验组": name, "订单量": 0, "订单金额": 0.0, "用户数": 0}])],
                ignore_index=True,
            )

    grouped["排序"] = grouped["实验组"].map({"A 方案": 0, "B 方案": 1, "未分组": 2}).fillna(9)
    grouped = grouped.sort_values("排序").drop(columns=["排序"]).reset_index(drop=True)

    total_orders = int(test_df["订单编号"].nunique())
    total_revenue = float(test_df["支付金额"].sum())
    grouped["订单占比"] = grouped["订单量"] / total_orders * 100 if total_orders else 0
    grouped["金额占比"] = grouped["订单金额"] / total_revenue * 100 if total_revenue else 0
    return test_df, grouped, total_orders, total_revenue


def render_ab_test_analysis(df, context):
    section("AB 测试对比分析", "运营问题：按用户 ID 尾数分组后，两个方案的订单量和金额贡献是否有明显差异？")

    if "user_id" not in df.columns:
        st.warning("当前数据没有识别到用户 ID 字段，无法按尾数做 AB 分组。")
        return

    with st.container(border=True):
        mode = st.segmented_control("分组方式", ["奇数 vs 偶数", "自定义尾数"], default="奇数 vs 偶数")
        if mode == "奇数 vs 偶数":
            a_digits = ODD_DIGITS
            b_digits = EVEN_DIGITS
            st.caption("当前规则：A 方案 = 1、3、5、7、9；B 方案 = 0、2、4、6、8。")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                a_digits = st.multiselect("A 方案用户ID尾数", DIGITS, default=ODD_DIGITS, key="ab_custom_a_digits")
            with col_b:
                b_digits = st.multiselect("B 方案用户ID尾数", DIGITS, default=EVEN_DIGITS, key="ab_custom_b_digits")
            st.caption("把某几个尾数归到 A 或 B，用于适配不同实验规则。")

    overlap = sorted(set(a_digits) & set(b_digits))
    if overlap:
        st.warning("A 方案和 B 方案不能包含相同尾数：" + "、".join(overlap))
        return
    if not a_digits or not b_digits:
        st.warning("A 方案和 B 方案都至少需要选择 1 个用户 ID 尾数。")
        return

    test_df, summary, total_orders, total_revenue = _build_ab_summary(df, set(a_digits), set(b_digits))
    compare = summary[summary["实验组"].isin(["A 方案", "B 方案"])].copy()
    unknown = summary[summary["实验组"] == "未分组"].iloc[0]
    a_row = compare[compare["实验组"] == "A 方案"].iloc[0]
    b_row = compare[compare["实验组"] == "B 方案"].iloc[0]
    order_gap = int(a_row["订单量"] - b_row["订单量"])
    revenue_gap = float(a_row["订单金额"] - b_row["订单金额"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("A 方案订单 / 金额", f"{int(a_row['订单量']):,} 单", note=fmt_money(a_row["订单金额"]), accent="#2563eb")
    with c2:
        metric_card("B 方案订单 / 金额", f"{int(b_row['订单量']):,} 单", note=fmt_money(b_row["订单金额"]), accent="#16a34a")
    with c3:
        metric_card("订单差值 A-B", f"{order_gap:+,} 单", note=f"总订单 {total_orders:,} 单", accent="#f97316")
    with c4:
        metric_card("金额差值 A-B", fmt_money(revenue_gap), note=f"总金额 {fmt_money(total_revenue)}", accent="#7c3aed")

    if int(unknown["订单量"]) > 0:
        st.markdown(
            f'<div class="small-muted">有 {int(unknown["订单量"]):,} 单未分组，通常是用户 ID 缺失或尾数不在当前 A/B 规则内。</div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section("订单占比", "运营问题：A/B 两个方案分别贡献了多少订单？")
            fig = px.bar(compare, x="实验组", y="订单占比", text="订单量", title="A/B 订单占比")
            fig.update_traces(marker_color=["#2563eb", "#16a34a"], texttemplate="%{text:,} 单", textposition="outside")
            fig.update_layout(xaxis_title="", yaxis_title="订单占比")
            st.plotly_chart(style_chart(fig, height=340), use_container_width=True)

    with right:
        with st.container(border=True):
            section("金额占比", "运营问题：A/B 两个方案分别贡献了多少收入？")
            fig = px.bar(compare, x="实验组", y="金额占比", text="订单金额", title="A/B 金额占比")
            fig.update_traces(marker_color=["#2563eb", "#16a34a"], texttemplate="¥%{text:,.0f}", textposition="outside")
            fig.update_layout(xaxis_title="", yaxis_title="金额占比")
            st.plotly_chart(style_chart(fig, height=340), use_container_width=True)

    with st.container(border=True):
        section("AB 方案明细", "运营问题：两个方案的订单量、订单占比、订单金额和金额占比分别是多少？")
        table = summary.copy()
        table["用户ID尾数"] = table["实验组"].map(
            {
                "A 方案": "、".join(a_digits),
                "B 方案": "、".join(b_digits),
                "未分组": "缺失或不在规则内",
            }
        )
        table["订单金额"] = table["订单金额"].map(fmt_money)
        table["订单占比"] = table["订单占比"].map(fmt_percent)
        table["金额占比"] = table["金额占比"].map(fmt_percent)
        st.dataframe(
            table[["实验组", "用户ID尾数", "订单量", "订单占比", "订单金额", "金额占比", "用户数"]],
            use_container_width=True,
            hide_index=True,
        )

    with st.container(border=True):
        section("尾数分布检查", "运营问题：当前实验分流是否接近均匀，是否存在某个尾数异常集中？")
        digit_summary = (
            test_df.groupby(["用户ID尾数", "实验组"])
            .agg(订单量=("订单编号", "nunique"), 订单金额=("支付金额", "sum"))
            .reset_index()
            .sort_values("用户ID尾数")
        )
        digit_summary["用户ID尾数"] = digit_summary["用户ID尾数"].replace("", "未识别")
        digit_summary["订单金额"] = digit_summary["订单金额"].map(fmt_money)
        st.dataframe(digit_summary, use_container_width=True, hide_index=True)
