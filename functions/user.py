import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime
import functions.data as data
import functions.utils as ut


def select_user(src: str) -> None:
    """
    Updates the active user according to source:

    "sidebar":
        Selectbox in the sidebar changed: new user selected, change session state user

    "deleting":
        Delete button was used: deleted user was active, new user to be selected

    "adding":
        Add button was used: new user was added, new user to be selected

    When user changes:
        - update session state user index/name/height/target/trend-data
        - load db for selected user

    Args:
        src (str): Source of the call "sidebar" | "deleting" | "adding"

    Returns:
        None
    """

    # Get current users list
    users_dict = load_users_dict()
    user_names = list(users_dict.keys())

    match src:
        # from sidebar
        case "sidebar":
            idx = st.session_state["sb_user"]

        # after adding new user
        case "adding":
            idx = len(user_names) - 1

        # after deletion
        case "deleting":
            idx = None

        case _:
            idx = None

    # update user + selectbox in menu
    st.session_state.user_idx = idx
    st.session_state.sb_user = idx

    # update user settings
    ut.set_user_sessionstate(what="user")
    ut.set_user_sessionstate(what="trend")

    # load user db
    if st.session_state.user_idx is not None:
        st.session_state.db = data.load_db()
    else:
        st.session_state.db = data.create_df()


def load_db() -> pd.DataFrame:
    """
    Load the user database from JSON file.

    Reads and returns the users.json file which contains user profiles and settings.

    Returns:
        pd.DataFrame: DataFrame containing user data from users.json
    """

    json_path = os.path.join("data", "users.json")

    if not os.path.exists(json_path):
        # Create empty JSON file if it doesn't exist
        with open(json_path, "w") as f:
            json.dump([], f)
        return pd.DataFrame()

    with open(json_path, "r") as f:
        users_data = json.load(f)

    if not users_data:
        return pd.DataFrame()

    # Convert JSON to DataFrame
    db = pd.DataFrame(users_data)
    db["trend_start"] = pd.to_datetime(db["trend_start"])

    return db


def load_users_dict() -> dict:
    """
    Load the user database from JSON file as a dictionary.

    Reads and returns the users.json file which contains user profiles and settings.

    Returns:
        dict: Dictionary with user names as keys and user data as values
    """

    json_path = os.path.join("data", "users.json")

    if not os.path.exists(json_path):
        # Create empty JSON file if it doesn't exist
        with open(json_path, "w") as f:
            json.dump([], f)
        return {}

    with open(json_path, "r") as f:
        users_data = json.load(f)

    if not users_data:
        return {}

    # Convert list of users to dictionary with names as keys
    users_dict = {}
    for user_data in users_data:
        # Convert trend_start string to datetime if it exists
        if "trend_start" in user_data and user_data["trend_start"]:
            try:
                from datetime import datetime

                user_data["trend_start"] = datetime.fromisoformat(
                    user_data["trend_start"]
                ).date()
            except (ValueError, TypeError):
                # Keep as string if parsing fails
                pass

        users_dict[user_data["name"]] = user_data

    return users_dict


