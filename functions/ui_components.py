import time
import streamlit as st
import functions.user as user
import functions.utils as ut
import functions.data as data


# ----- Manage User/s -------------------------------------------------------
def add_user() -> None:
    @st.dialog("Add new user")
    def add_user(item):
        st.markdown("Fill in the name, height and target weight and press [enter].")
        # name
        name = st.text_input(
            "Name:",
            placeholder="...",
            max_chars=50,
            key="new_usr_name",
        )

        col_hgt, col_trgt = st.columns([1, 1], gap="medium")

        # height
        with col_hgt:
            height = st.slider(
                "Height:",
                min_value=0,
                max_value=250,
                step=1,
                value=180,
                format="%d cm",
                key="new_usr_height",
            )

        # target weight
        with col_trgt:
            target = st.slider(
                "Target Weight:",
                min_value=0,
                max_value=200,
                step=1,
                value=80,
                format="%d kg",
                key="new_usr_target",
            )

        col_button, col_feedback = st.columns(
            [1, 1], gap="small", vertical_alignment="center"
        )

        with col_button:
            # submit button
            submitted_add = st.button(
                "add new user",
                disabled=True if st.session_state.new_usr_name == "" else False,
                on_click=user.add_user,
                use_container_width=True,
                icon=":material/person_add:",
                args=(name, height, target),
            )

            if submitted_add:
                st.rerun()

    st.button(
        "Add new user",
        icon=":material/add_circle:",
        on_click=add_user,
        args=(None,),
        type="primary",
        use_container_width=True,
    )


def edit_user(current_user: str) -> None:
    users_dict = user.load_users_dict()
    current_user_dict = users_dict[current_user]

    with st.container(border=True):
        # User Data section
        with st.container(border=False):
            st.markdown("##### User Data")
            with st.form(
                "edit_user_form",
                clear_on_submit=False,
                border=False,
            ):
                col_height, col_target = st.columns([1, 1], gap="medium")

                # Height field
                with col_height:
                    st.slider(
                        "Height:",
                        min_value=0,
                        max_value=250,
                        value=current_user_dict["height"],
                        step=1,
                        format="%d cm",
                        key="edit_user_height",
                    )

                # Target weight field
                with col_target:
                    st.slider(
                        "Target Weight:",
                        min_value=0,
                        max_value=200,
                        value=current_user_dict["target"],
                        step=1,
                        format="%d kg",
                        key="edit_user_target",
                    )

                # Measurement Types section
                ut.h_spacer(2)
                st.markdown("##### Measurement Types")
                current_measure_types = current_user_dict.get("measure_types", [])

                # Display measure types for editing
                for i, measure_type in enumerate(current_measure_types):
                    col_name, col_unit, col_decimals, col_actions = st.columns(
                        [2, 1, 1, 1],
                        gap="small",
                        vertical_alignment="bottom",
                    )

                    with col_name:
                        st.text_input(
                            label="Name",
                            value=measure_type["name"],
                            key=f"edit_user_measure_name_{i}",
                            placeholder="e.g., weight, fat, muscle",
                            label_visibility="collapsed" if i != 0 else "visible",
                            disabled=(
                                True if measure_type["name"] == "Weight" else False
                            ),
                        )

                    with col_unit:
                        unit_options = ["kg", "g", "%", "cm", "m", "AU"]
                        unit_index = 0
                        if measure_type["unit"] in unit_options:
                            unit_index = unit_options.index(measure_type["unit"])
                        st.selectbox(
                            label="Unit",
                            options=unit_options,
                            index=unit_index,
                            key=f"edit_user_measure_unit_{i}",
                            label_visibility="collapsed" if i != 0 else "visible",
                            disabled=(
                                True if measure_type["name"] == "Weight" else False
                            ),
                        )

                    with col_decimals:
                        st.number_input(
                            label="Decimals",
                            value=measure_type["decimals"],
                            min_value=0,
                            max_value=10,
                            step=1,
                            key=f"edit_user_measure_decimals_{i}",
                            label_visibility="collapsed" if i != 0 else "visible",
                        )

                    with col_actions:
                        if measure_type["name"] != "Weight":
                            st.checkbox(
                                "Delete",
                                key=f"edit_user_delete_measure_{i}",
                                help="Check to delete this measurement type",
                            )

                    # No need to update session state - form inputs maintain their own state

                col_button, col_feedback = st.columns(
                    [1, 1], gap="small", vertical_alignment="bottom"
                )
                with col_button:
                    # Submit button
                    submitted = st.form_submit_button(
                        "update user data",
                        type="secondary",
                        use_container_width=True,
                        icon=":material/save:",
                    )

                # Handle form submission outside the form context
                if submitted:
                    # Process edit form (height, target, and measurement types from form inputs)
                    user.update_user(process_edit_form=True)

                    # Rerun to show feedback
                    st.rerun()

                # Feedback
                with col_feedback:
                    container_update = st.empty()
                    container_update.container(height=56, border=False)

                if st.session_state.flags["usr_update_ok"]:
                    st.session_state.flags["usr_update_ok"] = False
                    container_update.success(
                        "User **updated**", icon=":material/done_outline:"
                    )
                    time.sleep(1)
                    container_update.container(height=56, border=False)

        # Add new measurement type section
        st.divider()
        with st.container(border=False):
            st.markdown("##### Add New Measurement Type")
            with st.form(
                "add_new_measurement_form",
                clear_on_submit=False,
                border=False,
            ):

                col_name, col_unit, col_decimals, col_button = st.columns(
                    [2, 1, 1, 1], gap="small", vertical_alignment="bottom"
                )

                with col_name:
                    st.text_input(
                        "Name:",
                        placeholder="...",
                        max_chars=50,
                        key="new_measurement_name",
                        label_visibility="collapsed",
                    )

                with col_unit:
                    st.selectbox(
                        "Unit:",
                        options=["kg", "g", "%", "cm", "m", "AU"],
                        key="new_measurement_unit",
                        label_visibility="collapsed",
                    )

                with col_decimals:
                    st.number_input(
                        "Decimals:",
                        min_value=0,
                        max_value=10,
                        step=1,
                        key="new_measurement_decimals",
                        label_visibility="collapsed",
                    )

                with col_button:
                    if st.form_submit_button(
                        "add",
                        type="secondary",
                        use_container_width=True,
                        icon=":material/add_circle:",
                    ):
                        # Process the add new measurement type form
                        user.update_user(process_add_form=True)
                        st.rerun()


