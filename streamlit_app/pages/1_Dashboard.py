import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib import api
from lib.format import fmt_pct, fmt_num
from lib.state import render_user_picker
from lib.style import render_header, render_footer

st.set_page_config(page_title="Dashboard — Resona AI", page_icon="🎧", layout="wide")
user_id = render_user_picker()

if not user_id:
    st.stop()

render_header(
    "Dashboard", icon="📋",
    subtitle=f"A snapshot of {user_id}'s Listening DNA, current context, discovered persona, "
    "and top recommendations — every number below comes from a real API call.",
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("##### 📊 Listening DNA")
        try:
            dna = api.get_listening_dna(user_id)
            a, b, c, d = st.columns(4)
            a.metric("Events", dna["n_events"])
            b.metric("Sessions", dna["n_sessions"])
            c.metric("Artist diversity", fmt_pct(dna["artist_diversity"]))
            d.metric("Discovery rate", fmt_pct(dna["discovery_rate"]))
        except api.ApiError as e:
            st.error(e.message)

with col2:
    with st.container(border=True):
        st.markdown("##### 🧭 Current Context")
        try:
            ctx = api.get_current_context(user_id)
            st.markdown(f"**{ctx['context_label']}**")
            st.caption(ctx["context_explanation"])
        except api.ApiError as e:
            st.error(e.message)

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.markdown("##### 🎭 Listener Persona")
        try:
            persona = api.get_persona(user_id)
            st.markdown(f"**{persona['persona_name']}**")
            st.caption(
                f"Cluster of {persona['cluster_size']} listeners · "
                f"silhouette {fmt_num(persona['silhouette_score'], 2)}"
            )
        except api.ApiError as e:
            st.info("Not enough listening history yet. " + e.message)

with col4:
    with st.container(border=True):
        st.markdown("##### ✨ Personality")
        st.caption(
            f"No personality labels exist for Last.fm listeners like {user_id} — the "
            "personality model is demonstrated separately on real research-participant "
            "data, never fabricated for a behavioral demo user. See the Personality page."
        )

st.write("")
with st.container(border=True):
    st.markdown("##### Top Recommendations")
    try:
        recs = api.get_recommendations(user_id, limit=3)
        if not recs["recommendations"]:
            st.info("No recommendations available for this listener right now.")
        else:
            cols = st.columns(3)
            for col, item in zip(cols, recs["recommendations"]):
                with col:
                    st.markdown(f"**{item['track_title']}**")
                    st.caption(item["artist_name"])
    except api.ApiError as e:
        st.error(e.message)

render_footer()
