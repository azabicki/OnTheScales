import streamlit as st
import functions.utils as ut
import functions.user as user
import functions.data as data
import functions.ui_components as ui
from withings.ui_components import (
    show_connection_status,
    show_token_info,
    show_authentication_interface,
)

# init default values
ut.init_vars()
ut.default_style()
ut.create_menu()

users_dict = user.load_users_dict()

# Handle user selection from query parameters (e.g., after OAuth callback)
# This must be done AFTER create_menu() to avoid widget modification errors
if "select_user" in st.query_params:
    user_to_select = st.query_params["select_user"]
    # Find the user index and select them
    user_names = list(users_dict.keys())
    if user_names:
        for idx, user_name in enumerate(user_names):
            if user_name == user_to_select:
                st.session_state.pending_user_selection = idx
                st.query_params.clear()
                st.rerun()

# Apply pending user selection if it exists
if "pending_user_selection" in st.session_state:
    idx = st.session_state.pending_user_selection
    # Set the user index and update user settings
    st.session_state.user_idx = idx
    # Update user settings
    ut.set_user_sessionstate(what="user")
    ut.set_user_sessionstate(what="trend")
    # Load user data
    if st.session_state.user_idx is not None:
        st.session_state.db = data.load_db()
    del st.session_state.pending_user_selection
    st.rerun()

col_title, col_add = st.columns([2, 1], gap="small", vertical_alignment="bottom")
with col_title:
    st.subheader("User Management")
with col_add:
    ui.add_user()
container_feedback = st.empty()

# ----- User Management Feedback -----------------------------------------------
if st.session_state.flags["usr_del_ok"]:
    usr_del_name = st.session_state.flags["usr_del_name"]
    container_feedback.success(
        f"User **_{usr_del_name}_** deleted succesfully",
        icon=":material/done_outline:",
    )
    st.session_state.flags["usr_del_ok"] = False
    st.session_state.flags["usr_del_name"] = ""

if st.session_state.flags["usr_add_ok"]:
    usr_add_name = st.session_state.user_name
    st.session_state.flags["usr_add_ok"] = False
    container_feedback.success(
        f"User **_{usr_add_name}_** added succesfully",
        icon=":material/done_outline:",
    )

if st.session_state.flags["usr_add_exists"]:
    usr_add_exists_name = st.session_state.flags["usr_add_exists_name"]
    container_feedback.error(
        f"User name **_{usr_add_exists_name}_** already exists",
        icon=":material/warning:",
    )
    st.session_state.flags["usr_add_exists"] = False
    st.session_state.flags["usr_add_exists_name"] = ""

# ----- if user selected ---------------------------------------------------
if users_dict and st.session_state.user_idx is not None:
    # Get the current user
    current_user = st.session_state.user_name

    # ----- update users ---------------------------------------------------
    ui.edit_user(current_user)

    # ----- Withings Integration -------------------------------------------
    ut.h_spacer(2)
    st.markdown("#### Withings Integration")
    with st.container(border=True):
        # Show connection status
        withings_status = show_connection_status(current_user)

        if withings_status["connected"]:
            show_token_info(current_user)
        elif withings_status["configured"]:
            show_authentication_interface(current_user)
        else:
            st.warning(
                "Withings API credentials not configured. Check .streamlit/secrets.toml !",
                icon=":material/warning:",
            )

    # ----- danger zone ----------------------------------------------------
    ut.h_spacer(2)
    ui.danger_zone(current_user)

# ----- no user selected ---------------------------------------------------
else:
    if not users_dict:
        st.info("No users found. Add a user below to get started.")
    else:
        st.info("Please select a user from the sidebar to edit their data.")
