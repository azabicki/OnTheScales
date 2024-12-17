import os
from datetime import datetime
import streamlit as st
import pandas as pd
import functions.data as data


def select_user():
    """
        select active user via selectbox and update the session_state variables wrt to the now active user
    """
    print("___ user from selectbox: ", st.session_state["sb_user"])
    # update user
    st.session_state.user_idx = st.session_state["sb_user"]

    # update user settings
    st.session_state.user_name = st.session_state.user_db.loc[st.session_state.user_idx, "name"]
    st.session_state.user_cm = st.session_state.user_db.loc[st.session_state.user_idx, "height"]
    st.session_state.user_kg = st.session_state.user_db.loc[st.session_state.user_idx, "target"]
    st.session_state.trend_how = st.session_state.user_db.loc[st.session_state.user_idx, "trend_how"]
    st.session_state.trend_start = st.session_state.user_db.loc[st.session_state.user_idx, "trend_start"]
    st.session_state.trend_range = st.session_state.user_db.loc[st.session_state.user_idx, "trend_range"]

    # load user db
    st.session_state.db = data.load()


def load_db() -> pd.DataFrame:
    """
        loads the user database `data/users.csv`
    """
    # return pd.read_csv(os.path.join("data", "usersBSK.csv"))
    return pd.read_csv(os.path.join("data", "users.csv"))


def add(name, height, target) -> None:
    """
        add new user to database and create a new csv file for users measurements

        Args:
            name (str): name of the user
            height (int): height of the user
            target (int): target weight of the user
    """

    # return if user already exists
    if name in st.session_state.user_db["name"].values:
        st.session_state.flags["usr_add_exists"] = True
        return

    # reset session state variables
    st.session_state.flags["usr_add_ok"] = True
    st.session_state["new_usr_name"] = ""
    st.session_state["new_usr_height"] = 180
    st.session_state["new_usr_target"] = 80

    # new row for user
    new_user = pd.DataFrame.from_records({
        "name": name,
        "height": height,
        "target": target,
        "trend_how": "date_range",
        "trend_start": datetime.now().date(),
        "trend_range": 4
    },index=[0])

    # add row to users_db
    st.session_state.user_db = pd.concat([st.session_state.user_db, new_user], ignore_index=True)

    # save users.csv
    st.session_state.user_db.to_csv(os.path.join("data", "users.csv"), index=False)

    # create new csv for new user
    new_db = data.create_df()
    new_db.to_csv(os.path.join("data", name + ".csv"), index=False)