def delete_user(current_user: str) -> None:
    @st.dialog(f"Are you sure, {current_user}?")
    def delete_user(item):
        if st.button(
            "nope, please let me think about it.",
            type="secondary",
            use_container_width=True,
            icon=":material/cancel:",
        ):
            st.rerun()

        ut.h_spacer(1)
        submitted_del = st.button(
            "YES! LET'S DO IT!",
            type="primary",
            icon=":material/delete:",
            use_container_width=True,
            on_click=lambda: user.delete(current_user),
        )

        if submitted_del:
            st.rerun()

    st.markdown("###### Delete account")
    st.warning(
        f"This is not reversible and all data will be lost!\n\n"
        f"Consider downloading your file or copy your data manually.\n\n"
        f"It's located at _'data/{current_user}.csv'_.\n\n",
        icon=":material/warning:",
    )

    col_download, col_delete = st.columns(
        [1, 1], gap="small", vertical_alignment="center"
    )

    # download button
    with col_download:
        with open(f"data/{current_user}.csv", "r") as file:
            st.download_button(
                "Download Measurement Data",
                file,
                file_name=f"data_{current_user}.csv",
                use_container_width=True,
                mime="text/csv",
                type="secondary",
                icon=":material/download:",
            )

    # delete button
    with col_delete:
        if st.button("Delete User", icon=":material/delete:", use_container_width=True):
            delete_user(current_user)


def danger_zone(current_user: str) -> None:
    st.markdown("#### Danger Zone")
    with st.container(border=True):
        # delete user
        delete_user(current_user)


