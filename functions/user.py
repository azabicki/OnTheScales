import os
from datetime import datetime
import streamlit as st
import pandas as pd
import functions.data as data
import functions.utils as utils


def select_user(src: str, del_idx: int) -> None:
    """
        select active user via selectbox and update the session_state variables wrt to the now active user
    """

    match src:
        # from sidebar
        case "sidebar":
            idx = st.session_state["sb_user"]

        # from sidebar
        case "deletion":

            # last user deleted
            if len(st.session_state.user_db) == 0:
                idx = None

            # deleted used was ABOVE active
            elif del_idx <  st.session_state.user_idx:
                idx = st.session_state.user_idx-1

            # deleted used was UNDER active
            elif del_idx > st.session_state.user_idx:
                idx = st.session_state.user_idx

            # deleted user was EQUAL active
            else:
                nUser = len(st.session_state.user_db)-1
                idx = del_idx if del_idx < nUser else nUser

        case _:
            idx = None

    # update user
    st.session_state.user_idx = idx

    # update user settings
    utils.set_user_sessionstate()

    # load user db
    if st.session_state.user_idx is not None:
        st.session_state.db = data.load()
    else:
        st.session_state.db = data.create_df()


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

    # set flag
    st.session_state.flags["usr_add_ok"] = True

    # reset session state variables
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


def update_user():
    """
        update user's height and/or target, based on changes made manually to dataframe
    """

    # first, process edited cells and create temporary df
    st.session_state.user_db = st.session_state.user_db.copy()
    edt = st.session_state.user_edited["edited_rows"]
    for idx, dct in edt.items():
        for col, val in dct.items():
            st.session_state.user_db.loc[idx, col] = val

    # set flag
    st.session_state.flags["usr_update_ok"] = True

    # update user_db and user_data in session_state
    st.session_state.user_cm = st.session_state.user_db.loc[st.session_state.user_idx, "height"]
    st.session_state.user_kg = st.session_state.user_db.loc[st.session_state.user_idx, "target"]

    # save users.csv
    st.session_state.user_db.to_csv(os.path.join("data", "users.csv"), index=False)



def delete(idx: int|None) -> None:
    """
    Deletes a user from the user database and removes their csv file.

    Args:
        idx (int|None): Index of user to delete in the user database dataframe.
            If None, resets session state variables and returns.

    Returns:
        None
    """

    # if idx is None, reset session state variables and return
    if idx is None:
        st.session_state.sb_user_delete = None
        return

    # remove user's data csv file
    os.remove(os.path.join("data", st.session_state.user_db.loc[idx, "name"] + ".csv"))

    # delete user from user_db
    print(st.session_state.user_db)
    st.session_state.user_db = st.session_state.user_db.drop(idx).reset_index(drop=True)
    print(st.session_state.user_db)

    # save users.csv
    st.session_state.user_db.to_csv(os.path.join("data", "users.csv"), index=False)

    # handle 'active user' when deleted user was active user
    print("___handle active user, deleted: ", idx)
    select_user(src="deletion", del_idx=idx)

    # set flag
    st.session_state.flags["usr_del_ok"] = True
