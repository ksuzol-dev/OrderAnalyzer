import streamlit as st

from components.ui import section


def render_user_analysis(df, detected):
    section("用户分析", "运营问题：未来要回答新客、复购和生命周期变化，目前先预留模块入口。")
    st.markdown(
        '<div class="placeholder-box">V0.3 Foundation 只预留用户分析页面。后续版本会根据订单中的用户标识字段，增加新客数、复购率、生命周期和用户分层。</div>',
        unsafe_allow_html=True,
    )

    user_like_columns = [column for column in df.columns if any(key in str(column) for key in ["用户", "客户", "买家", "手机号", "会员"])]
    if user_like_columns:
        st.write("疑似用户字段：")
        st.dataframe({"字段名": user_like_columns}, use_container_width=True, hide_index=True)
    else:
        st.info("当前标准化数据中暂未识别到用户字段。")

    with st.expander("当前已识别订单字段"):
        st.json(detected)
