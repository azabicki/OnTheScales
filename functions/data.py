import os
import streamlit as st
import pandas as pd
import numpy as np


def create_df() -> pd.DataFrame:
    """
    Generates an empty dataframe with date, weight, fat, water, and muscle metrics

    Returns:
        pd.DataFrame: empty base dataframe with column structure
    """

    cols = {"date":[], "weight":[], "fat":[], "water":[], "muscle":[]}
    df = pd.DataFrame(cols)
    return df


def load() -> pd.DataFrame:
    """
    Loads current user data from .csv file and returns as pandas dataframe

    Returns:
        pd.DataFrame: user's health metrics data
    """

    usr_name = st.session_state.user_name
    db = pd.read_csv(os.path.join("data", usr_name + ".csv"))
    db["date"] = pd.to_datetime(db["date"])
    return db

