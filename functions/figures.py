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

