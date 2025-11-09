import streamlit as st
import math
import numpy as np
import pandas as pd
from datetime import datetime, time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression as LinReg
import functions.user as user

# dictionary of colors
clrs = {
    "weight": "#2E4057",
    "fat": "#EEAA49",
    "water": "#1098F7",
    "muscle": "#EF5B5B",
    "trend": "#66a3FF",
    "prediction": "#FF5757",
}


def get_target_weight() -> float:
    """
    Get the current user's target weight.

    Returns:
        float: Target weight, or 0 if no user is selected.
    """
    user_data = user.get_current_user_data()
    return user_data.get("target", 0)


def gaussian_weighted_mean(x):
    if len(x) == 0:
        return np.nan
    n = len(x)
    center = (n - 1) / 2
    positions = np.arange(n)
    sigma = n / 4
    weights = np.exp(-((positions - center) ** 2) / (2 * sigma**2))
    weights = weights / weights.sum()
    return np.average(x, weights=weights)


def main() -> go.Figure | None:
    """
    Main function to generate the primary weight tracking figure.

    Returns:
        go.Figure | None: Plotly figure object containing the weight tracking visualization,
                         or None if no measurements are stored.
    """

    # return if no measurements stored
    if st.session_state.db.shape[0] == 0:
        return None

    # marker/line mode
    mode = (
        "markers+lines"
        if st.session_state["fig_main_style"] == "both"
        else st.session_state["fig_main_style"]
    )

    # if only one measurement, use markers
    if st.session_state.db.shape[0] == 1:
        mode = "markers"

    # instantiate figure
    fig = go.Figure()

    # add target weight
    fig.add_trace(
        go.Scatter(
            x=[
                list(st.session_state.db["date"])[0],
                list(st.session_state.db["date"])[-1],
            ],
            y=[get_target_weight(), get_target_weight()],
            showlegend=True,
            hoverinfo="skip",
            name="target",
            mode="lines",
            line_color="#ff4444",
            line_width=2,
        ),
    )

    # add _weight_
    fig.add_trace(
        go.Scatter(
            x=st.session_state.db["date"],
            y=st.session_state.db["weight"],
            showlegend=True,
            name="weight",
            mode=mode,
            line_width=3,
            line_color=clrs["weight"],
            marker_size=6,
        ),
    )

    # Get selected smoothing method from segmented control
    smoothing_method = st.session_state.get("fig_main_smoothing", "5-day EMA")

    db_with_date_index = st.session_state.db.set_index("date")
    import numpy as np

    # Add selected smoothing line
    if smoothing_method is not None:
        if smoothing_method == "5-day EMA":
            # Calculate 5-day exponentially weighted average
            smoothed_weight = (
                db_with_date_index["weight"]
                .ewm(halflife="5D", times=db_with_date_index.index)
                .mean()
                .round(2)
            )

        elif smoothing_method == "10-day cMA":
            # Calculate centered moving average with Gaussian weighting
            smoothed_weight = (
                db_with_date_index["weight"]
                .rolling(window="10D", center=True, min_periods=1)
                .apply(gaussian_weighted_mean, raw=True)
                .round(2)
            )

        elif smoothing_method == "Spline" and len(st.session_state.db) > 3:
            # Calculate smoothing spline
            from scipy.interpolate import UnivariateSpline

            smooth = 0.3
            dates_numeric = st.session_state.db["date"].astype(np.int64) / 10**9
            weights = st.session_state.db["weight"].values

            spline = UnivariateSpline(
                dates_numeric, weights, s=len(dates_numeric) * smooth, k=3
            )

            # Create dense date grid for interpolation (add points in gaps >= 7 days)
            dates_for_spline = [dates_numeric[0]]
            dates_obj_for_spline = [st.session_state.db["date"].iloc[0]]

            for i in range(1, len(dates_numeric)):
                gap_days = (dates_numeric[i] - dates_numeric[i - 1]) / (24 * 3600)

                if gap_days >= 7:
                    num_interpolated = int(gap_days) - 1
                    interpolated_dates = np.linspace(
                        dates_numeric[i - 1], dates_numeric[i], num_interpolated + 2
                    )[1:-1]
                    dates_for_spline.extend(interpolated_dates)

                    for d in interpolated_dates:
                        dates_obj_for_spline.append(pd.Timestamp(d, unit="s"))

                dates_for_spline.append(dates_numeric[i])
                dates_obj_for_spline.append(st.session_state.db["date"].iloc[i])

            dates_for_spline = np.array(dates_for_spline)
            smoothed_weight = spline(dates_for_spline).round(2)

        # plot smoothed weight
        fig.add_trace(
            go.Scatter(
                x=(
                    dates_obj_for_spline
                    if smoothing_method == "Spline"
                    else st.session_state.db["date"]
                ),
                y=smoothed_weight,
                showlegend=True,
                name=smoothing_method,
                mode="lines",
                line_width=1.5,
                line_color="#54BE44",
                line_dash="solid",
            ),
        )

    # set some layout properties
    fig.update_layout(
        # height of figure
        height=420,
        # hovering
        hovermode="x unified",
        hoverlabel=dict(font_size=12, bgcolor="#fefefe"),
        hoverdistance=1,
        # title
        title=dict(
            text="Weight Chronicles",
            automargin=True,
        ),
        # margin
        margin=dict(l=0, r=0, t=0, b=0),
        # legend
        legend=dict(
            orientation="v",
            borderwidth=1,
            bordercolor="#aaaaaa",
            bgcolor="#fefefe",
            xanchor="right",
            x=1,
            itemclick=False,
            traceorder="reversed",
        ),
    )

    # Set x/y-axes properties
    fig.update_xaxes(
        type="date",
        showgrid=True,
        range=(
            list(st.session_state.db["date"])[0] - pd.DateOffset(weeks=1),
            list(st.session_state.db["date"])[-1] + pd.DateOffset(weeks=1),
        ),
    )
    fig.update_yaxes(
        ticksuffix=" kg",
    )

    # Add range_selector
    fig.update_xaxes(
        rangeselector=dict(
            bgcolor="#ffffff",
            buttons=list(
                [
                    dict(count=1, label="-1mon", step="month", stepmode="backward"),
                    dict(count=2, label="-2mos", step="month", stepmode="backward"),
                    dict(count=3, label="-3mos", step="month", stepmode="backward"),
                    dict(count=6, label="-6mos", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            ),
            x=1,
            xanchor="right",
            y=1.05,
            yanchor="middle",
        ),
    )

    return fig


def trend() -> tuple[go.Figure | None, float]:
    """
    Function to calculate and visualize weight trends and predictions.

    Performs linear regression on weight data to determine trends, creates a
    visualization of actual weights, trend lines, and predictions for future
    weight based on current trends.

    Returns:
        tuple[go.Figure|None, float]: A tuple containing:
            - A plotly figure object with the trend visualization, or None if no data
            - The calculated trend coefficient (slope of regression line)
    """

    # return if no measurements stored
    if st.session_state.db.shape[0] <= 1:
        return None, 0

    # instantiate figure
    fig = go.Figure()

    # get dates for x_axis based on trend_how
    if st.session_state.trend_how == "start date":
        # get date
        x_data = [
            datetime.combine(st.session_state.trend_start, time(0, 0, 0)),
            list(st.session_state.db["date"])[-1],
        ]

    elif st.session_state.trend_how == "date range":
        # get weeks - calculate from today, not from last measurement
        weeks = int(st.session_state.trend_range)
        today = pd.Timestamp.now()
        x_data = [
            today - pd.Timedelta(weeks=weeks),
            today,
        ]
    else:
        x_data = [
            list(st.session_state.db["date"])[0],
            list(st.session_state.db["date"])[-1],
        ]

    # filter data
    idx_db = st.session_state.db["date"][st.session_state.db["date"] >= x_data[0]].index
    db_data = st.session_state.db.iloc[idx_db]

    # check if there's insufficient data within the selected range
    if (
        st.session_state.trend_how in ["start date", "date range"]
        and db_data.shape[0] <= 1
    ):
        return None, 0

    # lin. reg. of relevant data
    X = db_data["date"].values.reshape(-1, 1)
    y = db_data["weight"].values
    LR = LinReg().fit(X, y)
    trnd = LR.coef_[0].item()
    ntrcpt = LR.intercept_

    # fit of actual data
    y_fit = LR.predict(db_data["date"].values.astype(int).reshape(-1, 1))
    db_data = db_data.assign(fit=y_fit)

    # find weeks to be predicted (=w2p) - depending on if trend is going towards target
    target_in_past = False  # Initialize flag
    if (trnd < 0 and get_target_weight() > db_data["weight"].iloc[-1]) or (
        trnd > 0 and get_target_weight() < db_data["weight"].iloc[-1]
    ):
        # trend away from target: predict until today
        today = pd.Timestamp.now()
        t_diff = today - db_data["date"].iloc[-1]
        w2p = max(0, math.ceil(t_diff / np.timedelta64(1, "W")))

        # set target_flags
        target_reached = False
        target_late = False

    else:
        # calculate weeks until target is reached
        date_on_target = pd.to_datetime(
            (get_target_weight() - ntrcpt) / trnd, unit="ns"
        )
        today = pd.Timestamp.now()

        # Check if target was reached in the past
        target_in_past = date_on_target < today
        if target_in_past:
            # Target reached in past, show until today + 7 days
            t_diff = (today + pd.Timedelta(days=7)) - db_data["date"].iloc[-1]
            w2p = max(0, math.ceil(t_diff / np.timedelta64(1, "W")))
            target_reached = True
            target_late = False
        else:
            # Target in future
            # Check if target is more than 6 months from TODAY
            six_months_from_today = today + pd.Timedelta(weeks=26)

            if date_on_target <= today + pd.Timedelta(days=7):
                # Target within next 7 days, show until today + 7 days
                t_diff = (today + pd.Timedelta(days=7)) - db_data["date"].iloc[-1]
                w2p = max(0, math.ceil(t_diff / np.timedelta64(1, "W")))
                target_reached = True
                target_late = False
            elif date_on_target > six_months_from_today:
                # Target more than 6 months away, cap at 6 months from TODAY
                t_diff = six_months_from_today - db_data["date"].iloc[-1]
                w2p = max(0, math.ceil(t_diff / np.timedelta64(1, "W")))
                target_reached = True
                target_late = True
            else:
                # Target between 7 days and 6 months from today
                t_diff = date_on_target - db_data["date"].iloc[-1]
                w2p = max(0, math.ceil(t_diff / np.timedelta64(1, "W")))
                target_reached = True
                target_late = False

    # predict weight
    if w2p > 0:
        pred_date = pd.date_range(
            db_data["date"].iloc[-1] + pd.Timedelta(days=1),
            db_data["date"].iloc[-1] + pd.Timedelta(weeks=w2p),
            freq="d",
        )
        pred_weight = LR.predict(pred_date.values.astype(int).reshape(-1, 1)).round(2)
        x_range_end = pred_date[-1]
    else:
        # No prediction needed (last measurement is today or later)
        pred_date = pd.DatetimeIndex([])
        pred_weight = []
        x_range_end = pd.Timestamp.now()

    # calculate x-range
    x_range = [
        db_data["date"].iloc[0] - pd.Timedelta(weeks=1),
        x_range_end,
    ]

    # add target weight
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=[get_target_weight(), get_target_weight()],
            hoverinfo="skip",
            name="target",
            mode="lines",
            line_color="#50C878",
            line_width=2,
        )
    )

    # add weight
    fig.add_trace(
        go.Scatter(
            x=db_data["date"],
            y=db_data["weight"],
            name="weight",
            mode="markers",
            marker_size=10,
            marker_color=clrs["weight"],
        )
    )

    # add _FIT_
    fig.add_trace(
        go.Scatter(
            x=db_data["date"],
            y=db_data["fit"],
            hoverinfo="skip",
            name="weight",
            mode="lines",
            line_width=3,
            line_color=clrs["trend"],
        )
    )

    # add _PREDICTION_
    fig.add_trace(
        go.Scatter(
            x=pred_date,
            y=pred_weight[:,],
            name="prediction",
            mode="lines",
            line_width=3,
            line_dash="dash",
            line_color=clrs["prediction"],
        )
    )

    # add _PREDICTION_TEXT_
    if target_reached:
        # find first day [index] of target reached
        if target_late:
            # Calculate actual target date even though prediction is capped
            actual_date_on_target = pd.to_datetime(
                (get_target_weight() - ntrcpt) / trnd, unit="ns"
            )
            str_target = actual_date_on_target.strftime("%d.%m.%y")
            days_to_target = (actual_date_on_target - pd.Timestamp.today()).days
            weeks_to_target = math.ceil(days_to_target / 7)
            text = f"{str_target}<br>({weeks_to_target} weeks)"
            # Use last prediction date for arrow position (x and y)
            pred_target_date = -1
            pred_target_y = pred_weight[pred_target_date]

        else:
            pred_target_date = (
                np.where(pred_weight < get_target_weight())[0][0]
                if trnd < 0
                else np.where(pred_weight > get_target_weight())[0][0]
            )

            str_target = pred_date[pred_target_date].strftime("%d.%m.%y")
            str_days = pred_date[pred_target_date] - pd.Timestamp.today()
            text = f"{str_target}<br>({str_days.days} days)"
            pred_target_y = get_target_weight()

        # text_patch
        fig.add_annotation(
            x=pred_date[pred_target_date],
            y=pred_target_y,
            text=text,
            showarrow=True,
            arrowhead=3,
            yanchor="bottom",
            ay=-80 if trnd < 0 else 80,
            ax=-40,
            borderwidth=1,
            borderpad=7,
            bgcolor="#ffffff",
        )

    # add vertical line at today
    today_timestamp = pd.Timestamp.now()
    fig.add_vline(
        x=today_timestamp,
        line_width=1,
        line_dash="solid",
        line_color="black",
    )

    # add annotation for today line
    fig.add_annotation(
        x=today_timestamp,
        y=0.88,
        yref="paper",
        text="today",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.3,
        arrowwidth=1,
        arrowcolor="black",
        ax=-40,
        ay=-25,
        yanchor="top",
        font=dict(size=10, color="grey"),
        bgcolor="white",
        borderwidth=0,
        borderpad=4,
    )

    # set some layout properties
    fig.update_layout(
        # height of figure
        height=350,
        # turn legend off
        showlegend=False,
        # hovering
        hovermode="x unified",
        hoverlabel=dict(font_size=12, bgcolor="#fefefe"),
        hoverdistance=1,
        # margin
        margin=dict(l=0, r=0, t=0, b=0),
    )

    # set x/y-axes properties
    fig.update_xaxes(
        range=x_range,
        type="date",
        showgrid=True,
    )

    # Constrain y-axis if target was reached in the past
    if target_in_past:
        # Get target weight
        target = get_target_weight()

        # Get range of actual weights only (not predictions)
        weight_min = db_data["weight"].min()
        weight_max = db_data["weight"].max()

        # Calculate the range between target and measurements
        # Add 10% of that range on both sides
        if target > weight_max:
            # Target above measurements
            range_distance = target - weight_min
            y_max = target + range_distance * 0.1
            y_min = weight_min - range_distance * 0.1
        elif target < weight_min:
            # Target below measurements
            range_distance = weight_max - target
            y_max = weight_max + range_distance * 0.1
            y_min = target - range_distance * 0.1
        else:
            # Target between measurements
            range_distance = weight_max - weight_min
            y_max = weight_max + range_distance * 0.1
            y_min = weight_min - range_distance * 0.1

        fig.update_yaxes(
            ticksuffix=" kg",
            range=[y_min, y_max],
        )
    else:
        fig.update_yaxes(
            ticksuffix=" kg",
        )

    return fig, trnd


