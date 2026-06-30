import streamlit as st

from components.ui import metric_card, section


def render_user_analysis(df, detected):
    user_like_columns = [column for column in df.columns if any(key in str(column) for key in ["用户", "客户", "买家", "手机号", "会员"])]
    vip_id_count = df["vip_id"].replace("", None).dropna().nunique() if "vip_id" in df.columns else 0
    vip_type_count = df["vip_type"].replace("", None).dropna().nunique() if "vip_type" in df.columns else 0

    section("用户分析", "运营问题：未来要回答新客、复购和生命周期变化，目前先预留模块入口。")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("疑似用户字段", f"{len(user_like_columns):,} 个", note="从字段名推断", accent="#2563eb")
    with c2:
        metric_card("VIP ID 数量", f"{vip_id_count:,}", note="标准字段 vip_id", accent="#16a34a")
    with c3:
        metric_card("VIP 类型数量", f"{vip_type_count:,}", note="标准字段 vip_type", accent="#7c3aed")

    st.markdown(
        '<div class="placeholder-box">V0.3.2 继续保留用户分析入口。后续版本会根据 VIP ID、会员 ID、手机号或买家 ID，增加新客数、复购率、生命周期和用户分层。</div>',
        unsafe_allow_html=True,
    )

    if user_like_columns:
        with st.container(border=True):
            section("疑似用户字段")
            st.dataframe({"字段名": user_like_columns}, use_container_width=True, hide_index=True)
    else:
        st.info("当前标准化数据中暂未识别到用户字段。")

    with st.expander("当前已识别订单字段"):
        st.json(detected)
