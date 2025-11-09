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
            "usr_add_exists_name": "",
            "usr_update_ok": False,
            "usr_del_ok": False,
            "usr_del_name": "",
        }

    # load user database
    if "user_db" not in st.session_state:
        st.session_state.user_db = user.load_db()  # Keep DataFrame for compatibility
        users_dict = user.load_users_dict()
        if len(users_dict) == 0:
            st.session_state.user_idx = None
        else:
            st.session_state.user_idx = 0

    # get user data from user_db
    if "user_name" not in st.session_state:
        set_user_sessionstate("user")

    # get user data from user_db
    if "user_trend_how" not in st.session_state:
        set_user_sessionstate("trend")

    # load data_db for current user / or create empty db
    if "db" not in st.session_state:
        if st.session_state.user_idx is not None:
            st.session_state.db = data.load_db()
        else:
            st.session_state.db = data.create_df()

    if "fig_main_style" not in st.session_state:
        st.session_state.fig_main_style = "lines"
        st.session_state.fig_main_smoothing = None
        st.session_state.fig_body_comp_type = "%"
        st.session_state.fig_body_comp_weight = None
        st.session_state.fig_body_comp_style = "lines"


def set_user_sessionstate(what: str) -> None:
    """
    Sets session state variables related to the user or trend settings.

    Args:
        what (str): String indicating which variables to set ("user" or "trend")

    Returns:
        None
    """

    match what:
        case "user":
            # Get users dictionary for efficient access
            users_dict = user.load_users_dict()
            user_names = list(users_dict.keys())

            if (
                st.session_state.user_idx is not None
                and st.session_state.user_idx < len(user_names)
            ):
                # user data
                current_user = user_names[st.session_state.user_idx]
                user_data = users_dict[current_user]
                st.session_state.user_name = user_data["name"]
            else:
                # when no user in user_db
                st.session_state.user_name = "..."

        case "trend":
            # Get users dictionary for efficient access
            users_dict = user.load_users_dict()
            user_names = list(users_dict.keys())

            if (
                st.session_state.user_idx is not None
                and st.session_state.user_idx < len(user_names)
            ):
                # trend settings
                current_user = user_names[st.session_state.user_idx]
                user_data = users_dict[current_user]
                st.session_state.trend_how = user_data["trend_how"]
                st.session_state.trend_start = user_data["trend_start"]
                st.session_state.trend_range = user_data["trend_range"]
            else:
                # when no user in user_db
                st.session_state.trend_how = "date range"
                st.session_state.trend_start = None
                st.session_state.trend_range = 8


def create_menu() -> None:
    """
    creates the left-side menu

    Args:
        None

    Returns:
        None
    """

    # title
    st.sidebar.markdown("# Bouski<br>On<br>The<br>Scales", unsafe_allow_html=True)
    st.sidebar.divider()

    # user selectbox
    users_dict = user.load_users_dict()
    user_names = list(users_dict.keys())
    usr_idx = list(range(len(user_names)))
    usr_name = user_names

    st.sidebar.selectbox(
        "select user:",
        options=usr_idx,
        format_func=lambda i: usr_name[i],
        index=st.session_state.user_idx,
        key="sb_user",
        on_change=user.select_user,
        args=("sidebar",),
        placeholder=("add new user" if len(user_names) == 0 else "select user"),
    )
    st.sidebar.divider()

    # pages
    st.sidebar.page_link("OnTheScales.py", label=":material/trending_down: Graphs")
    st.sidebar.page_link(
        os.path.join("pages", "measurements.py"), label=":material/notes: Measurements"
    )
    st.sidebar.page_link(
        os.path.join("pages", "manage_users.py"),
        label=":material/groups: Manage User/s",
    )
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


def h_spacer(height: int = 0, sb: bool = False) -> None:
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
    pages = get_pages("OnTheScales.py")  # OR whatever your main page is called

    for page_hash, config in pages.items():
        if standardize_name(config.get("page_name", "")) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )

    page_names = [
        standardize_name(config.get("page_name", "")) for config in pages.values()
    ]
    raise ValueError(f"Could not find page {page_name}. Must be one of {page_names}")
