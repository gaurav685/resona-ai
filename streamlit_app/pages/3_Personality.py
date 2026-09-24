import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib import api
from lib.state import render_user_picker
from lib.style import render_header, render_footer

st.set_page_config(page_title="Personality — Resona AI", page_icon="🎧", layout="wide")
render_user_picker()

render_header(
    "Personality", icon="🧠",
    subtitle="Model-estimated Big Five associations from the beyond_big_five research "
    "dataset — real participants, real audio-preference features.",
)

st.warning(
    "These are model-estimated associations from music-listening preference data, "
    "not psychological diagnoses. No personality data exists for Last.fm listeners "
    "in this MVP — this page demonstrates the model on real research participants "
    "instead of fabricating a score for a behavioral demo user."
)

try:
    participants = api.get_sample_participants()["participants"]
except api.ApiError as e:
    st.error(e.message)
    st.stop()

if not participants:
    st.info("No sample participants available.")
    st.stop()

options = {p["participant_id"]: p for p in participants}
with st.container(border=True):
    selected_id = st.selectbox(
        "Research participant", list(options.keys()), format_func=lambda pid: f"Participant #{pid}"
    )
    participant = options[selected_id]

    with st.spinner("Running Random Forest inference…"):
        try:
            prediction = api.predict_personality(participant["features"])
        except api.ApiError as e:
            st.error(e.message)
            st.stop()

    st.write("")
    for pred in prediction["predictions"]:
        trait = pred["trait"]
        score = pred["score"]
        actual = participant["actual_traits"].get(trait)
        st.markdown(f"**{trait}** — {score:.2f} / 5")
        st.progress(min(max(score / 5, 0.0), 1.0))
        detail = []
        if pred["confidence"] is not None:
            detail.append(f"± {pred['confidence']:.2f} (tree-ensemble std. dev.)")
        else:
            detail.append(pred["confidence_note"] or "")
        if actual is not None:
            detail.append(f"Actual (self-reported): {actual:.2f}")
        st.caption(" · ".join(d for d in detail if d))
        top_features = ", ".join(f["feature"] for f in pred["important_features"][:3])
        if top_features:
            st.caption(f"Top contributing features: {top_features}")
        st.write("")

st.caption(
    f"Model: {prediction['predictions'][0]['model_version']}. \"Actual\" is this "
    "participant's self-reported BFI-2 score from the source dataset, shown for "
    "transparency — the model was not always close to it (see Methodology for "
    "honest evaluation metrics, including negative R² on this small dataset)."
)

render_footer()
