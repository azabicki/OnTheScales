import streamlit as st
import functions.utils as ut
import functions.user as user
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
    c1,c2,c3 = st.columns([3, 2, 2])
    c1.markdown("**$\Delta$kg {txt}:**"
        .format(
            txt="since {date}".format(date=st.session_state.trend_start.date().strftime("%d.%m.%Y"))
            if st.session_state.trend_how == "start date"
            else f"in last {st.session_state.trend_range} weeks"
    ))
    c2.markdown(f"_{round(trend*10**9*60*60*24*7, 2)} kg/week_")
    c3.markdown(f"_{round(trend*10**9*60*60*24*30, 2)} kg/month_")

    # plot trend
    st.plotly_chart(fig_trend, use_container_width=True, config = {'displayModeBar': False}, key="fig_trend")

    with st.popover("🛠️ trend options"):
        col_trend = st.columns(2, gap="small")
        with col_trend[0]:
            # radio button to select how to define starting point
            st.radio(
                "trend based on",
                ["start date", "date range"],
                key="trend_how",
                on_change=user.update_trend
            )

        # select _start date_
        with col_trend[1]:
            if st.session_state.trend_how == "start date":
                st.date_input(
                    "select 'start date'",
                    format="DD.MM.YYYY",
                    key="trend_start",
                    disabled=False if st.session_state.trend_how == "start date" else True,
                    on_change=user.update_trend
                )

            # select _date range_
            if st.session_state.trend_how == "date range":
                st.selectbox(
                    "select 'range'",
                    [4, 8, 12, 16, 20, 24],
                    format_func=lambda x: str(x) + " weeks",
                    key="trend_range",
                    disabled=False if st.session_state.trend_how == "date range" else True,
                    on_change=user.update_trend
                )

