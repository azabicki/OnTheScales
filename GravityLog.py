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


# ----- trend figure -----
ut.h_spacer(2)
st.subheader("trend & predict")

# draw trend figure and get trend
fig_trend, trend = fgs.trend()

with st.container(border=True):
    # show current change rate of weight
    c1,c2,c3 = st.columns([1, 1, 1])
    c1.markdown("**weight changes:**")
    c2.markdown(f"_{round(trend*10**9*60*60*24*7, 2)} kg/week_")
    c3.markdown(f"_{round(trend*10**9*60*60*24*30, 2)} kg/month_")

    # plot trend
    st.plotly_chart(fig_trend, use_container_width=True, config = {'displayModeBar': False}, key="fig_trend")

    with st.popover("trend settings"):
        # radio button to select how to define starting point
        st.radio(
            "trend based on",
            ["start date", "date range"],
            key="trend_how",
        )

        # select _start date_
        if st.session_state.trend_how == "start date":
            st.date_input(
                "select 'start date'",
                format="YYYY-MM-DD",
                key="trend_start",
            )

        # select _date range_
        elif st.session_state.trend_how == "date range":
            weeks = np.array([4, 8, 12, 16, 20, 24], dtype=np.int64)
            st.selectbox(
                "select 'range'",
                weeks,
                format_func=lambda x: str(x) + " weeks = " + str(x // 4) + " months",
                key="trend_range",
            )

