import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from lib.state import render_user_picker
from lib.style import inject_css, render_footer
from lib import theme

st.set_page_config(page_title="Resona AI", page_icon="🎧", layout="wide")

render_user_picker()
inject_css()

st.markdown(
    f"""
    <div style="padding: 2.5rem 0 1.5rem;">
      <span class="resona-eyebrow">College MVP · Research Project</span>
      <div class="resona-hero-title">🎧 Resona AI</div>
      <p style="font-size: 1.35rem; font-weight: 500; color: {theme.TEXT_SECONDARY}; margin-bottom: 1rem;
                animation: resona-fade-up 0.6s cubic-bezier(0.16,1,0.3,1) 0.2s both;">
        Understand people through music.
      </p>
      <p style="max-width: 42rem; color: {theme.TEXT_SECONDARY}; font-size: 1.02rem; line-height: 1.65;
                animation: resona-fade-up 0.6s cubic-bezier(0.16,1,0.3,1) 0.3s both;">
        Resona analyzes real listening behavior to estimate personality-related associations,
        discover listener personas, detect current listening context, and generate
        explainable, feedback-adaptive music recommendations — all backed by real datasets
        and models, with no fabricated numbers anywhere in the pipeline.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Personality outputs are **model-estimated associations**, not psychological diagnoses. "
    "See the Methodology page."
)

st.markdown("#### From listening data to a recommendation")
cols = st.columns(4)
steps = [
    ("📊", "Listening Behavior", "Real events from the Last.fm 1K research dataset"),
    ("🧠", "AI Intelligence", "Feature engineering, classical + neural models, clustering"),
    ("🎭", "Personality + Context + Persona", "Model-estimated associations, session context, discovered clusters"),
    ("✨", "Personalized Recommendations", "Hybrid scoring, explained and adaptive to feedback"),
]
for col, (icon, label, detail) in zip(cols, steps):
    with col:
        with st.container(border=True):
            st.markdown(f"### {icon}")
            st.markdown(f"**{label}**")
            st.caption(detail)

st.write("")
left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown("#### Why typical recommenders fall short")
        st.markdown(
            "- **Popularity bias** — most recommenders lean on what's already popular\n"
            "- **No explanation** — \"because you listened to X\" is usually the whole story\n"
            "- **Behavior only** — plays/skips treated as the complete picture, ignoring "
            "context, personality signal, or discovery intent"
        )
with right:
    with st.container(border=True):
        st.markdown("#### What Resona adds")
        st.markdown(
            "- **Context intelligence** — session-vs-baseline behavioral shift detection\n"
            "- **Persona discovery** — unsupervised clustering, never hard-coded labels\n"
            "- **Personality signal** — a real trained model, evaluated honestly (including "
            "where it underperforms)\n"
            "- **Full explainability** — every recommendation's evidence is stored and its "
            "explanation is generated from that evidence, never guessed"
        )

st.write("")
with st.container(border=True):
    st.markdown("#### 🗂️ Built on real research datasets")
    st.markdown(
        "Last.fm 1K (992 real users), the Beyond the Big Five music-personality dataset "
        "(279 real research participants), the Million Song Dataset, and DEAM. Every metric "
        "in this app is computed from these datasets or the models trained on them — see "
        "**Methodology** in the sidebar for the full breakdown, including honest limitations."
    )

st.write("")
st.success("👈 Pick a demo listener in the sidebar, then explore the pages there — or upload your own history on **Your Own History**.")

render_footer()
