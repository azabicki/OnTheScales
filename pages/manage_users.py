import time
import streamlit as st
import functions.utils as ut
import functions.user as user

# init default values
ut.init_vars()
ut.default_style()
ut.create_menu()

# update users ----------------------------------------------------------------
st.subheader("Manage Users")
st.markdown("Edit the fields accordingly and press [enter].")
edited_user = st.data_editor(
    st.session_state.user_db,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_order=("name", "height", "target"),
    column_config={
        "name": st.column_config.Column(label="Name", disabled=True),
        "height": st.column_config.NumberColumn(
            label="Height", format="%d cm", required=True, min_value=0, max_value=250
        ),
        "target": st.column_config.NumberColumn(
            label="Target Weight",
            format="%d kg",
            required=True,
            min_value=0,
            max_value=200,
        ),
    },
    on_change=user.update_user,
    key="user_edited"
)

# placeholder for feedback
container_update = st.empty()

# show feedback
if st.session_state.flags["usr_update_ok"]:
    st.session_state.flags["usr_update_ok"] = False
    container_update.success("User **updated**")
    time.sleep(2)
    container_update.empty()

if st.session_state.flags["usr_update_exists"]:
    st.session_state.flags["usr_update_exists"] = False
    container_update.error("User name already in database")
    time.sleep(2)
    container_update.empty()
    st.rerun()


# add users -------------------------------------------------------------------
ut.h_spacer(2)
st.subheader("Add User")
with st.container(border=True):
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
            "Height:", min_value=0, max_value=250, step=1, value=180, format="%d cm", key="new_usr_height"
        )

    # target weight
    with col_trgt:
        target = st.slider(
            "Target Weight:", min_value=0, max_value=200, step=1, value=80, format="%d kg", key="new_usr_target"
        )

    col_btn, col_fdb = st.columns([1, 4], gap="small")
    # submit button
    with col_btn:
        submitted_add = st.button(
            "add new user",
            disabled=True if st.session_state.new_usr_name == "" else False,
            on_click=user.add,
            args=(name, height, target)
        )

    # placeholder for feedback
    with col_fdb:
        container_add = st.empty()

    # flag submission & rerun
    if submitted_add:
        st.rerun()

    # show feedback
    if st.session_state.flags["usr_add_ok"]:
        st.session_state.flags["usr_add_ok"] = False
        container_add.success("User **added**")
        time.sleep(2)
        container_add.empty()

    if st.session_state.flags["usr_add_exists"]:
        st.session_state.flags["usr_add_exists"] = False
        container_add.error("User already in database")
        time.sleep(2)
        container_add.empty()

