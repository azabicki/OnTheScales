import time
import pandas as pd
import streamlit as st
import functions.utils as ut
import functions.data as data
import debug as dbg

ut.init_vars()
ut.default_style()
ut.create_menu()



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
