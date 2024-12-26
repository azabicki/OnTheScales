import os
import numpy as np
import pandas as pd
import streamlit as st
from datetime import date


def create_df() -> pd.DataFrame:
    """
    Generates an empty dataframe with date, weight, fat, water, and muscle metrics

    Returns:
        pd.DataFrame: empty base dataframe with column structure
    """

    cols = {"date": [], "weight": [], "fat": [], "water": [], "muscle": []}
    df = pd.DataFrame(cols)
    return df


def load_db() -> pd.DataFrame:
    """
    Loads current user data from .csv file and returns as pandas dataframe

    Returns:
        pd.DataFrame: user's health metrics data
    """

    usr_name = st.session_state.user_name
    db = pd.read_csv(os.path.join("data", usr_name + ".csv"))
    db["date"] = pd.to_datetime(db["date"])
    return db


def add_update(date: date, wgt: float, fat: float, h2o: float, msc: float) -> None:
    """
    Adds a new entry with health metrics to user database or updates existing record

    Args:
        date (date): date of entry
        wgt (float): weight measurement
        fat (float): body fat percentage
        h2o (float): body water percentage
        msc (float): muscle mass percentage

    Returns:
        None
    """

    # new row for date
    new_entry = pd.DataFrame.from_dict(
        {
            "date": [pd.to_datetime(date)],
            "weight": round(wgt, 1),
            "fat": round(fat, 1),
            "water": round(h2o, 1),
            "muscle": round(msc, 1),
        },
    )

    # handle new entry, either update or add it, and set flags
    if any(st.session_state.db["date"] == pd.to_datetime(date)):
        # update previously saved entry
        st.session_state.flags["data_upd"] = True

        # find indes of entry to update
        idx_date = (st.session_state.db["date"] == pd.to_datetime(date)).idxmax()

        # update entry
        st.session_state.db.loc[idx_date, "weight"] = round(wgt, 1)
        st.session_state.db.loc[idx_date, "fat"] = round(fat, 1)
        st.session_state.db.loc[idx_date, "water"] = round(h2o, 1)
        st.session_state.db.loc[idx_date, "muscle"] = round(msc, 1)

    else:
        # add new entry
        st.session_state.flags["data_add"] = True

        if st.session_state.db.shape[0] == 0:
            # if data_db is empty
            st.session_state.db = new_entry
        else:
            # else append to data_db
            st.session_state.db = pd.concat(
                [st.session_state.db, new_entry], ignore_index=True
            )

    # sort & save db
    save_db()


def delete(date: date) -> None:
    """
    Deletes user entry for given date from database file

    Args:
        date (date): date of entry to delete

    Returns:
        None
    """
    # set flag
    st.session_state.flags["data_del"] = True

    # find index of entry to delete
    idx_date = st.session_state.db["date"] == pd.to_datetime(date)

    # save all but deleted entry
    st.session_state.db = st.session_state.db.loc[np.invert(idx_date), :]

    # sort & save db
    save_db()


def save_db() -> None:
    """
    Sorts user database by date and writes to .csv file

    Returns:
        None
    """

    # sort db
    st.session_state.db = st.session_state.db.sort_values(by="date", ignore_index=True)

    # save db to csv
    st.session_state.db.to_csv(
        os.path.join("data", st.session_state.user_name + ".csv"), index=False
    )
