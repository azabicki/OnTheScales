import streamlit as st
import functions.utils as ut
import functions.user as user
import functions.figures as fgs

# init default values
ut.init_vars()
ut.default_style()
ut.create_menu()

# ----- current user -----
col_title = st.columns(2, gap="small", vertical_alignment="bottom")
# name
with col_title[0]:
    col_title[0].header(st.session_state.user_name)
# shortcut to go to measurements page
with col_title[1]:
    goto_measurement = st.button("New Measurement", icon=":material/add_circle:")
    if goto_measurement:
        ut.switch_page("measurements")


# ----- main figure -----
# create fragment 4 main_figure
@st.fragment()
def fragment_main_figure():
    with st.container(border=True):
        # create figure
        fig_chrono = fgs.main()

        # draw and show figure
        if fig_chrono is None:
            st.markdown("_No measurements stored yet._")
        else:
            st.plotly_chart(
                fig_chrono,
                use_container_width=True,
                config={"displayModeBar": False},
                key="fig_chrono",
            )

        # add selectbox for figure styling
        st.divider()
        st.segmented_control(
            "data style:", options=["lines", "markers", "both"], key="fig_main_style"
        )


# run main figure fragment
fragment_main_figure()

# ----- trend figure -----
ut.h_spacer(1)
st.subheader("trend & predict")

# create trend figure and get trend
fig_trend, trend = fgs.trend()

with st.container(border=True):
    if fig_trend is None:
        st.markdown("_No, or not enough, measurements stored yet._")
    else:
        # show current change rate of weight
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.markdown(
            "**$\Delta$kg {txt}:**".format(
                txt=(
                    "since {date}".format(
                        date=st.session_state.trend_start.date().strftime("%d.%m.%Y")
                    )
                    if st.session_state.trend_how == "start date"
                    else "in last {weeks} weeks".format(
                        weeks=st.session_state.trend_range
                    )
                )
            )
        )
        c2.markdown(f"_{round(trend*10**9*60*60*24*7, 2)} kg/week_")
        c3.markdown(f"_{round(trend*10**9*60*60*24*30, 2)} kg/month_")

        # draw and show trend
        st.plotly_chart(
            fig_trend,
            use_container_width=True,
            config={"displayModeBar": False},
            key="fig_trend",
        )

    # add columns for figure options
    st.divider()
    col_trend = st.columns(2, gap="small")

    # radio button to select how to define starting point
    with col_trend[0]:
        st.segmented_control(
            "trend based on:",
            options=["start date", "date range"],
            key="trend_how",
            on_change=user.update_trend,
        )

    # select _start date_
    with col_trend[1]:
        if st.session_state.trend_how == "start date":
            st.date_input(
                "select 'start date':",
                format="DD.MM.YYYY",
                key="trend_start",
                on_change=user.update_trend,
            )

        # select _date range_
        if st.session_state.trend_how == "date range":
            st.number_input(
                "select 'range' - in weeks:",
                format="%d",
                min_value=1,
                max_value=100,
                step=1,
                key="trend_range",
                on_change=user.update_trend,
            )

# ----- body composition figure -----
ut.h_spacer(1)
st.subheader("body composition")

with st.container(border=True):
    # draw figure
    fig_body_comp = fgs.body_comp()

    if fig_body_comp is None:
        st.markdown("_No measurements stored yet._")
    else:
        st.plotly_chart(
            fig_body_comp,
            use_container_width=True,
            config={"displayModeBar": False},
            key="fig_body_comp",
        )

    # add columns for figure options
    st.divider()
    col_body_comp = st.columns([2, 3, 2], gap="small")

    # add selectbox for body composition
    col_body_comp[0].segmented_control(
        "body composition:",
        options=["%", "kg"],
        format_func=lambda x: "in " + x,
        key="fig_body_comp_type",
    )

    # add selectbox for figure styling
    col_body_comp[1].segmented_control(
        "data style:",
        options=["lines", "markers", "both"],
        key="fig_body_comp_style",
    )

    # add selectbox for adding weight
    col_body_comp[2].segmented_control(
        "showing:",
        options=["weight & target"],
        key="fig_body_comp_weight",
    )
