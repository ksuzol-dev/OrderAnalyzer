import streamlit as st

from components.ui import metric_card, section


def render_data_check(raw_df, df, detected):
    section("数据检查", "运营问题：本次上传的数据是否足够完整，可以支撑看板判断？")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("原始行数", f"{len(raw_df):,}")
    with c2:
        metric_card("支付成功行数", f"{len(df):,}")
    with c3:
        metric_card("支付成功订单数", f"{df['订单编号'].nunique():,}")
    with c4:
        metric_card("识别字段数", f"{sum(value is not None for value in detected.values())}/{len(detected)}")

    section("字段识别")
    st.json(detected)

    section("标准字段预览")
    standard_columns = [
        "订单编号",
        "SKU",
        "支付金额",
        "支付完成时间",
        "来源平台",
        "开通方式",
        "VIP ID",
        "VIP 名称",
        "VIP 类型",
        "source_platform",
        "pay_type",
        "vip_id",
        "vip_name",
        "vip_type",
    ]
    available_columns = [column for column in standard_columns if column in df.columns]
    st.dataframe(df[available_columns].head(50), use_container_width=True, hide_index=True)

    section("原始字段")
    st.dataframe({"字段名": list(raw_df.columns)}, use_container_width=True, hide_index=True)

    section("原始数据样例")
    st.dataframe(raw_df.head(50), use_container_width=True)
