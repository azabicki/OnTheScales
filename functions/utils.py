import os
import streamlit as st
import functions.user as user
import functions.data as data


def init_vars() -> None:
    """
    Initializes session_state variables on first run.

    Args:
        None

    Returns:
        None
    """

    # a collection of flags in a dict
    if "flags" not in st.session_state:
        st.session_state.flags = {
            "data_add": False,
            "data_upd": False,
            "data_del": False,
            "usr_add_ok": False,
            "usr_add_exists": False,
            "usr_update_ok": False,
            "usr_del_ok": False,
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
        set_user_sessionstate()

    # load data_db for current user / or create empty db
    if "db" not in st.session_state:
        if st.session_state.user_idx is not None:
            st.session_state.db = data.load_db()
        else:
            st.session_state.db = data.create_df()

    if "fig_main_style" not in st.session_state:
        st.session_state.fig_main_style = "lines"
        st.session_state.fig_body_comp = "%"

    if "debug" not in st.session_state:
        st.session_state.debug = False


def set_user_sessionstate() -> None:
    """
    Sets initial user session_state variables

    Args:
        None

    Returns:
        None
    """

    if st.session_state.user_idx is not None:
        # user data
        st.session_state.user_name = st.session_state.user_db.loc[st.session_state.user_idx, "name"]
        st.session_state.user_cm = st.session_state.user_db.loc[st.session_state.user_idx, "height"]
        st.session_state.user_kg = st.session_state.user_db.loc[st.session_state.user_idx, "target"]

        # trend settings
        st.session_state.trend_how = st.session_state.user_db.loc[st.session_state.user_idx, "trend_how"]
        st.session_state.trend_start = st.session_state.user_db.loc[st.session_state.user_idx, "trend_start"]
        st.session_state.trend_range = st.session_state.user_db.loc[st.session_state.user_idx, "trend_range"]

    else:
        # when no user in user_db
        st.session_state.user_name = "..."
        st.session_state.user_cm = None
        st.session_state.user_kg = None
        st.session_state.trend_how = "..."
        st.session_state.trend_start = "..."
        st.session_state.trend_range = "..."


def create_menu() -> None:
    """
    creates the left-side menu

    Args:
        None

    Returns:
        None
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
        args=('sidebar', None),
        placeholder="add new user" if len(st.session_state.user_db) == 0 else "select user"
    )
    st.sidebar.divider()

    # pages
    st.sidebar.page_link("GravityLog.py", label="📉 Graphs")
    st.sidebar.page_link(os.path.join("pages", "measurements.py"), label="📓 Measurements")
    st.sidebar.page_link(os.path.join("pages", "manage_users.py"), label="👥 Manage Users")
    st.sidebar.divider()


def default_style() -> None:
    """
    Defines defaults styling and layout settings.

    Args:
        None

    Returns:
        None
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


def h_spacer(height:int=0, sb:bool=False) -> None:
    """
    Adds empty lines.

    Args:
        height (int): Number of lines to add, defaults to 0
        sb (bool): If True, adds lines to sidebar. If False, adds to main area, defaults to False

    Returns:
        None
    """

    for _ in range(height):
        if sb:
            st.sidebar.write("\n")
        else:
            st.write("\n")


def switch_page(page_name: str):
    """
    Switch page programmatically in a multipage app

    Args:
        page_name (str): Target page name
    """
    from streamlit.runtime.scriptrunner import RerunData, RerunException
    from streamlit.source_util import get_pages

    def standardize_name(name: str) -> str:
        return name.lower().replace("_", " ")

    page_name = standardize_name(page_name)
    pages = get_pages("GravityLog.py")  # OR whatever your main page is called

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )

    page_names = [standardize_name(config["page_name"]) for config in pages.values()]
    raise ValueError(f"Could not find page {page_name}. Must be one of {page_names}")
