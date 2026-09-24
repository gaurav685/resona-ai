import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib import api
from lib.format import fmt_reason_code
from lib.state import render_user_picker

st.set_page_config(page_title="Recommendations — Resona AI", page_icon="🎧", layout="wide")
user_id = render_user_picker()
st.title("Recommendations")

if not user_id:
    st.stop()

if "feedback_sent" not in st.session_state:
    st.session_state.feedback_sent = {}  # recommendation_id -> feedback_type

st.caption(
    f"Hybrid recommendations for {user_id} — content/co-listening similarity, artist "
    "preference, context alignment, and novelty, combined and diversity-reranked."
)

c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    novelty = st.slider("Novelty", 0.0, 1.0, 0.2, 0.1, help="Low = familiar, High = novel picks")
with c2:
    context_override = st.selectbox(
        "Listening context", ["Auto-detect", "Exploratory", "Focused", "Reflective", "Routine"]
    )
with c3:
    st.write("")
    st.write("")
    if st.button("Refresh"):
        st.cache_data.clear()

context_param = None if context_override == "Auto-detect" else context_override

try:
    recs = api.get_recommendations(user_id, limit=12, novelty=novelty, context=context_param)
except api.ApiError as e:
    st.error(e.message)
    st.stop()

if recs["recommendations"]:
    w = recs["weights_used"]
    st.caption(
        f"Detected context: **{recs['context_label']}** · weights used: "
        f"co-listening {w['co_listening_similarity']*100:.0f}%, "
        f"artist preference {w['artist_preference']*100:.0f}%, "
        f"context {w['context_alignment']*100:.0f}%, novelty {w['novelty']*100:.0f}%"
    )
else:
    st.info("This listener has no eligible candidates right now — try adjusting novelty or context.")

cols = st.columns(3)
for i, item in enumerate(recs["recommendations"]):
    rec_id = item["recommendation_id"]
    sent = st.session_state.feedback_sent.get(rec_id)
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"**{item['track_title']}**")
            st.caption(item["artist_name"])
            st.caption(f"Score: {item['score']*100:.0f}")
            st.caption(" · ".join(fmt_reason_code(c) for c in item["reason_codes"]))
            st.write(item["explanation"])

            b1, b2, b3, b4 = st.columns(4)
            button_specs = [
                (b1, "👍", "like"),
                (b2, "👎", "dislike"),
                (b3, "🔖", "save"),
                (b4, "🙈", "hide"),
            ]
            for btn_col, icon, feedback_type in button_specs:
                with btn_col:
                    active = sent == feedback_type
                    if st.button(
                        icon,
                        key=f"{feedback_type}_{rec_id}",
                        help=feedback_type.capitalize(),
                        type="primary" if active else "secondary",
                    ):
                        try:
                            api.submit_feedback(rec_id, feedback_type)
                            st.session_state.feedback_sent[rec_id] = feedback_type
                            st.rerun()
                        except api.ApiError as e:
                            st.error(e.message)

            if sent in ("hide", "dislike"):
                st.caption("Recorded — excluded from future recommendations for this listener.")
            elif sent:
                st.caption(f"Recorded: {sent}.")

if recs["recommendations"]:
    st.caption(recs["note"])