# ----- Measurements -------------------------------------------------------
def manage_measurements() -> None:
    with st.container(border=True):
        # get date first
        date = st.date_input("Date", "today", format="DD.MM.YYYY")

        # get measurements to fill in form
        last_measurements = data.get_last_measurements_before_date(date)

        # create form to fill in measurements
        with st.form("data_entry", border=False):
            # Get user's measure types
            measure_types = user.get_user_measure_types(st.session_state.user_name)

            # Create dynamic form fields based on user's measure types
            measurements = {}

            # Create columns for measurements (2 per row)
            for i in range(0, len(measure_types), 2):
                cols = st.columns([1, 1], gap="small")

                for j, col in enumerate(cols):
                    if i + j < len(measure_types):
                        measure_type = measure_types[i + j]
                        name = measure_type["name"]
                        var_name = name.lower().replace(" ", "_")
                        unit = measure_type["unit"]
                        decimals = measure_type["decimals"]

                        with col:
                            # Set appropriate min/max values based on unit
                            if unit == "kg":
                                min_val, max_val, step = 0.0, 200.0, 10**-decimals
                            elif unit == "%":
                                min_val, max_val, step = 0.0, 100.0, 10**-decimals
                            else:
                                min_val, max_val, step = 0.0, 1000.0, 10**-decimals

                            # Get value and ensure correct type (float or int)
                            value = last_measurements.get(var_name, 0.0)
                            if value is None:
                                value = 0.0

                            # If decimals is 0, use int types for consistency
                            if decimals == 0:
                                value = int(value) if value else 0
                                min_val, max_val, step = (
                                    int(min_val),
                                    int(max_val),
                                    int(step),
                                )
                                format_str = "%d"
                            else:
                                value = float(value) if value else 0.0
                                min_val, max_val, step = (
                                    float(min_val),
                                    float(max_val),
                                    float(step),
                                )
                                format_str = f"%.{decimals}f"

                            measurements[var_name] = st.number_input(
                                f"{name} [{unit}]:",
                                value=value,
                                min_value=min_val,
                                max_value=max_val,
                                step=step,
                                format=format_str,
                            )

            # check if measurements for this day are already saved
            if any(st.session_state.db["date"].dt.date == date):
                btn_add_upd_lbl = "**update** measurement"
                btn_add_upd_icn = ":material/update:"
                btn_del_disabled = False
            else:
                btn_add_upd_lbl = "**add new** measurement"
                btn_add_upd_icn = ":material/add_circle:"
                btn_del_disabled = True

            # submit button
            col_button, col_fdb_add_upd = st.columns(2, vertical_alignment="center")
            with col_button:
                submitted_add_upd = st.form_submit_button(
                    label=btn_add_upd_lbl,
                    icon=btn_add_upd_icn,
                    use_container_width=True,
                )

        # delete button
        col_delete, col_fdb_del = st.columns(2, vertical_alignment="center")
        with col_delete:
            submitted_del = st.button(
                label="**delete** measurement",
                icon=":material/delete:",
                disabled=btn_del_disabled,
                use_container_width=True,
            )

        # handle buttons
        if submitted_add_upd:
            data.add_update(date, measurements)
            st.rerun()

        if submitted_del:
            data.delete(date)
            st.rerun()

    # feedback messages ----------------------
    with col_fdb_add_upd:
        container_fdb_add_upd = st.empty()
        container_fdb_add_upd.container(height=56, border=False)

    with col_fdb_del:
        container_fdb_del = st.empty()
        container_fdb_del.container(height=56, border=False)

    if st.session_state.flags["data_add"]:
        st.session_state.flags["data_add"] = False
        container_fdb_add_upd.success(
            "new entry **added**", icon=":material/add_circle:"
        )
        time.sleep(2)
        container_fdb_add_upd.container(height=56, border=False)

    if st.session_state.flags["data_upd"]:
        st.session_state.flags["data_upd"] = False
        container_fdb_add_upd.success("old entry **updated**", icon=":material/update:")
        time.sleep(2)
        container_fdb_add_upd.container(height=56, border=False)

    if st.session_state.flags["data_del"]:
        st.session_state.flags["data_del"] = False
        container_fdb_del.success("entry **deleted**", icon=":material/delete:")
        time.sleep(2)
        container_fdb_del.container(height=56, border=False)


def display_measurements() -> None:
    st.subheader("All Measurements")

    # Get user's measure types for column configuration
    measure_types = user.get_user_measure_types(st.session_state.user_name)

    # Create dynamic column configuration
    column_config = {
        "date": st.column_config.DateColumn(
            label="Date", format="DD.MM.YYYY", pinned=True
        ),
    }

    # Add column config for each measure type
    for measure_type in measure_types:
        name = measure_type["name"]
        var_name = name.lower().replace(" ", "_")
        unit = measure_type["unit"] if measure_type["unit"] != "%" else "%%"
        decimals = measure_type["decimals"]

        column_config[var_name] = st.column_config.NumberColumn(
            label=name, format=f"%.{decimals}f {unit}"
        )

    st.dataframe(
        st.session_state.db.sort_values(by="date", ascending=False),
        use_container_width=True,
        hide_index=True,
        height=246,
        column_config=column_config,
    )