def add_user(name: str, height: int, target: int) -> None:
    """
    Add a new user to the database and create a new CSV file for user measurements.

    Takes the user's name, height, and target weight, creates a new entry in the
    user database with default trend settings and measure types, and generates a blank measurement
    CSV file for the new user.

    If the user name already exists, sets a flag and returns without making changes.

    Args:
        name (str): Name of the user to add
        height (int): Height of the user in centimeters
        target (int): Target weight of the user in kilograms

    Returns:
        None

    Side Effects:
        - Creates new user entry in users.json
        - Creates new blank CSV file for user measurements
        - Updates session state user database
        - Sets success/error flags in session state
    """

    # return if user already exists
    users_dict = load_users_dict()
    if name in users_dict:
        st.session_state.flags["usr_add_exists"] = True
        st.session_state.flags["usr_add_exists_name"] = name
        return

    # set flag
    st.session_state.flags["usr_add_ok"] = True

    # reset session state variables
    st.session_state["new_usr_name"] = ""
    st.session_state["new_usr_height"] = 180
    st.session_state["new_usr_target"] = 80

    # Default measure types for new users
    default_measure_types = [
        {"name": "Weight", "unit": "kg", "decimals": 2},
        {"name": "Fat", "unit": "%", "decimals": 1},
        {"name": "Water", "unit": "%", "decimals": 1},
        {"name": "Muscle", "unit": "%", "decimals": 1},
    ]

    # new user data
    new_user_data = {
        "name": name,
        "height": height,
        "target": target,
        "trend_how": "date range",
        "trend_start": datetime.now().date().isoformat(),
        "trend_range": 8,
        "measure_types": default_measure_types,
        "imported_dates": [],
    }

    # Load existing users from JSON
    json_path = os.path.join("data", "users.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            users_data = json.load(f)
    else:
        users_data = []

    # Add new user
    users_data.append(new_user_data)

    # Save to JSON
    with open(json_path, "w") as f:
        json.dump(users_data, f, indent=2)

    # create new csv for new user
    new_db = data.create_df()
    new_db.to_csv(os.path.join("data", name + ".csv"), index=False)

    # handle 'active user' when user was added
    select_user(src="adding")


def update_user(
    process_edit_form: bool = False,
    process_add_form: bool = False,
) -> None:
    """
    Updates the data of the current user in the user database.

    Can be called in two ways:
    1. Edit form mode: Processes edit form inputs (height, target, and measurement types)
    2. Add form mode: Processes add new measurement type form

    The current user is inferred from st.session_state.user_name.

    Args:
        process_edit_form (bool): If True, processes edit form inputs from session state
        process_add_form (bool): If True, processes add new measurement type form

    Returns:
        None
    """

    # Get current user from session state
    current_user = st.session_state.user_name

    # Load current users
    users_dict = load_users_dict()
    current_user_dict = users_dict[current_user]

    # Edit form mode: Process edit form inputs (height, target, and measurement types)
    if process_edit_form:
        # Update basic user data from form inputs
        if "edit_user_height" in st.session_state:
            current_user_dict["height"] = st.session_state["edit_user_height"]
        if "edit_user_target" in st.session_state:
            current_user_dict["target"] = st.session_state["edit_user_target"]

        # Process measurement types
        current_measure_types = current_user_dict.get("measure_types", [])

        # Collect form data directly from form inputs
        updated_measure_types = []
        for i in range(len(current_measure_types)):
            delete_key = f"edit_user_delete_measure_{i}"

            # Skip if marked for deletion
            if delete_key in st.session_state and st.session_state[delete_key]:
                data.delete_measure_column(
                    current_measure_types[i]["name"].lower().replace(" ", "_")
                )
                continue

            # Get form input values
            name_key = f"edit_user_measure_name_{i}"
            unit_key = f"edit_user_measure_unit_{i}"
            decimals_key = f"edit_user_measure_decimals_{i}"

            if all(
                key in st.session_state for key in [name_key, unit_key, decimals_key]
            ):
                name = st.session_state[name_key].strip()
                if name:  # Only add if name is not empty
                    updated_measure_types.append(
                        {
                            "name": name,
                            "unit": st.session_state[unit_key],
                            "decimals": st.session_state[decimals_key],
                        }
                    )

        # Update the user with processed measurement types
        current_user_dict["measure_types"] = updated_measure_types

    # Add form mode: Process add new measurement type form
    elif process_add_form:
        # Get form input values
        name = st.session_state.get("new_measurement_name", "").strip()
        unit = st.session_state.get("new_measurement_unit", "kg")
        decimals = st.session_state.get("new_measurement_decimals", 1)

        if name:  # Only add if name is not empty
            # Add new measurement type
            new_measure_type = {
                "name": name,
                "unit": unit,
                "decimals": decimals,
            }

            current_user_dict["measure_types"].append(new_measure_type)

            # Add new column to session state database
            data.add_measure_column(name.lower().replace(" ", "_"))

    # Save updated users to JSON
    save_users_dict_to_json(users_dict)

    # set flag
    st.session_state.flags["usr_update_ok"] = True


def update_trend() -> None:
    """
    Updates trend settings for the current user.

    Takes trend settings from session state (how/start/range) and updates them
    in the user database, then saves to users.json.

    Returns:
        None
    """

    # Load current users
    users_dict = load_users_dict()
    user_names = list(users_dict.keys())

    if st.session_state.user_idx is not None and st.session_state.user_idx < len(
        user_names
    ):
        current_user = user_names[st.session_state.user_idx]

        # Update trend settings
        users_dict[current_user]["trend_how"] = st.session_state.trend_how
        # Store trend_start as date only (not datetime)
        trend_start_value = st.session_state.trend_start
        if hasattr(trend_start_value, "date"):
            users_dict[current_user]["trend_start"] = trend_start_value.date()
        else:
            users_dict[current_user]["trend_start"] = trend_start_value
        users_dict[current_user]["trend_range"] = st.session_state.trend_range

        # Save updated users to JSON
        save_users_dict_to_json(users_dict)


def delete(user_to_delete: str) -> None:
    """
    Deletes a user from the user database and removes their csv file.

    Args:
        user_to_delete (str): Name of user to delete in the user database.
            If None, resets session state variables and returns.

    Returns:
        None
    """

    # Load current users
    users_dict = load_users_dict()

    # remove user's data csv file
    os.remove(os.path.join("data", user_to_delete + ".csv"))

    # delete user from dictionary
    del users_dict[user_to_delete]

    # save updated users to JSON
    save_users_dict_to_json(users_dict)

    # handle 'active user' when user was deleted
    select_user(src="deleting")

    # set flag
    st.session_state.flags["usr_del_ok"] = True
    st.session_state.flags["usr_del_name"] = user_to_delete


def save_users_dict_to_json(users_dict: dict) -> None:
    """
    Saves a users dictionary to users.json file.

    Converts the dictionary to JSON format and saves it to the users.json file.
    Handles the conversion of datetime objects to ISO format strings.

    Args:
        users_dict (dict): Dictionary with user names as keys and user data as values

    Returns:
        None
    """
    json_path = os.path.join("data", "users.json")

    # Convert dictionary to list of dictionaries
    users_data = list(users_dict.values())

    # Convert datetime objects to ISO format strings (date only)
    for user_data in users_data:
        if "trend_start" in user_data and user_data["trend_start"]:
            # Always store as date only (YYYY-MM-DD format)
            if hasattr(user_data["trend_start"], "date"):
                # If it's a datetime, get just the date part
                user_data["trend_start"] = user_data["trend_start"].date().isoformat()
            elif hasattr(user_data["trend_start"], "isoformat"):
                # If it's already a date object, use isoformat directly
                user_data["trend_start"] = user_data["trend_start"].isoformat()

    # Save to JSON file
    with open(json_path, "w") as f:
        json.dump(users_data, f, indent=2)


def get_current_user_data() -> dict:
    """
    Get the current user's data from the users dictionary.

    Returns:
        dict: Current user's data including height, target, measure_types, etc.
        Returns empty dict if no user is selected.
    """
    if not hasattr(st.session_state, "user_name") or not st.session_state.user_name:
        return {}

    users_dict = load_users_dict()
    if st.session_state.user_name in users_dict:
        return users_dict[st.session_state.user_name]

    return {}


def get_user_measure_types(user_name: str) -> list:
    """
    Get the measure types for a specific user.

    Args:
        user_name (str): Name of the user

    Returns:
        list: List of measure types for the user
    """
    # Load user database directly from JSON as dictionary
    users_dict = load_users_dict()

    if not users_dict or user_name not in users_dict:
        return []

    # Get measure_types from the user data
    user_data = users_dict[user_name]
    measure_types = user_data.get("measure_types", [])

    # If measure_types is stored as a string (JSON), parse it
    if isinstance(measure_types, str):
        try:
            measure_types = json.loads(measure_types)
        except json.JSONDecodeError:
            measure_types = []

    return measure_types if measure_types else []


def save_user_measure_types(user_name: str, measure_types: list) -> None:
    """
    Save updated measure types for a user.

    Args:
        user_name: Name of the user
        measure_types: List of measure type dictionaries to save
    """
    users_dict = load_users_dict()

    if user_name in users_dict:
        users_dict[user_name]["measure_types"] = measure_types
        save_users_dict_to_json(users_dict)


def add_user_measure_types(
    measurements: dict,
    data_source: str = "withings",
) -> list:
    """
    Add new measure types to user's configuration based on incoming measurements.

    Args:
        measurements: Dictionary of incoming measurements
        data_source: Source of the data ("withings", "manual", etc.)

    Returns:
        List of newly added measure type names
    """

    # Load user's current measure types
    user_measure_types = get_user_measure_types(st.session_state.user_name)

    # Create a mapping of measure names to their decimal precision
    user_measure_decimals = {
        measure_type["name"].lower().replace(" ", "_"): measure_type["decimals"]
        for measure_type in user_measure_types
    }

    new_measure_types_added = []
    new_measure_names = []  # Track the actual measure names (not display names)

    for measure_name in measurements.keys():
        if measure_name not in user_measure_decimals:
            # Get unit and decimals from appropriate config based on data source
            if data_source == "withings":
                from withings.withings import withings_client

                display_name, unit, decimals = withings_client.get_measure_type_config(
                    measure_name
                )
            else:
                # Default fallback for other data sources
                display_name = measure_name.replace("_", " ").title()
                unit, decimals = "kg", 1

            new_measure_type = {
                "name": display_name,
                "unit": unit,
                "decimals": decimals,
            }

            # Add to user's measure types
            user_measure_decimals[measure_name] = decimals
            user_measure_types.append(new_measure_type)
            new_measure_types_added.append(display_name)
            new_measure_names.append(measure_name)  # Track the measure name

    # Save updated user configuration if new measure types were added
    if new_measure_types_added:
        save_user_measure_types(st.session_state.user_name, user_measure_types)

        # Add new columns to session state database
        for measure_name in new_measure_names:
            data.add_measure_column(measure_name)

    return new_measure_types_added
