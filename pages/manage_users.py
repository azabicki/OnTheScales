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

# delete users ----------------------------------------------------------------
ut.h_spacer(2)
st.subheader("Delete User")
with st.container(border=True):
    col_del_sb, col_del_btn = st.columns([1, 1], gap="medium")
    # select box
    with col_del_sb:
        usr_idx = [i for i, _ in st.session_state.user_db.iterrows()]
        usr_name = [r["name"] for i, r in st.session_state.user_db.iterrows()]

        st.selectbox(
            "select user:",
            label_visibility="collapsed",
            options=usr_idx,
            format_func=lambda i: usr_name[i],
            key="sb_user_delete",
            placeholder="...",
            index=None
        )

    # submit button inside a popover
    with col_del_btn:
        with st.popover(
                "delete user",
                use_container_width=True,
                icon="🚨",
                disabled=True if st.session_state.sb_user_delete is None else False):

            # last question
            st.subheader(f"Are you sure to delete _'{usr_name[st.session_state.sb_user_delete] if st.session_state.sb_user_delete is not None else ''}'_?")
            st.caption("This is not reversible and all data will be lost! Maybe consider __exporting__ the data first?")

            col_b1, col_b2 = st.columns([1, 1], gap="small")
            # abort button
            with col_b1:
                submitted_abort = st.button(
                    "nope... stop it!",
                    type="secondary",
                    use_container_width=True,
                    on_click=user.delete,
                    args=(None, ),
                    disabled=True if st.session_state.sb_user_delete is None else False
                )
            # delete button !
            with col_b2:
                submitted_del = st.button(
                    "YES! LET'S DO IT!",
                    type="primary",
                    icon="🔥",
                    use_container_width=True,
                    on_click=user.delete,
                    args=(st.session_state.sb_user_delete, ),
                    disabled=True if st.session_state.sb_user_delete is None else False
                )

    # placeholder for feedback
    container_del = st.empty()

    # flag submission & rerun
    if submitted_del or submitted_abort:
        st.rerun()

    # show feedback
    if st.session_state.flags["usr_del_ok"]:
        st.session_state.flags["usr_del_ok"] = False
        container_del.success("User **deleted**")
        time.sleep(1)
        container_del.empty()
