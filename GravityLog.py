import streamlit as st
import functions.utils as ut

# init default values
ut.init_vars()
ut.default_style()
ut.create_menu()

# name of current user
st.title("Gravity Log !!")
ut.h_spacer()
st.divider()

