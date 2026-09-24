import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib import api
from lib.format import fmt_pct, fmt_num
from lib.state import render_user_picker
from lib.style import render_header, render_footer

st.set_page_config(page_title="Current State — Resona AI", page_icon="🎧", layout="wide")
user_id = render_user_picker()

if not user_id:
    st.stop()

render_header(
    "Current State", icon="⏱️",
    subtitle=f"Recent listening activity for {user_id}, compared against their own historical baseline.",
)

try:
    ctx = api.get_current_context(user_id)
except api.ApiError as e:
    st.error(e.message)
    st.stop()

with st.container(border=True):
    st.markdown(f"### {ctx['context_label']}")
    st.write(ctx["context_explanation"])
    st.caption(ctx["disclaimer"])

st.write("")
st.markdown("##### Recent Windows")
windows = ctx["windows"]
labels = {
    "last_5": "Last 5 tracks",
    "last_10": "Last 10 tracks",
    "current_session": "Current session",
    "last_30_min": "Last 30 minutes",
}
cols = st.columns(4)
for col, (key, label) in zip(cols, labels.items()):
    w = windows[key]
    with col:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            if w["n_events"] == 0:
                st.caption("No events")
            else:
                st.caption(f"{w['n_events']} events")
                st.caption(f"Diversity: {fmt_pct(w['artist_diversity'])}")
                st.caption(f"Repeat: {fmt_pct(w['repeat_rate'])}")

st.write("")
left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.markdown("##### Shift vs. Personal Baseline")
        st.caption("Current session compared to this listener's history before it.")
        shifts = ctx["shifts"]

        def shift_row(label, value, unit=""):
            if value is None:
                return
            sign = "+" if value > 0 else ""
            st.write(f"{label}: **{sign}{value:.0f}{unit}**" if unit == "s" else f"{label}: **{sign}{value:.2f}**")

        shift_row("Artist diversity shift", shifts["diversity_shift"])
        shift_row("Repeat-rate shift", shifts["repeat_shift"])
        shift_row("Night-listening shift", shifts["night_shift"])
        shift_row("Pace shift", shifts["pace_shift_sec"], unit="s")

with right:
    with st.container(border=True):
        st.markdown("##### Not Available For This Dataset")
        for key, label in [
            ("energy_shift", "Energy"),
            ("valence_shift", "Valence"),
            ("tempo_shift", "Tempo"),
            ("genre_shift", "Genre"),
        ]:
            reason = shifts.get(f"{key}_unavailable_reason")
            st.caption(f"🚫 **{label}**: not available — {reason}")
        st.caption(f"Baseline events: {fmt_num(ctx['baseline'].get('n_events'), 0)}")

render_footer()
