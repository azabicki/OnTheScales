import streamlit as st
import math
import numpy as np
import pandas as pd
from datetime import datetime, time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression as LinReg


# dictionary of colors
clrs = {
    "weight": "#2E4057",
    "fat": "#EEAA49",
    "water": "#1098F7",
    "muscle": "#EF5B5B",
    "trend": "#66a3FF",
    "prediction": "#FF5757",
}


def main() -> go.Figure|None:
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
            y=[st.session_state.user_kg, st.session_state.user_kg],
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

    # set some layout properties
    fig.update_layout(
        # height of figure
        height=420,

        # hovering
        hovermode="x unified",
        hoverlabel=dict(
            font_size=12,
            bgcolor="#fefefe"),
        hoverdistance=1,

        # title
        title=dict(
            text="Chronology of Mass",
            automargin=True,
        ),

        # margin
        margin=dict(
            l=0, r=0, t=55, b=0
        ),

        # legend
        legend=dict(
            orientation="v",
            borderwidth=1,
            bordercolor="#aaaaaa",
            bgcolor="#fefefe",
            xanchor="right",
            x=1,
            itemclick=False
        )
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


def trend() -> tuple[go.Figure|None, float]:
    """
    Function to calculate and visualize weight trends and predictions.

    Performs linear regression on weight data to determine trends, creates a visualization of actual weights, trend lines, and predictions for future weight based on current trends.

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
        # get weeks
        weeks = int(st.session_state.trend_range)
        x_data = [
            list(st.session_state.db["date"])[-1] - pd.Timedelta(weeks=weeks),
            list(st.session_state.db["date"])[-1],
        ]
    else:
        x_data = [
            list(st.session_state.db["date"])[0],
            list(st.session_state.db["date"])[-1],
        ]

    # filter data
    idx_db = st.session_state.db["date"][st.session_state.db["date"] >= x_data[0]].index
    db_data = st.session_state.db.iloc[idx_db]

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
    if (trnd < 0 and st.session_state.user_kg > db_data["weight"].iloc[-1]) or (
        trnd > 0 and st.session_state.user_kg < db_data["weight"].iloc[-1]
    ):
        # 2 weeks to predict for unwanted trend
        w2p = 2

        # set target_flags
        target_reached = False
        target_late = False

    else:
        # calculate weeks until target is reached
        date_on_target = pd.to_datetime(
            (st.session_state.user_kg - ntrcpt) / trnd, unit="ns"
        )
        t_diff = date_on_target - db_data["date"].iloc[-1]
        w2p = math.ceil(t_diff / np.timedelta64(1, "W")) + 1

        # set target_flags
        target_reached = True
        target_late = False
        if w2p > 51:
            w2p = 51
            target_late = True

    # predict weight
    pred_date = pd.date_range(
        db_data["date"].iloc[-1] + pd.Timedelta(days=1),
        db_data["date"].iloc[-1] + pd.Timedelta(weeks=w2p),
        freq="d",
    )
    pred_weight = LR.predict(pred_date.values.astype(int).reshape(-1, 1)).round(2)

    # calculate x-range
    x_range = [
        db_data["date"].iloc[0] - pd.Timedelta(weeks=1),
        pred_date[-1],
    ]

    # add target weight
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=[st.session_state.user_kg, st.session_state.user_kg],
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
            y=pred_weight[:, ],
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
            pred_target_date = -1
            str_target = pred_date[pred_target_date].strftime("%d.%m.%y")
            text = f"{str_target}<br>(> year)"

        else:
            pred_target_date = (
                np.where(pred_weight < st.session_state.user_kg)[0][0]
                if trnd < 0
                else np.where(pred_weight > st.session_state.user_kg)[0][0]
            )

            str_target = pred_date[pred_target_date].strftime("%d.%m.%y")
            str_days = pred_date[pred_target_date] - pd.Timestamp.today()
            text = f"{str_target}<br>({str_days.days} days)"

        # text_patch
        fig.add_annotation(
            x=pred_date[pred_target_date],
            y=st.session_state.user_kg,
            text=text,
            showarrow=True,
            arrowhead=3,
            yanchor="bottom",
            ay=-180 if trnd < 0 else 180,
            ax=-40,
            borderwidth=1,
            borderpad=7,
            bgcolor="#ffffff",
        )

    # set some layout properties
    fig.update_layout(
        # height of figure
        height=350,

        # turn legend off
        showlegend=False,

        # hovering
        hovermode="x unified",
        hoverlabel=dict(
            font_size=12,
            bgcolor="#fefefe"),
        hoverdistance=1,

        # margin
        margin=dict(
            l=0, r=0, t=0, b=0
        ),
    )

    # set x/y-axes properties
    fig.update_xaxes(
        range=x_range,
        type="date",
        showgrid=True,
    )
    fig.update_yaxes(
        ticksuffix=" kg",
    )

    return fig, trnd


def body_comp() -> go.Figure|None:
    """
    Function to visualize the body composition over time.

    Creates a plot showing the evolution of various body composition measurements (fat, water, and muscle percentages) over time. Can display values either as percentages or absolute weights, and optionally include weight and target lines.

    Returns:
        go.Figure | None: Plotly figure object containing the body composition visualization, or None if no measurements are stored.
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
                    legendgroup="%",
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
                    legendgroup="%",
                )
            )


    # add _weight_ & _target_
    if st.session_state["fig_body_comp_weight"] == "weight & target":
        if second_y:
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
                    legendgroup="kg",
                ),
                secondary_y=bc_in_prc,
            )

            fig.add_trace(
                go.Scatter(
                    x=[
                        list(st.session_state.db["date"])[0],
                        list(st.session_state.db["date"])[-1],
                    ],
                    y=[st.session_state.user_kg, st.session_state.user_kg],
                    showlegend=True,
                    hoverinfo="skip",
                    name="target",
                    mode="lines",
                    line_color="#595959",
                    line_width=1,
                    line_dash="dot",
                    legendgroup="kg",
                ),
                secondary_y=bc_in_prc,
            )
        else:
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
                    legendgroup="kg",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=[
                        list(st.session_state.db["date"])[0],
                        list(st.session_state.db["date"])[-1],
                    ],
                    y=[st.session_state.user_kg, st.session_state.user_kg],
                    showlegend=True,
                    hoverinfo="skip",
                    name="target",
                    mode="lines",
                    line_color="#595959",
                    line_width=1,
                    line_dash="dot",
                    legendgroup="kg",
                )
            )


    # set some layout properties
    fig.update_layout(
        # height of figure
        height=370,

        # hovering
        hovermode="x unified",
        hoverlabel=dict(
            font_size=12,
            bgcolor="#fefefe"),

        # margin
        margin=dict(
            l=0, r=0, t=0, b=0
        ),

        # legend
        legend=dict(
            orientation="v",
            borderwidth=1,
            bordercolor="#aaaaaa",
            bgcolor="#fefefe",
            xanchor="left",
            x=1.08 if second_y else 1.01,
            yanchor="top",
            y=1,
            tracegroupgap=20,
            itemclick=False,
        )
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
