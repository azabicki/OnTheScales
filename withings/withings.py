"""
Simplified Withings integration module.
Consolidates all core functionality into a single, elegant module.
"""

import os
import json
import time
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple, Set
from urllib.parse import urlencode
import functions.user as user
import functions.data as data


# =============================================================================
# CONFIGURATION
# =============================================================================


class WithingsConfig:
    """Configuration settings for Withings integration."""

    # API endpoints
    AUTHORIZE_URL = "https://account.withings.com/oauth2_user/authorize2"
    TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
    BASE_URL = "https://wbsapi.withings.net"

    # Settings
    TOKEN_REFRESH_BUFFER_MINUTES = 15
    DEFAULT_DATE_RANGE_DAYS = 14
    MAX_DATE_RANGE_DAYS = 365
    ROUND_DECIMALS = 2
    DEFAULT_FAT_PERCENTAGE = 25.0

    # Measure types
    MEASURE_TYPES = {
        1: {
            "name": "Weight",
            "unit": "kg",
            "decimals": 2,
        },
        5: {
            "name": "Fat free",
            "unit": "kg",
            "decimals": 2,
        },
        8: {
            "name": "Fat",
            "unit": "kg",
            "decimals": 2,
        },
        76: {
            "name": "Muscle",
            "unit": "kg",
            "decimals": 2,
        },
        77: {
            "name": "Water",
            "unit": "kg",
            "decimals": 2,
        },
        88: {
            "name": "Bone",
            "unit": "kg",
            "decimals": 2,
        },
        170: {
            "name": "Visceral fat",
            "unit": "AU",
            "decimals": 1,
        },
        227: {
            "name": "Metabolic age",
            "unit": "years",
            "decimals": 0,
        },
    }


# =============================================================================
# CREDENTIALS & TOKEN MANAGEMENT
# =============================================================================


