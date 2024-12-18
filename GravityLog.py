import streamlit as st
import numpy as np
import functions.utils as ut
import functions.figures as fgs

# init default values
ut.init_vars()
ut.default_style()
ut.create_menu()

# name of current user
st.title(st.session_state.user_name)

# shortcut to go to measurements page
goto_measurement = st.button("New Measurement")
if goto_measurement:
    ut.switch_page("measurements")

# ----- main figure -----
with st.container(border=True):
    # draw figure
    fig_chrono = fgs.main()
    st.plotly_chart(fig_chrono, use_container_width=True, config = {'displayModeBar': False}, key="fig_chrono")

    # add selectbox for figure styling
    st.selectbox(
        "style:", ["lines", "markers", "both"], index=0, key="fig_main_style",
    )

