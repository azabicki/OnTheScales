"""
Reusable UI components for Withings integration.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
import time
from .withings import withings_client


def _get_column_config() -> Dict:
    """
    Generate column configuration dynamically based on WithingsConfig.MEASURE_TYPES.
    """
    config = {
        "date": st.column_config.DateColumn(
            "Date",
            help="Measurement date",
            format="DD.MM.YY",
            disabled=True,
            pinned=True,
        ),
        "synced": st.column_config.CheckboxColumn(
            "Sync?",
            help="Check to sync this measurement with _**OnTheScales**_",
            default=False,
            pinned=True,
        ),
    }

    # Add columns for each measure type
    for _, measure_info in withings_client.config.MEASURE_TYPES.items():
        name = measure_info["name"]
        var_name = name.lower().replace(" ", "_")
        unit = measure_info["unit"] if measure_info["unit"] != "%" else "%%"
        decimals = measure_info["decimals"]

        # Format string based on decimals
        if decimals == 0:
            format_str = f"%d {unit}"
        else:
            format_str = f"%.{decimals}f {unit}"

        config[var_name] = st.column_config.NumberColumn(
            label=name,
            help=f"{name} in {unit}",
            format=format_str,
            disabled=True,
        )

    return config


def show_connection_status(user_name: str) -> Dict:
    """
    Show Withings connection status for a user.

    Args:
        user_name: Name of the user

    Returns:
        Connection status dictionary
    """
    status = withings_client.get_connection_status(user_name)

    if not status["configured"]:
        st.warning("Withings API credentials not configured", icon=":material/warning:")
        st.caption("Please check your .streamlit/secrets.toml file")
        return status

    if not status["connected"]:
        st.info(
            f"{user_name} not connected to Withings",
            icon=":material/info:",
        )
        return status

    # User is connected - show status
    token_status = status["token_status"]

    if token_status["valid"]:
        st.info(f"{user_name} connected to Withings", icon=":material/done_outline:")
    else:
        st.error(f"{user_name}'s Withings token expired", icon=":material/error:")

    return status


def show_token_info(user_name: str) -> None:
    """
    Show detailed token information in an expander.

    Args:
        user_name: Name of the user
    """
    status = withings_client.get_connection_status(user_name)
    token_status = status["token_status"]
    token_data = status.get("token_data")

    col_info, col_button = st.columns(2, vertical_alignment="center", gap="small")
    with col_info:
        # Status
        status_text = "Valid" if token_status["valid"] else "Invalid / Expired"
        st.write(f"**Token Status:** {status_text}")

        # Expires in/at (if token data available)
        if token_data and "expires_at" in token_data:
            expires_at = token_data["expires_at"]
            expires_date = datetime.fromtimestamp(expires_at)
            current_time = datetime.now()

            # Calculate time until expiry
            time_diff = expires_date - current_time
            if time_diff.total_seconds() > 0:
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                seconds = int(time_diff.total_seconds() % 60)
                expires_in = f"{hours}h {minutes}m {seconds}s"
                st.write(f"**Expires in:** {expires_in}")
            else:
                st.write("**Expires in:** Expired")

            st.write(f"**Expires at:** {expires_date.strftime('%d.%m.%y %H:%M:%S')}")

    with col_button:
        # Manual refresh button
        if st.button(
            "refresh Token now",
            help="Manually refresh the Withings access token (wait 10+ seconds between attempts)",
            type="secondary",
            use_container_width=True,
            icon=":material/refresh:",
        ):
            result = withings_client.refresh_token(
                user_name=user_name, force_refresh=True
            )
            if result["result"]:
                st.rerun()
            else:
                # Provide specific error guidance
                st.error(
                    result["message"],
                    icon=":material/error:",
                )

        show_disconnect_button(user_name)


def show_disconnect_button(user_name: str) -> None:
    """
    Show disconnect button for a user.

    Args:
        user_name: Name of the user
    """
    if st.button(
        "Disconnect from Withings",
        type="secondary",
        use_container_width=True,
        icon=":material/power_off:",
    ):
        if withings_client.disconnect_user(user_name):
            st.success("Disconnected from Withings")
            st.rerun()
        else:
            st.error("Failed to disconnect from Withings")


def show_authentication_interface(user_name: str) -> None:
    """
    Show authentication interface for connecting to Withings.

    Args:
        user_name: Name of the user
    """
    try:
        auth_url = withings_client.get_authorization_url(user_name)

        st.link_button(
            "connect to Withings",
            auth_url,
            help="Click to authenticate with Withings",
            icon=":material/cable:",
        )

        # Handle OAuth callback
        query_params = st.query_params
        if "code" in query_params and "state" in query_params:
            state = query_params["state"]
            if state.startswith("withings_auth_"):
                auth_user = state.replace("withings_auth_", "")
                if auth_user == user_name:
                    code = query_params["code"]

                    with st.spinner("Authenticating with Withings..."):
                        if withings_client.process_authorization_code(code, user_name):
                            st.success(
                                f"Successfully connected {user_name} to Withings!"
                            )
                            # Clear query params and add user selection
                            st.query_params.clear()
                            st.query_params["select_user"] = user_name
                            st.rerun()
                        else:
                            st.error(
                                "Failed to authenticate with Withings. Please try again."
                            )

    except Exception as e:
        st.error(f"Error setting up authentication: {str(e)}")


def show_data_load_interface(user_name: str) -> Optional[str]:
    """
    Show data fetching interface.

    Args:
        user_name: Name of the user

    Returns:
        Session state key for fetched data or None
    """
    with st.form(key="withings_data_load_form", border=False):
        # Date range selection
        col_start, col_end, col_fetch = st.columns(
            [1, 1, 2], gap="small", vertical_alignment="bottom"
        )
        with col_start:
            start_date = st.date_input(
                "Start Date:",
                value=datetime.now().date()
                - timedelta(days=withings_client.config.DEFAULT_DATE_RANGE_DAYS),
                format="DD.MM.YYYY",
            )
        with col_end:
            end_date = st.date_input(
                "End Date:", value=datetime.now().date(), format="DD.MM.YYYY"
            )
        with col_fetch:
            # Fetch data button
            if st.form_submit_button(
                "load Withings data",
                type="secondary",
                use_container_width=True,
                icon=":material/download:",
            ):
                with st.spinner("Loading data from Withings..."):
                    withings_df = withings_client.load_withings_data(
                        user_name,
                        datetime.combine(start_date, datetime.min.time()),
                        datetime.combine(end_date, datetime.max.time()),
                    )
                    st.session_state[f"withings_data_{user_name}"] = withings_df

                    # Clear previous selection states when loading new data
                    selection_key = f"withings_selection_{user_name}"
                    if selection_key in st.session_state:
                        del st.session_state[selection_key]

    try:
        loaded_df = st.session_state[f"withings_data_{user_name}"]
        if loaded_df is not None and not loaded_df.empty:
            col_txt, col_feedback = st.columns(
                2, gap="small", vertical_alignment="bottom"
            )
            with col_txt:
                st.markdown("**Select measurements to import:**")
            with col_feedback:
                st.success(f"Loaded {len(loaded_df)} measurements!")
        elif loaded_df is not None and loaded_df.empty:
            st.info("No measurements found in the selected date range.")
        else:
            st.error("Failed to load data from Withings. Please check your connection.")
    except Exception:
        st.info(
            "Load Withings data first to see import options.", icon=":material/info:"
        )

    data_key = f"withings_data_{user_name}"
    return data_key if data_key in st.session_state else None


def show_data_sync_interface(user_name: str) -> None:
    """
    Show data import interface.

    Args:
        user_name: Name of the user
    """
    data_key = f"withings_data_{user_name}"
    unknown_key = f"withings_unknown_{user_name}"
    if data_key not in st.session_state or st.session_state[data_key].empty:
        return

    # Prepare data for display
    display_df = withings_client.prepare_data_for_display(
        st.session_state[f"withings_data_{user_name}"], user_name
    )

    # Session state keys
    selection_key = f"withings_selection_{user_name}"

    # Apply selection state to the dataframe
    if selection_key in st.session_state:
        for idx, row in display_df.iterrows():
            if f"row_{idx}" in st.session_state[selection_key]:
                display_df.at[idx, "synced"] = st.session_state[selection_key][
                    f"row_{idx}"
                ]

    # Store a copy to detect actual manual changes
    display_df_copy = display_df.copy()

    # Create editable dataframe with checkboxes
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        column_order=(
            "date",
            "synced",
            "weight",
            "fat",
            "water",
            "muscle",
            "fat_free",
            "bone",
            "visceral_fat",
            "metabolic_age",
        ),
        hide_index=True,
        column_config=_get_column_config(),
        key="withings_data_editor",
    )

    # Detect manual changes in the data editor
    manual_changes_detected = False
    if not display_df_copy.equals(edited_df):
        # Check if this is truly a manual change (not just from our session state)
        for idx in edited_df.index:
            edited_value = edited_df.loc[idx, "synced"]
            original_value = display_df_copy.loc[idx, "synced"]
            if edited_value != original_value:
                # This is a real manual change
                manual_changes_detected = True
                if selection_key not in st.session_state:
                    st.session_state[selection_key] = {}
                st.session_state[selection_key][f"row_{idx}"] = edited_value

        # If manual changes were detected, rerun to sync state
        if manual_changes_detected:
            st.rerun()

    # Selection controls using buttons
    col_all, col_none, col_reset, col_unknown = st.columns(
        [1, 1, 1, 2], gap="small", vertical_alignment="center"
    )
    with col_all:
        if st.button(
            "All",
            type="secondary",
            use_container_width=True,
            icon=":material/check_box:",
        ):
            # Select all rows
            if selection_key not in st.session_state:
                st.session_state[selection_key] = {}
            for idx in display_df.index:
                st.session_state[selection_key][f"row_{idx}"] = True
            st.rerun()

    with col_none:
        if st.button(
            "None",
            type="secondary",
            use_container_width=True,
            icon=":material/check_box_outline_blank:",
        ):
            # Deselect all rows
            if selection_key not in st.session_state:
                st.session_state[selection_key] = {}
            for idx in display_df.index:
                st.session_state[selection_key][f"row_{idx}"] = False
            st.rerun()

    with col_reset:
        if st.button(
            "Reset",
            type="secondary",
            use_container_width=True,
            icon=":material/refresh:",
        ):
            # Reset to actual import status
            if selection_key in st.session_state:
                del st.session_state[selection_key]
            st.rerun()

    with col_unknown:
        # col_unknown, col_button_import = st.columns([2, 3], gap="small")
        # with col_unknown:
        st.toggle(
            "import unknown",
            key=unknown_key,
            value=True,
            help="Import unknown measurements",
        )

    # with col_button_sync:
    sync_clicked = st.button(
        "sync selected entries with _**BouskiOnTheScales**_",
        type="primary",
        use_container_width=True,
        icon=":material/sync:",
    )

    # Sync logic
    if sync_clicked:
        all_available_data = st.session_state[data_key]
        sync_unknown = st.session_state[unknown_key]
        sync_index = edited_df[edited_df["synced"]]

        # Get selected data (checked rows)
        if not sync_index.empty:
            selected_dates = sync_index["date"].dt.date
            selected_data = all_available_data[
                all_available_data["date"].dt.date.isin(selected_dates)
            ]
        else:
            selected_data = pd.DataFrame()

        # Use sync function to handle both import and deletion
        # Pass the entire loaded dataframe to ensure only visible entries are handled
        sync_result = withings_client.sync_data(
            user_name, selected_data, all_available_data, sync_unknown
        )

        # Show appropriate feedback messages
        synced_count = sync_result["synced"]
        deleted_count = sync_result["deleted"]
        new_measure_types = sync_result["new_measure_types"]

        messages = []
        if synced_count > 0:
            messages.append(f"Synced {synced_count} new measurements")
        if deleted_count > 0:
            messages.append(f"Deleted {deleted_count} deselected measurements")
        if new_measure_types:
            messages.append(f"Added new measure types: {', '.join(new_measure_types)}")

        if messages:
            # Clear selection state after successful sync
            selection_key = f"withings_selection_{user_name}"
            if selection_key in st.session_state:
                del st.session_state[selection_key]

            st.success(" | ".join(messages))
            time.sleep(2)
            st.rerun()
        elif synced_count == 0 and deleted_count == 0:
            st.info("No changes made - all selected measurements were already synced.")
            time.sleep(2)
            st.rerun()
        else:
            st.warning("Please select at least one measurement to sync.")