def get_withings_credentials() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get Withings API credentials from Streamlit secrets.

    Returns:
        Tuple of (client_id, client_secret, redirect_uri) or (None, None, None)
    """
    try:
        secrets = st.secrets["withings"]
        return (
            secrets.get("client_id"),
            secrets.get(
                "secret"
            ),  # Note: secrets file uses "secret" not "client_secret"
            secrets.get(
                "callback_uri"
            ),  # Note: secrets file uses "callback_uri" not "redirect_uri"
        )
    except (KeyError, AttributeError):
        return None, None, None


def load_user_token(user_name: str) -> Optional[Dict]:
    """
    Load user's Withings token from file.

    Args:
        user_name: Name of the user

    Returns:
        Token data dictionary or None if not found
    """
    token_file = f"data/tokens/withings_{user_name}.json"

    try:
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass

    return None


def save_user_token(user_name: str, token_data: Dict) -> None:
    """
    Save user's Withings token to file.

    Args:
        user_name: Name of the user
        token_data: Token data to save
    """
    token_file = f"data/tokens/withings_{user_name}.json"

    try:
        os.makedirs("data/tokens", exist_ok=True)
        with open(token_file, "w") as f:
            json.dump(token_data, f, indent=2)
    except IOError:
        st.error("Failed to save Withings token")


def delete_user_token(user_name: str) -> bool:
    """
    Delete user's Withings token.

    Args:
        user_name: Name of the user

    Returns:
        True if deleted successfully
    """
    token_file = f"data/tokens/withings_{user_name}.json"

    try:
        if os.path.exists(token_file):
            os.remove(token_file)
        return True
    except IOError:
        return False


def is_token_expiring_soon(token_data: Dict) -> bool:
    """
    Check if token is expiring soon.

    Args:
        token_data: Token data dictionary

    Returns:
        True if token expires within buffer time
    """
    if "expires_at" not in token_data:
        return True

    buffer_seconds = WithingsConfig.TOKEN_REFRESH_BUFFER_MINUTES * 60
    return token_data["expires_at"] - time.time() < buffer_seconds


def _check_rate_limit(user_name: str) -> bool:
    """
    Check if we're rate-limited for token refresh.
    Withings requires 10 seconds between refresh attempts.

    Args:
        user_name: Name of the user

    Returns:
        True if we can proceed, False if rate-limited
    """
    last_refresh_key = f"last_refresh_attempt_{user_name}"

    if hasattr(st.session_state, last_refresh_key):
        last_attempt = getattr(st.session_state, last_refresh_key)
        time_since_last = time.time() - last_attempt

        if time_since_last < 10:
            # Only log once to avoid spam during reruns
            log_key = f"{last_refresh_key}_logged"
            if not hasattr(st.session_state, log_key):
                wait_time = 10 - int(time_since_last)
                print(f"Rate limit: Must wait {wait_time} more seconds before retrying")
                setattr(st.session_state, log_key, True)
            return False

    # Record this refresh attempt and clear logged flag
    setattr(st.session_state, last_refresh_key, time.time())
    log_key = f"{last_refresh_key}_logged"
    if hasattr(st.session_state, log_key):
        delattr(st.session_state, log_key)

    return True


def refresh_token_if_needed(
    user_name: str, force_refresh: bool = False
) -> Dict[str, any]:
    """
    Refresh token if it's expiring soon.

    Args:
        user_name: Name of the user
        force_refresh: Force refresh even if not expiring

    Returns:
        True if token is valid (refreshed or not expiring)
    """
    # Load and validate token
    token_data = load_user_token(user_name)
    if not token_data:
        return {"result": False, "message": "Token not found."}

    # Check if refresh is needed
    if not is_token_expiring_soon(token_data) and not force_refresh:
        return {"result": True, "message": "Token is not expiring soon."}

    # Check rate limiting
    if not _check_rate_limit(user_name):
        return {
            "result": False,
            "message": "Rate limit hit. Wait 10 seconds before retrying.",
        }

    # Get API credentials
    client_id, client_secret, redirect_uri = get_withings_credentials()
    if not all([client_id, client_secret, redirect_uri]):
        return {"result": False, "message": "API credentials not found."}

    # Make API request
    try:
        response = requests.post(
            WithingsConfig.TOKEN_URL,
            data={
                "action": "requesttoken",
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": token_data["refresh_token"],
            },
        )

        if response.status_code != 200:
            return {
                "result": False,
                "message": f"Token refresh failed: HTTP {response.status_code}.",
            }

        # Handle Withings API response
        data = response.json()
        status = data.get("status", 0)

        # Check for API errors (status != 0 means error)
        if status == 503:
            return {
                "result": False,
                "message": "Invalid refresh token. Re-authentication required.",
            }

        if status != 0:
            return {
                "result": False,
                "message": f"Withings API error {status}: {data.get('error')}",
            }

        # Extract and save new token
        if "body" not in data or "expires_in" not in data["body"]:
            return {"result": False, "message": "Invalid token response structure."}

        new_token = data["body"]
        new_token["expires_at"] = time.time() + new_token["expires_in"]
        save_user_token(user_name, new_token)
        return {"result": True, "message": "Token refreshed successfully."}

    except Exception as e:
        return {"result": False, "message": f"Token refresh exception: {e}"}


# =============================================================================
# API CALLS
# =============================================================================


def _make_api_request(
    user_name: str, endpoint: str, params: Dict = None
) -> Optional[Dict]:
    """
    Make authenticated API request to Withings.

    Args:
        user_name: Name of the user
        endpoint: API endpoint
        params: Request parameters

    Returns:
        API response data or None if failed
    """
    refresh_result = refresh_token_if_needed(user_name)
    if not refresh_result["result"]:
        return None

    token_data = load_user_token(user_name)
    if not token_data:
        return None

    try:
        response = requests.get(
            f"{WithingsConfig.BASE_URL}{endpoint}",
            params={**(params or {}), "access_token": token_data["access_token"]},
        )

        if response.status_code == 200:
            return response.json()["body"]
    except (requests.RequestException, KeyError, json.JSONDecodeError):
        pass

    return None


def get_measurements(
    user_name: str, start_date: datetime, end_date: datetime
) -> Optional[Dict]:
    """
    Get measurements from Withings API.

    Args:
        user_name: Name of the user
        start_date: Start date for measurements
        end_date: End date for measurements

    Returns:
        Measurements data or None if failed
    """
    params = {
        "action": "getmeas",
        "startdate": int(start_date.timestamp()),
        "enddate": int(end_date.timestamp()),
    }

    return _make_api_request(user_name, "/measure", params)


# =============================================================================
# DATA PROCESSING
# =============================================================================


def process_measurements_data(measurements_data: Dict, user_name: str) -> pd.DataFrame:
    """
    Process raw measurements data into a clean DataFrame.

    Args:
        measurements_data: Raw measurements data from API
        user_name: Name of the user

    Returns:
        Processed DataFrame
    """
    if not measurements_data or "measuregrps" not in measurements_data:
        return pd.DataFrame()

    # Get measure types
    measure_type_map = WithingsConfig.MEASURE_TYPES
    processed_data = []

    for group in measurements_data["measuregrps"]:
        timestamp = group["date"]
        measures = group["measures"]

        # Create row data
        row_data = {"date": datetime.fromtimestamp(timestamp)}

        # Process each measure in the group
        for measure in measures:
            measure_type = measure["type"]
            value = measure["value"] * (10 ** measure["unit"])

            # Map Withings measure types to user's measure types
            if measure_type in measure_type_map:
                var_name = (
                    measure_type_map[measure_type]["name"].lower().replace(" ", "_")
                )
                row_data[var_name] = round(
                    value, measure_type_map[measure_type]["decimals"]
                )
            else:
                print(f"WARNING: Unknown measure type {measure_type} - skipping")

        if "weight" in row_data:
            processed_data.append(row_data)

    return pd.DataFrame(processed_data)


# =============================================================================
# IMPORT TRACKING
# =============================================================================


def get_imported_timestamps(user_name: str) -> Set[int]:
    """
    Get set of Unix timestamps that have been imported from Withings.

    Args:
        user_name: Name of the user

    Returns:
        Set of imported Unix timestamps
    """
    # Get from user's imported_dates in users.json
    users_dict = user.load_users_dict()
    if user_name in users_dict:
        return set(users_dict[user_name].get("imported_dates", []))
    return set()


def save_imported_timestamps(user_name: str, timestamps: Set[int]) -> None:
    """
    Save imported timestamps to user's data.

    Args:
        user_name: Name of the user
        timestamps: Set of Unix timestamps
    """
    users_dict = user.load_users_dict()
    if user_name in users_dict:
        users_dict[user_name]["imported_dates"] = list(timestamps)
        user.save_users_dict_to_json(users_dict)


def _has_additional_measure_types(row: pd.Series, user_name: str) -> bool:
    """Check if row has additional measure types not in existing data."""
    import streamlit as st
    import functions.user as user

    # Get measure types from row
    row_measure_types = set(row.index) - {"date", "imported"}

    # Get user's configured measure types
    user_measure_types = user.get_user_measure_types(user_name)
    user_measure_type_names = {
        m["name"].lower().replace(" ", "_") for m in user_measure_types
    }

    # Get existing measure types from database
    existing_measure_types = set()
    if hasattr(st.session_state, "db") and not st.session_state.db.empty:
        row_date = row["date"].date()
        existing_row = st.session_state.db[
            st.session_state.db["date"].dt.date == row_date
        ]
        if not existing_row.empty:
            # Convert columns to set, then subtract
            cols_to_check = set(existing_row.columns) - {
                "date",
                "timestamp",
                "imported",
            }
            existing_measure_types = {
                col for col in cols_to_check if not existing_row[col].isna().all()
            }

    # Check for new measure types
    new_measure_types = (
        row_measure_types - user_measure_type_names - existing_measure_types
    )
    return len(new_measure_types) > 0


def import_withings_data(
    user_name: str, selected_data: pd.DataFrame, import_unknown: bool
) -> Dict[str, any]:
    """
    Import selected Withings data to the main database.

    Args:
        user_name: Name of the user
        selected_data: DataFrame with selected measurements
        import_unknown: Whether to import unknown measurements
    Returns:
        Dictionary with 'count' and 'new_measure_types' list
    """
    if selected_data.empty:
        return {"count": 0, "new_measure_types": []}

    # Get already imported timestamps
    imported_timestamps = get_imported_timestamps(user_name)

    # Filter out already imported data
    new_timestamps = set()
    new_measurements = []

    for _, row in selected_data.iterrows():
        timestamp = int(row["date"].timestamp())

        # Always include if not previously imported
        if timestamp not in imported_timestamps:
            new_timestamps.add(timestamp)
            new_measurements.append(row)
        # If previously imported and import_unknown is enabled, check if data is different
        elif import_unknown and timestamp in imported_timestamps:
            # Check if the new data has additional measure types not in existing data
            if _has_additional_measure_types(row, user_name):
                new_timestamps.add(timestamp)
                new_measurements.append(row)

    if not new_measurements:
        return {"count": 0, "new_measure_types": []}

    # Add new measurements to user's database
    users_measure_types = user.get_user_measure_types(user_name)
    user_measure_type_names = {
        m["name"].lower().replace(" ", "_") for m in users_measure_types
    }

    # Pre-compute unit mappings
    withings_unit_map = {
        measure_type["name"].lower().replace(" ", "_"): measure_type["unit"]
        for measure_type in WithingsConfig.MEASURE_TYPES.values()
    }
    user_unit_map = {
        measure_type["name"].lower().replace(" ", "_"): measure_type["unit"]
        for measure_type in users_measure_types
    }

    for measurement in new_measurements:
        measurements_dict = {
            col: val
            for col, val in measurement.items()
            if col != "date" and (import_unknown or col in user_measure_type_names)
        }

        # Convert units if necessary
        for col, val in measurements_dict.items():
            if val is not None:
                withings_unit = withings_unit_map.get(col)
                user_unit = user_unit_map.get(col)

                # Convert from kg to % if necessary
                if withings_unit == "kg" and user_unit == "%":
                    measurements_dict[col] = val / measurements_dict["weight"] * 100

        data.add_update(
            measurement["date"].date(),
            measurements_dict,
            suppress_feedback=True,
            data_source="withings",
        )

    # Save imported timestamps
    save_imported_timestamps(user_name, imported_timestamps | new_timestamps)

    # Detect new measure types that will be added
    new_measure_types = []

    # Find new measure types
    if import_unknown:
        for measure_name in set(selected_data.columns) - {"date", "imported"}:
            if measure_name not in user_measure_type_names:
                # Get display name from Withings config
                display_name, _, _ = withings_client.get_measure_type_config(
                    measure_name
                )
                new_measure_types.append(display_name)

    return {"count": len(new_measurements), "new_measure_types": new_measure_types}


def sync_withings_data(
    user_name: str,
    selected_data: pd.DataFrame,
    loaded_df: pd.DataFrame,
    import_unknown: bool,
) -> Dict[str, any]:
    """
    Sync Withings data with the main database - import selected and delete deselected.

    Only handles dates visible in loaded_df to prevent ghost deletions.

    Args:
        user_name: Name of the user
        selected_data: DataFrame with selected measurements to import (checked boxes)
        loaded_df: DataFrame with all loaded Withings data (visible in UI)
        import_unknown: Whether to import unknown measurements

    Returns:
        Dictionary with 'imported', 'deleted' counts and 'new_measure_types' list
    """

    # Get timestamps from loaded dataframe (visible data only)
    loaded_timestamps = set()
    for _, row in loaded_df.iterrows():
        timestamp = int(row["date"].timestamp())
        loaded_timestamps.add(timestamp)

    # Get timestamps user wants to import (checked boxes)
    selected_timestamps = set()
    for _, row in selected_data.iterrows():
        timestamp = int(row["date"].timestamp())
        selected_timestamps.add(timestamp)

    # Get currently imported timestamps
    current_imported = get_imported_timestamps(user_name)

    # Timestamps to DELETE: in loaded view, previously imported, but NOW unchecked
    timestamps_to_delete = (loaded_timestamps & current_imported) - selected_timestamps

    # Delete deselected entries from database
    deleted_count = 0
    for timestamp in timestamps_to_delete:
        # Convert timestamp back to date
        delete_date = datetime.fromtimestamp(timestamp).date()
        # Check if entry exists in database before deleting
        try:
            if hasattr(st.session_state, "db") and not st.session_state.db.empty:
                if any(st.session_state.db["date"].dt.date == delete_date):
                    data.delete(delete_date, suppress_feedback=True)
                    deleted_count += 1
        except (AttributeError, KeyError):
            # If session state is not available, skip deletion
            pass

    # Import selected data
    import_result = import_withings_data(user_name, selected_data, import_unknown)

    # Update imported timestamps: remove deleted from loaded view, add imported
    new_imported = (current_imported - timestamps_to_delete) | selected_timestamps
    save_imported_timestamps(user_name, new_imported)

    # Cleanup empty measure types after deletion
    if deleted_count > 0:
        cleanup_empty_measures(user_name)

    return {
        "synced": import_result["count"],
        "deleted": deleted_count,
        "new_measure_types": import_result["new_measure_types"],
    }


def cleanup_empty_measures(user_name: str) -> None:
    """
    Remove measure types from user configuration if they have no values in the database.

    Called after deletions to clean up measures that no longer have any data.

    Args:
        user_name: Name of the user
    """
    # Get user's measure types
    user_measure_types = user.get_user_measure_types(user_name)

    # Load user's database
    if not hasattr(st.session_state, "db") or st.session_state.db.empty:
        return

    user_db = st.session_state.db

    # Check each measure type
    measures_to_remove = []
    for measure_type in user_measure_types:
        measure_name = measure_type["name"].lower().replace(" ", "_")

        # Skip 'date' column and check if column exists
        if measure_name == "date" or measure_name not in user_db.columns:
            continue

        # Check if measure has any non-null values
        has_values = user_db[measure_name].notna().any()

        if not has_values:
            measures_to_remove.append(measure_type)

    # Remove empty measures from user configuration
    if measures_to_remove:
        updated_measure_types = [
            mt for mt in user_measure_types if mt not in measures_to_remove
        ]
        user.save_user_measure_types(user_name, updated_measure_types)

        # Remove columns from database
        for measure_type in measures_to_remove:
            measure_name = measure_type["name"].lower().replace(" ", "_")
            data.delete_measure_column(measure_name)


def prepare_data_for_display(withings_df: pd.DataFrame, user_name: str) -> pd.DataFrame:
    """
    Prepare Withings DataFrame for display with synced status.

    Checks both imported_dates list and actual presence in user's CSV database
    to ensure accurate synced status.

    Args:
        withings_df: DataFrame with Withings data
        user_name: Name of the user

    Returns:
        DataFrame with synced status column
    """
    if withings_df.empty:
        return withings_df

    # Get imported timestamps from users.json
    imported_timestamps = get_imported_timestamps(user_name)

    # Load user's actual database to verify presence
    user_db = (
        data.load_db()
        if hasattr(st.session_state, "user_name")
        and st.session_state.user_name == user_name
        else pd.DataFrame()
    )

    # Add import status column
    display_df = withings_df.copy()

    def check_imported_status(row):
        timestamp = int(row["date"].timestamp())

        # Must be in imported_timestamps list
        if timestamp not in imported_timestamps:
            return False

        # Also verify entry exists in actual database
        if user_db.empty:
            return False

        row_date = row["date"].date()
        matching_rows = user_db[user_db["date"].dt.date == row_date]

        # Entry exists in database
        return not matching_rows.empty

    display_df["synced"] = display_df.apply(check_imported_status, axis=1)

    return display_df


# =============================================================================
# CONNECTION STATUS & AUTHENTICATION
# =============================================================================


def get_connection_status(user_name: str) -> Dict:
    """
    Get connection status for a user.

    Args:
        user_name: Name of the user

    Returns:
        Connection status dictionary
    """
    client_id, client_secret, redirect_uri = get_withings_credentials()

    if not all([client_id, client_secret, redirect_uri]):
        return {
            "configured": False,
            "connected": False,
            "message": "Withings API credentials not configured",
            "token_status": {"valid": False},
            "token_data": None,
        }

    token_data = load_user_token(user_name)
    if not token_data:
        return {
            "configured": True,
            "connected": False,
            "message": "Not connected to Withings",
            "token_status": {"valid": False},
            "token_data": None,
        }

    # Check token status and refresh if needed
    if is_token_expiring_soon(token_data):
        refresh_result = refresh_token_if_needed(user_name)
        if not refresh_result["result"]:
            # Refresh failed, but still return token data so user can see status
            # and manually try to refresh or re-authenticate
            return {
                "configured": True,
                "connected": False,
                "message": f"Token expired and refresh failed: {refresh_result['message']}",
                "token_status": {"valid": False},
                "token_data": token_data,  # Still provide token data
            }

        # Refresh succeeded - reload token data to get updated expiration
        token_data = load_user_token(user_name)

    # Token is valid (either was already valid or just refreshed)
    return {
        "configured": True,
        "connected": True,
        "message": "Connected to Withings",
        "token_status": {"valid": True},
        "token_data": token_data,
    }


def get_auth_url(user_name: str) -> str:
    """
    Get authorization URL for OAuth flow.

    Args:
        user_name: Name of the user

    Returns:
        Authorization URL
    """
    client_id, client_secret, redirect_uri = get_withings_credentials()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "user.metrics",
        "state": f"withings_auth_{user_name}",
    }

    return f"{WithingsConfig.AUTHORIZE_URL}?{urlencode(params)}"


def handle_oauth_callback(user_name: str, code: str) -> bool:
    """
    Handle OAuth callback and exchange code for token.

    Args:
        user_name: Name of the user
        code: Authorization code from OAuth callback

    Returns:
        True if token exchange successful
    """
    client_id, client_secret, redirect_uri = get_withings_credentials()

    if not all([client_id, client_secret, redirect_uri]):
        return False

    try:
        response = requests.post(
            WithingsConfig.TOKEN_URL,
            data={
                "action": "requesttoken",
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )

        if response.status_code == 200:
            token_data = response.json()["body"]
            token_data["expires_at"] = time.time() + token_data["expires_in"]
            save_user_token(user_name, token_data)
            return True
    except (requests.RequestException, KeyError, json.JSONDecodeError):
        pass

    return False


# =============================================================================
# MAIN CLIENT INTERFACE
# =============================================================================


class WithingsClient:
    """
    Simplified Withings client that provides a clean interface.
    """

    def __init__(self):
        self.config = WithingsConfig()

    def get_connection_status(self, user_name: str) -> Dict:
        """Get connection status for a user."""
        return get_connection_status(user_name)

    def get_authorization_url(self, user_name: str) -> str:
        """Get authorization URL for OAuth flow."""
        return get_auth_url(user_name)

    def process_authorization_code(self, code: str, user_name: str) -> bool:
        """Process OAuth authorization code."""
        return handle_oauth_callback(user_name, code)

    def refresh_token(self, user_name: str, force_refresh: bool = False) -> Dict:
        """Manually refresh user's token."""
        return refresh_token_if_needed(user_name, force_refresh)

    def disconnect_user(self, user_name: str) -> bool:
        """Disconnect user from Withings."""
        return delete_user_token(user_name)

    def load_withings_data(
        self, user_name: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Load Withings data for a user."""
        measurements_data = get_measurements(user_name, start_date, end_date)
        if not measurements_data:
            return None

        return process_measurements_data(measurements_data, user_name)

    def sync_data(
        self,
        user_name: str,
        selected_data: pd.DataFrame,
        loaded_df: pd.DataFrame,
        import_unknown: bool,
    ) -> Dict[str, int]:
        """Sync Withings data - sync selected and delete deselected."""
        return sync_withings_data(user_name, selected_data, loaded_df, import_unknown)

    def prepare_data_for_display(
        self, withings_df: pd.DataFrame, user_name: str
    ) -> pd.DataFrame:
        """Prepare data for display with synced status."""
        return prepare_data_for_display(withings_df, user_name)

    def get_measure_type_config(self, measure_name: str) -> Tuple[str, str, int]:
        """
        Get display name, unit and decimal precision for a measure type from Withings config.

        Args:
            measure_name: Name of the measure type (e.g., "weight", "fat")

        Returns:
            Tuple of (display_name, unit, decimals)
        """
        # Look up in Withings config
        for measure_type in WithingsConfig.MEASURE_TYPES.values():
            if measure_type["name"].lower().replace(" ", "_") == measure_name:
                return (
                    measure_type["name"],
                    measure_type["unit"],
                    measure_type["decimals"],
                )

        # Fallback defaults if not found in Withings config
        return "Unknown", "kg", 1


# Global client instance
withings_client = WithingsClient()
