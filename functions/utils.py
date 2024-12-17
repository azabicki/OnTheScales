import os
import streamlit as st
import functions.user as user
import functions.data as data


def init_vars() -> None:
    """
        initializes session_state variables on first run
    """

    if "flags" not in st.session_state:
        st.session_state.flags = {
            "add": False,
            "add_new": False,
            "del": False,
            "usr_add_ok": False,
            "usr_add_exists": False,
        }

    # load user database
    if "user_db" not in st.session_state:
        st.session_state.user_db = user.load_db()
        if st.session_state.user_db.shape[0] == 0:
            st.session_state.user_idx = None
        else:
            st.session_state.user_idx = 0


    # get user data from user_db
    if "user_name" not in st.session_state:
        if st.session_state.user_idx is not None:
            st.session_state.user_name = st.session_state.user_db.loc[st.session_state.user_idx, "name"]
            st.session_state.user_cm = st.session_state.user_db.loc[st.session_state.user_idx, "height"]
            st.session_state.user_kg = st.session_state.user_db.loc[st.session_state.user_idx, "target"]
        else:
            st.session_state.user_name = ""
            st.session_state.user_cm = None
            st.session_state.user_kg = None

    # get user's trend settings from user_db
    if "trend_how" not in st.session_state:
        if st.session_state.user_idx is not None:
            st.session_state.trend_how = st.session_state.user_db.loc[st.session_state.user_idx, "trend_how"]
            st.session_state.trend_start = st.session_state.user_db.loc[st.session_state.user_idx, "trend_start"]
            st.session_state.trend_range = st.session_state.user_db.loc[st.session_state.user_idx, "trend_range"]
        else:
            st.session_state.trend_how = ""
            st.session_state.trend_start = ""
            st.session_state.trend_range = ""

        print("init how: ", st.session_state.trend_how)
        print("init start: ", st.session_state.trend_start)
        print("          : ", type(st.session_state.trend_start))
        print("init range: ", st.session_state.trend_range)
        print("          : ", type(st.session_state.trend_range))

    # load data_db for current user / or create empty db
    if "db" not in st.session_state:
        if st.session_state.user_idx is not None:
            st.session_state.db = data.load()
        else:
            st.session_state.db = data.create_df()

    # if "graph_main_style" not in st.session_state:
    #     st.session_state.graph_main_style = "lines"

    # if "bc_in_kg" not in st.session_state:
    #     st.session_state.bc_in_kg = "%"


def create_menu() -> None:
    """
        creates the left-side  menu
    """
    # title
    st.sidebar.title("GravityLog")
    st.sidebar.divider()

    # user selectbox
    usr_idx = [i for i, _ in st.session_state.user_db.iterrows()]
    usr_name = [r["name"] for i, r in st.session_state.user_db.iterrows()]

    st.sidebar.selectbox(
        "select user:",
        options=usr_idx,
        format_func=lambda i: usr_name[i],
        index=st.session_state.user_idx,
        key="sb_user",
        on_change=user.select_user,
        placeholder="add new user"
    )
    st.sidebar.divider()

    # pages
    st.sidebar.page_link("GravityLog.py", label="📉 Graphs")
    st.sidebar.page_link(os.path.join("pages", "measurements.py"), label="📓 Measurements")
    st.sidebar.page_link(os.path.join("pages", "manage_users.py"), label="👥 Manage Users")
    st.sidebar.divider()


def default_style() -> None:
    """
        defines defaults styling and layout settings
    """
    css = """
    <style>
        [data-testid="stSidebar"]{
            min-width: 220px;
            max-width: 220px;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def h_spacer(height=0, sb=False) -> None:
    """
        inserts a horizontal space

        height: number of lines
        sb: if true, inserts a line in the sidebar
    """
    for _ in range(height):
        if sb:
            st.sidebar.write("\n")
        else:
            st.write("\n")
