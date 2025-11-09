import streamlit as st
import functions.utils as ut
import functions.user as user
import functions.ui_components as ui
from withings.ui_components import (
    show_connection_status,
    show_data_load_interface,
    show_data_sync_interface,
    show_authentication_interface,
)

ut.init_vars()
ut.default_style()
ut.create_menu()

st.subheader("Manage Measurements")

# ----- if user selected ---------------------------------------------------
users_dict = user.load_users_dict()
if users_dict and st.session_state.user_idx is not None:
    # Get the current user
    current_user = st.session_state.user_name

    # ----- add/update measurements ---------------------------------------------------
    ui.manage_measurements()

    # ----- display measurements ---------------------------------------------------
    ut.h_spacer(2)
    ui.display_measurements()

    # ----- Withings Data Sync ----------------------
    ut.h_spacer(2)
    st.subheader("Withings Data Import")

    # Check if user is selected
    with st.container(border=True):
        current_user = st.session_state.user_name

        # Show connection status
        status = show_connection_status(current_user)

        if status["connected"]:
            # User is connected - show data fetch and sync interface
            show_data_load_interface(current_user)
            show_data_sync_interface(current_user)
        elif status["configured"]:
            # Credentials configured but user not connected
            show_authentication_interface(current_user)
        else:
            st.warning(
                "Withings API credentials not configured. Check .streamlit/secrets.toml !"
            )

# ----- no user selected ---------------------------------------------------
else:
    if not users_dict:
        st.info("No users found. Add a user below to get started.")
    else:
        st.info("Please select a user from the sidebar to edit their data.")
