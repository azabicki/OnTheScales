import time
import pandas as pd
import streamlit as st
import functions.utils as ut
import functions.data as data

ut.init_vars()
ut.default_style()
ut.create_menu()

# manage measurement ---------------------------------------------------------
st.subheader("Manage Measurements")
with st.container(border=True):
    # get date first
    date = st.date_input("Date", "today", format="DD.MM.YYYY")

    # get measurements to fill in form
    if st.session_state.db.shape[0] == 0:
        # if database is empty, use default values
        value_wgt = 80.0
        value_fat = 25.0
        value_h2o = 50.0
        value_msc = 25.0
    else:
        # else get last measurements before current date
        # find index of last measurement before current date
        if date < st.session_state.db["date"].min().date():
            idx_date = 0
        else:
            dates = st.session_state.db["date"][::-1] <= pd.to_datetime(date)
            idx_date = dates.idxmax()

        # get values of last measurement before current date
        value_wgt = st.session_state.db.loc[idx_date, "weight"]
        value_fat = st.session_state.db.loc[idx_date, "fat"]
        value_h2o = st.session_state.db.loc[idx_date, "water"]
        value_msc = st.session_state.db.loc[idx_date, "muscle"]

    # create form to fill in measurements
    with st.form('data_entry', border=False):
        # measurements fields
        col_wgt, col_fat = st.columns([1, 1], gap="small")
        with col_wgt:
            wgt = st.number_input(
                "Weight [kg]:",
                value=value_wgt,
                min_value=0.0,
                max_value=200.0,
                step=0.1,
                format="%.1f",
            )
        with col_fat:
            fat = st.number_input(
                "Fat [%]:",
                value=value_fat,
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
            )
        col_h20, col_msc = st.columns([1, 1], gap="small")
        with col_h20:
            h2o = st.number_input(
                "Water [%]:",
                value=value_h2o,
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
            )
        with col_msc:
            msc = st.number_input(
                "Muscle [%]:",
                value=value_msc,
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
            )

        # check if measurements for this day are already saved
        if any(st.session_state.db["date"] == pd.to_datetime(date)):
            btn_add_upd_lbl = "**update** measurement"
            btn_del_disabled = False
        else:
            btn_add_upd_lbl = "**add new** measurement"
            btn_del_disabled = True

        # submit button
        col_btn_add_upd, col_fdb_add_upd = st.columns([1, 3], gap="small")
        with col_btn_add_upd:
            submitted_add_upd = st.form_submit_button(label=btn_add_upd_lbl)
        with col_fdb_add_upd:
            container_add_upd = st.empty()

    # delete button and feedback
    col_btn_del, col_fdb_del = st.columns([1, 3], gap="small")
    with col_btn_del:
        submitted_del = st.button(label="**delete** measurement", disabled=btn_del_disabled)
    with col_fdb_del:
        container_del = st.empty()

    # handle ADDING/UPDATING
    if submitted_add_upd:
        # add data entry
        data.add_update(date, wgt, fat, h2o, msc)
        # rerun 4 feedback
        st.rerun()

    # handle DELETION
    if submitted_del:
        # delete entry
        data.delete(date)
        # rerun 4 feedback
        st.rerun()

# overview database entries -----------------------------------------------
ut.h_spacer(2)
st.subheader("All Measurements")
st.dataframe(
    st.session_state.db.sort_values(by="date", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "date": st.column_config.DateColumn(
            label="Date", format="DD.MM.YYYY", pinned=True),
        "weight": st.column_config.NumberColumn(
            label="Weight", format="%.1f kg"),
        "fat": st.column_config.NumberColumn(
            label="% Fat", format="%.1f %%"),
        "water": st.column_config.NumberColumn(
            label="% Water", format="%.1f %%"),
        "muscle": st.column_config.NumberColumn(
            label="% Muscle", format="%.1f %%"),
    },
)

# display messages ----------------------
if st.session_state.flags["data_add"]:
    st.session_state.flags["data_add"] = False
    container_add_upd.success("new entry **added**", icon=":material/add_circle:")
    time.sleep(2)
    container_add_upd.empty()

if st.session_state.flags["data_upd"]:
    st.session_state.flags["data_upd"] = False
    container_add_upd.success("old entry **updated**", icon=":material/update:")
    time.sleep(2)
    container_add_upd.empty()

if st.session_state.flags["data_del"]:
    st.session_state.flags["data_del"] = False
    container_del.success("entry **deleted**", icon=":material/delete:")
    time.sleep(2)
    container_del.empty()
