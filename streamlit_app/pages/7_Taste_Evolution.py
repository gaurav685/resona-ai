import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import api, theme
from lib.state import render_user_picker
from lib.style import render_header, render_footer


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"

st.set_page_config(page_title="Taste Evolution — Resona AI", page_icon="🎧", layout="wide")
user_id = render_user_picker()

if not user_id:
    st.stop()

render_header(
    "Taste Evolution", icon="📈",
    subtitle=f"Real monthly listening-behavior trends for {user_id}, binned from actual event timestamps.",
)

try:
    evolution = api.get_taste_evolution(user_id)
except api.ApiError as e:
    st.error(e.message)
    st.stop()

periods = evolution["periods"]

if not periods:
    st.info("Not enough listening history yet.")
    st.stop()

if len(periods) == 1:
    st.info(
        "Only one time period in this listener's sample. A trend needs at least two "
        "months of data — this listener's capped event sample falls in a single month."
    )
    st.stop()

df = pd.DataFrame(periods)


def line_chart(title, caption, col, color_key):
    with st.container(border=True):
        st.markdown(f"##### {title}")
        st.caption(caption)
        fig = go.Figure(
            go.Scatter(
                x=df["period"],
                y=df[col],
                mode="lines+markers",
                line=dict(color=theme.SERIES[color_key], width=2),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor=_hex_to_rgba(theme.SERIES[color_key], 0.08),
            )
        )
        fig.update_layout(
            height=220,
            margin=dict(l=0, r=20, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)


c1, c2 = st.columns(2)
with c1:
    line_chart("Listening Frequency", "Events per active day, by month", "listening_frequency", 1)
    st.write("")
    line_chart("Discovery Rate", "Share of plays that were a new artist, by month", "discovery_rate", 2)
with c2:
    line_chart("Artist Diversity", "Unique artists / plays, by month", "artist_diversity", 3)
    st.write("")
    line_chart("Unique Artists", "Distinct artists played, by month", "unique_artists", 4)

render_footer()
