import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import api, theme
from lib.format import fmt_pct, fmt_reason_code
from lib.state import render_user_picker
from lib.style import render_header, render_footer, render_pills

st.set_page_config(page_title="Your Own History — Resona AI", page_icon="🎧", layout="wide")
render_user_picker()
render_header(
    "Your Own History", icon="⬆️",
    subtitle="Upload your own Spotify, YouTube Music, or Apple Music export to run the same real "
    "Listening DNA, context, and recommendation pipeline on your own data — not the "
    "992 Last.fm demo listeners.",
)

st.info(
    "This is your own real export, not a live account connection — Resona has no "
    "registered Spotify/Google developer app, so it can't do live OAuth login. Your file "
    "is processed in memory for this one request and never saved to disk (recommendation "
    "results are logged like any other recommendation, so Like/Dislike/Save/Hide work — "
    "see the Methodology page)."
)
st.warning(
    "No personality result is shown here either: the personality model needs 29 real "
    "audio-feature + 3 attitude-rating inputs that none of these exports contain."
)

service = st.selectbox(
    "Which export are you uploading?",
    ["spotify", "youtube_music", "apple_music"],
    format_func=lambda s: {"spotify": "Spotify", "youtube_music": "YouTube Music", "apple_music": "Apple Music"}[s],
)

with st.expander("Where do I get this file?"):
    if service == "spotify":
        st.markdown(
            "- Go to **privacy.spotify.com** → *Request data* → **Extended streaming history** "
            "(richest — includes skip data) or the basic **Account data** request.\n"
            "- Spotify emails you a ZIP within a few days. Unzip it and upload the "
            "`StreamingHistory*.json` or `Streaming_History_Audio_*.json` file(s) here."
        )
    elif service == "youtube_music":
        st.markdown(
            "- Go to **takeout.google.com** → deselect all → select only **YouTube and YouTube Music** "
            "→ choose JSON format for history.\n"
            "- In the download, find `Takeout/YouTube and YouTube Music/history/watch-history.json` "
            "and upload it here (it includes regular YouTube views too — those are filtered out automatically)."
        )
    else:
        st.markdown(
            "- Go to **privacy.apple.com** → *Request a copy of your data* → select "
            "**Apple Media Services Information**.\n"
            "- In the download, find `Apple Music Activity/Apple Music - Play History Daily Tracks.csv` "
            "(or `Apple Music - Recently Played Tracks.csv`) and upload it here."
        )

uploaded_files = st.file_uploader(
    "Upload one or more export files",
    accept_multiple_files=True,
    type=["json", "csv"],
)

if uploaded_files and st.button("Analyze my history", type="primary"):
    with st.spinner("Parsing your history and running the real pipeline…"):
        try:
            result = api.analyze_upload(service, uploaded_files)
        except api.ApiError as e:
            st.error(e.message)
            st.stop()

    if result["parse_errors"]:
        for fname, err in result["parse_errors"].items():
            st.warning(f"Couldn't parse {fname}: {err}")

    st.success(
        f"Parsed {result['n_events_parsed']} events from {result['n_files']} file(s). "
        f"{result['n_tracks_matched_catalog']} of {result['n_distinct_tracks']} distinct tracks "
        "matched our recommendation catalog."
    )

    dna = result["listening_dna"]
    ctx = result["current_context"]

    st.write("")
    with st.container(border=True):
        st.markdown("##### 🧬 Listening DNA")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Events", dna["n_events"])
        c2.metric("Sessions", dna["n_sessions"])
        c3.metric("Artist diversity", fmt_pct(dna["artist_diversity"]))
        c4.metric("Discovery rate", fmt_pct(dna["discovery_rate"]))

        if dna["top_artists"]:
            df = pd.DataFrame(dna["top_artists"]).iloc[::-1]
            fig = go.Figure(go.Bar(x=df["play_count"], y=df["artist_name"], orientation="h", marker_color=theme.SERIES[1]))
            fig.update_layout(
                height=max(200, len(df) * 34), margin=dict(l=0, r=20, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.write("")
    with st.container(border=True):
        st.markdown("##### 🧭 Current Context")
        st.markdown(f"**{ctx['context_label']}**")
        st.write(ctx["context_explanation"])

    periods = result["taste_evolution"]["periods"]
    if len(periods) > 1:
        st.write("")
        with st.container(border=True):
            st.markdown("##### 📈 Taste Evolution")
            pdf = pd.DataFrame(periods)
            fig = go.Figure(go.Scatter(x=pdf["period"], y=pdf["listening_frequency"], mode="lines+markers", line=dict(color=theme.SERIES[1])))
            fig.update_layout(height=220, margin=dict(l=0, r=20, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    recs = result.get("recommendations")
    st.write("")
    if recs and recs["recommendations"]:
        st.markdown("##### ✨ Recommendations For You")
        cols = st.columns(3)
        for i, item in enumerate(recs["recommendations"]):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{item['track_title']}**")
                    st.caption(item["artist_name"])
                    render_pills([fmt_reason_code(c) for c in item["reason_codes"]], accent=True)
                    st.caption(item["explanation"])
                    b1, b2, b3, b4 = st.columns(4)
                    for btn_col, icon, fb in [(b1, "👍", "like"), (b2, "👎", "dislike"), (b3, "🔖", "save"), (b4, "🙈", "hide")]:
                        with btn_col:
                            if st.button(icon, key=f"{fb}_{item['recommendation_id']}", help=fb.capitalize(), use_container_width=True):
                                api.submit_feedback(item["recommendation_id"], fb)
                                st.toast(f"Recorded: {fb}")
    else:
        st.info("No recommendations could be generated from this upload.")

    st.caption(result["note"])

render_footer()