def body_comp() -> go.Figure | None:
    """
    Function to visualize the body composition over time.

    Creates a plot showing the evolution of various body composition measurements
    (fat, water, and muscle percentages) over time. Can display values either as
    percentages or absolute weights, and optionally include weight and target lines.

    Returns:
        go.Figure | None: Plotly figure object containing the body composition
        visualization, or None if no measurements are stored.
    """

    # return if no measurements stored
    if st.session_state.db.shape[0] == 0:
        return None

    # marker/line/body_comp mode
    mode = (
        "markers+lines"
        if st.session_state["fig_body_comp_style"] == "both"
        else st.session_state["fig_body_comp_style"]
    )
    bc_in_prc = st.session_state["fig_body_comp_type"] == "%"
    show_wgt = st.session_state["fig_body_comp_weight"] == "weight & target"
    second_y = bc_in_prc and show_wgt

    # if only one measurement, use markers
    if st.session_state.db.shape[0] == 1:
        mode = "markers"

    # instantiate figure
    if second_y:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = go.Figure()

    # add composites
    for var in ["fat", "water", "muscle"]:
        # convert into kg?
        if bc_in_prc:
            y = st.session_state.db[var]
        else:
            y = st.session_state.db["weight"] * st.session_state.db[var] / 100
            y = y.round(1)

        # plot
        if second_y:
            fig.add_trace(
                go.Scatter(
                    x=st.session_state.db["date"],
                    y=y,
                    showlegend=True,
                    name=var,
                    mode=mode,
                    marker_size=5,
                    line_width=3,
                    line_color=clrs[var],
                ),
                secondary_y=False,
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=st.session_state.db["date"],
                    y=y,
                    showlegend=True,
                    name=var,
                    mode=mode,
                    marker_size=5,
                    line_width=3,
                    line_color=clrs[var],
                )
            )

    # add _weight_ & _target_
    if st.session_state["fig_body_comp_weight"] == "weight & target":
        if second_y:
            # weight
            fig.add_trace(
                go.Scatter(
                    x=st.session_state.db["date"],
                    y=st.session_state.db["weight"],
                    showlegend=True,
                    name="weight",
                    mode=mode,
                    line_width=1,
                    line_color=clrs["weight"],
                    marker_size=4,
                ),
                secondary_y=bc_in_prc,
            )

            # target
            fig.add_trace(
                go.Scatter(
                    x=[
                        list(st.session_state.db["date"])[0],
                        list(st.session_state.db["date"])[-1],
                    ],
                    y=[get_target_weight(), get_target_weight()],
                    showlegend=False,
                    hoverinfo="skip",
                    name="target",
                    mode="lines",
                    line_color="#595959",
                    line_width=1,
                    line_dash="dot",
                ),
                secondary_y=bc_in_prc,
            )
        else:
            # weight
            fig.add_trace(
                go.Scatter(
                    x=st.session_state.db["date"],
                    y=st.session_state.db["weight"],
                    showlegend=True,
                    name="weight",
                    mode=mode,
                    line_width=1,
                    line_color=clrs["weight"],
                    marker_size=6,
                )
            )

            # target
            fig.add_trace(
                go.Scatter(
                    x=[
                        list(st.session_state.db["date"])[0],
                        list(st.session_state.db["date"])[-1],
                    ],
                    y=[get_target_weight(), get_target_weight()],
                    showlegend=False,
                    hoverinfo="skip",
                    name="target",
                    mode="lines",
                    line_color="#595959",
                    line_width=1,
                    line_dash="dot",
                )
            )

    # set some layout properties
    fig.update_layout(
        # height of figure
        height=370,
        # hovering
        hovermode="x unified",
        hoverlabel=dict(font_size=12, bgcolor="#fefefe"),
        # margin
        margin=dict(l=0, r=0, t=0, b=0, pad=4),
        # legend
        legend=dict(
            orientation="h",
            borderwidth=1,
            bordercolor="#aaaaaa",
            bgcolor="#fefefe",
            font_size=10,
            valign="bottom",
            xanchor="center",
            x=0.5,
            yanchor="top",
            y=-0.1,
            itemclick=False,
        ),
    )

    # Set x/y-axes properties
    fig.update_xaxes(
        type="date",
        showgrid=True,
        range=(
            list(st.session_state.db["date"])[0] - pd.DateOffset(weeks=1),
            list(st.session_state.db["date"])[-1] + pd.DateOffset(weeks=1),
        ),
    )
    if second_y:
        fig.update_yaxes(
            secondary_y=False,
            ticksuffix=" %" if bc_in_prc else " kg",
        )
        fig.update_yaxes(
            secondary_y=True,
            ticksuffix=" kg",
        )
    else:
        fig.update_yaxes(
            ticksuffix=" %" if bc_in_prc else " kg",
        )

    # Add range slider
    fig.update_xaxes(
        rangeselector=dict(
            bgcolor="#ffffff",
            buttons=list(
                [
                    dict(count=1, label="-1mon", step="month", stepmode="backward"),
                    dict(count=2, label="-2mos", step="month", stepmode="backward"),
                    dict(count=3, label="-3mos", step="month", stepmode="backward"),
                    dict(count=6, label="-6mos", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="backward"),
                    dict(step="all"),
                ]
            ),
            x=1,
            xanchor="right",
            y=1.05,
            yanchor="middle",
        ),
    )

    return fig
