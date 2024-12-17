import os
import streamlit as st
import pandas as pd
import numpy as np


def create_df() -> pd.DataFrame:
    """
        creates a dataframe with the data for the user
    """
    cols = {"date":[], "weight":[], "fat":[], "water":[], "muscle":[]}
    df = pd.DataFrame(cols)
    return df


def load() -> pd.DataFrame:
    """
        loads the data from the csv file
    """
    usr_name = st.session_state.user_name
    db = pd.read_csv(os.path.join("data", usr_name + ".csv"))
    db["date"] = pd.to_datetime(db["date"])
    return db

