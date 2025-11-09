import os
import numpy as np
import pandas as pd
import streamlit as st
from datetime import date
import functions.user as user


def create_df() -> pd.DataFrame:
    """
    Generates an empty dataframe with date and dynamic measure types based on user settings

    Returns:
        pd.DataFrame: empty base dataframe with column structure
    """
    # Get user's measure types
    measure_types = user.get_user_measure_types(st.session_state.user_name)

    # Start with date column
    cols = {"date": []}

    # Add columns for each measure type
    for measure_type in measure_types:
        cols[measure_type["name"].lower().replace(" ", "_")] = []

    df = pd.DataFrame(cols)
    return df


def load_db() -> pd.DataFrame:
    """
    Loads current user data from .csv file and returns as pandas dataframe

    Returns:
        pd.DataFrame: user's health metrics data
    """

    usr_name = st.session_state.user_name
    csv_path = os.path.join("data", usr_name + ".csv")

    # Check if CSV file exists, if not create empty dataframe
    if not os.path.exists(csv_path):
        return create_df()

    try:
        db = pd.read_csv(csv_path)
        db["date"] = pd.to_datetime(db["date"])
        return db
    except Exception:
        # If CSV is corrupted, return empty dataframe
        return create_df()


def add_update(
    date: date,
    measurements: dict,
    suppress_feedback: bool = False,
    data_source: str | None = None,
) -> None:
    """
    Adds a new entry with health metrics to user database or updates existing record

    Args:
        date (date): date of entry
        measurements (dict): dictionary of measurement values with measure type names as keys
        suppress_feedback (bool): whether to suppress feedback messages
        data_source (str): source of the data ("withings", etc.) for config lookup

    Returns:
        None
    """

    # Check for new measure types and add them to user's configuration
    if data_source is not None:
        user.add_user_measure_types(
            measurements,
            data_source,
        )

    # Get user's measure types for decimal precision (after potential updates)
    user_measure_types = user.get_user_measure_types(st.session_state.user_name)

    # Create a mapping of measure names to their decimal precision
    user_measure_decimals = {
        measure_type["name"].lower().replace(" ", "_"): measure_type["decimals"]
        for measure_type in user_measure_types
    }

    # Create new entry dictionary starting with date
    new_entry_dict = {"date": [pd.to_datetime(date)]}

    # Add each measure type from the incoming measurements
    for measure_name, value in measurements.items():
        # Get decimal precision from user config, default to 1 if not found
        decimals = user_measure_decimals.get(measure_name, 1)

        new_entry_dict[measure_name] = (
            [round(value, decimals)] if value is not None else [None]
        )

    # new row for date
    new_entry = pd.DataFrame.from_dict(new_entry_dict)

    # handle new entry, either update or add it, and set flags
    if any(st.session_state.db["date"] == pd.to_datetime(date)):
        # find index of entry to update
        idx_date = (st.session_state.db["date"] == pd.to_datetime(date)).idxmax()

        # update entry for each measure type from incoming measurements
        for measure_name, value in measurements.items():
            if value is not None:
                # Get decimal precision from user config, default to 1 if not found
                decimals = user_measure_decimals.get(measure_name, 1)
                st.session_state.db.loc[idx_date, measure_name] = round(value, decimals)

        if not suppress_feedback:
            st.session_state.flags["data_upd"] = True

    else:
        # add new entry
        if st.session_state.db.shape[0] == 0:
            # if data_db is empty
            st.session_state.db = new_entry
        else:
            # else append to data_db
            st.session_state.db = pd.concat(
                [st.session_state.db, new_entry], ignore_index=True
            )

        if not suppress_feedback:
            st.session_state.flags["data_add"] = True

    # sort & save db
    save_db()


def get_default_measurements() -> dict:
    """
    Get default measurement values for the current user's measure types.

    Returns:
        dict: Dictionary with default values for each measure type
    """
    measure_types = user.get_user_measure_types(st.session_state.user_name)
    defaults = {}

    # Set default values based on measure type
    for measure_type in measure_types:
        measure_name = measure_type["name"]
        if measure_name == "weight":
            defaults[measure_name] = 80.0
        elif measure_name in ["fat", "water", "muscle"]:
            defaults[measure_name] = 25.0
        else:
            defaults[measure_name] = 0.0

    return defaults


def get_last_measurements_before_date(target_date: date) -> dict:
    """
    Get the last measurements before a given date for the current user.

    Args:
        target_date (date): The date to find measurements before

    Returns:
        dict: Dictionary with the last measurement values for each measure type
    """
    measure_types = user.get_user_measure_types(st.session_state.user_name)

    if st.session_state.db.shape[0] == 0:
        return get_default_measurements()

    # Find index of last measurement before current date
    if target_date < st.session_state.db["date"].min().date():
        idx_date = 0
    else:
        dates = st.session_state.db["date"][::-1].dt.date <= target_date
        idx_date = dates.idxmax()

    # Get values of last measurement before current date
    last_measurements = {}
    for measure_type in measure_types:
        var_name = measure_type["name"].lower().replace(" ", "_")
        # Check if column exists in database before accessing
        if var_name in st.session_state.db.columns:
            last_measurements[var_name] = st.session_state.db.loc[idx_date, var_name]
        else:
            # If column doesn't exist, use None or default value
            last_measurements[var_name] = None

    return last_measurements


def delete(date: date, suppress_feedback: bool = False) -> None:
    """
    Deletes user entry for given date from database file

    Args:
        date (date): date of entry to delete

    Returns:
        None
    """
    # set flag
    if not suppress_feedback:
        st.session_state.flags["data_del"] = True

    # find index of entry to delete
    idx_date = st.session_state.db["date"] == pd.to_datetime(date)

    # save all but deleted entry
    st.session_state.db = st.session_state.db.loc[np.invert(idx_date), :]

    # sort & save db
    save_db()


def add_measure_column(measure_name: str) -> None:
    """
    Adds a new measure column to the current session state database and updates the CSV file.

    Args:
        measure_name (str): Name of the measure type to add
    """
    if measure_name not in st.session_state.db.columns:
        st.session_state.db[measure_name] = None
        save_db()


def delete_measure_column(measure_name: str) -> None:
    """
    Deletes a measure column from the current session state database and updates the CSV file.

    Args:
        measure_name (str): Name of the measure type to delete
    """
    if measure_name in st.session_state.db.columns:
        st.session_state.db = st.session_state.db.drop(columns=[measure_name])
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
