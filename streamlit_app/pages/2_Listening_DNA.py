import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import api, theme
from lib.format import fmt_pct
from lib.state import render_user_picker

st.set_page_config(page_title="Listening DNA — Resona AI", page_icon="🎧", layout="wide")
user_id = render_user_picker()
st.title("Listening DNA")

if not user_id:
    st.stop()

try:
    dna = api.get_listening_dna(user_id)
except api.ApiError as e:
    st.error(e.message)
    st.stop()

st.caption(f"Behavioral fingerprint for {user_id}, computed from real Last.fm listening events.")

cols = st.columns(6)
cols[0].metric("Events", dna["n_events"])
cols[1].metric("Sessions", dna["n_sessions"])
cols[2].metric("Artist diversity", fmt_pct(dna["artist_diversity"]))
cols[3].metric("Discovery rate", fmt_pct(dna["discovery_rate"]))
cols[4].metric("Replay rate", fmt_pct(dna["replay_rate"]))
cols[5].metric("Repeat rate", fmt_pct(dna["repeat_rate"]))

left, right = st.columns(2)

with left:
    st.subheader("Top Artists")
    top_artists = dna["top_artists"]
    if not top_artists:
        st.info("Not enough listening history yet.")
    else:
        df = pd.DataFrame(top_artists).iloc[::-1]  # #1 at top
        fig = go.Figure(
            go.Bar(
                x=df["play_count"],
                y=df["artist_name"],
                orientation="h",
                marker_color=theme.SERIES[1],
            )
        )
        fig.update_layout(
            height=max(220, len(df) * 34),
            margin=dict(l=0, r=20, t=10, b=10),
            xaxis_title="Plays",
            yaxis_title=None,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Temporal Patterns")
    st.progress(dna["night_listening_ratio_utc"] or 0.0, text=f"Night listening: {fmt_pct(dna['night_listening_ratio_utc'])}")
    st.progress(dna["weekend_listening_ratio_utc"] or 0.0, text=f"Weekend listening: {fmt_pct(dna['weekend_listening_ratio_utc'])}")
    st.progress(dna["artist_concentration"] or 0.0, text=f"Artist concentration (HHI): {fmt_pct(dna['artist_concentration'], 1)}")
    st.caption(
        "Night/weekend ratios use event UTC timestamps, not the listener's local time "
        "zone (not available in the source data)."
    )

    st.subheader("Not Available For This Dataset")
    unavailable_fields = [
        ("genre_diversity", "Genre diversity"),
        ("completion_rate", "Completion rate"),
        ("skip_rate", "Skip rate"),
        ("energy", "Energy"),
        ("valence", "Valence"),
        ("danceability", "Danceability"),
        ("tempo", "Tempo"),
        ("acousticness", "Acousticness"),
        ("instrumentalness", "Instrumentalness"),
        ("speechiness", "Speechiness"),
    ]
    for key, label in unavailable_fields:
        reason = dna.get(f"{key}_unavailable_reason")
        if reason:
            st.caption(f"🚫 **{label}**: not available — {reason}")
