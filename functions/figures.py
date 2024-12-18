import streamlit as st
import math
import numpy as np
import pandas as pd
from datetime import datetime, time
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression as LinReg


# dictionary of colors
clrs = {
    "weight": "#2E4057",
    "fat": "#FFBA49",
    "water": "#1098F7",
    "muscle": "#EF5B5B",
    "trend": "#66a3FF",
    "prediction": "#FF5757",
}


def main() -> go.Figure:
    """Generates figure showing timely development of weight measurements.

    Returns:
        plotly.graph_objects.Figure: main figure of app.
    """

    # marker/line mode
    mode = (
        "markers+lines"
        if st.session_state["fig_main_style"] == "both"
        else st.session_state["fig_main_style"]
    )

    # instantiate figure
    fig = go.Figure()

    # return if no measurements stored
    if st.session_state.db.shape[0] == 0:
        return fig

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
            list(st.session_state.db["date"])[0],
            list(st.session_state.db["date"])[-1] + pd.DateOffset(days=2),
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
                    dict(count=1, label="-1 month", step="month", stepmode="backward"),
                    dict(count=2, label="-2 months", step="month", stepmode="backward"),
                    dict(count=3, label="-3 months", step="month", stepmode="backward"),
                    dict(count=6, label="-6 months", step="month", stepmode="backward"),
                    dict(count=1, label="last year", step="year", stepmode="backward"),
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


def trend() -> tuple[go.Figure, float]:
    # instantiate figure
    fig = go.Figure()

    # return if no measurements stored
    if st.session_state.db.shape[0] == 0:
        return fig, 0

    print(" > how: ", st.session_state.trend_how)
    # get dates for x_axis based on trend_how
    if st.session_state.trend_how == "start date":
        # get date
        print("  > start: ", st.session_state.trend_start)
        print("         : ", type(st.session_state.trend_start))

        x_data = [
            datetime.combine(st.session_state.trend_start, time(0, 0, 0)),
            list(st.session_state.db["date"])[-1],
        ]

    elif st.session_state.trend_how == "date range":
        # get weeks
        print("  > range: ", st.session_state.trend_range)
        print("         : ", type(st.session_state.trend_range))

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

    print("    > first day: ", x_data[0])
    print("               : ", type(x_data[0]))

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

    # return if no measurements stored
    if st.session_state.db.shape[0] == 0:
        return fig, 0

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
