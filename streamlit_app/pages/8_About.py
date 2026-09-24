import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib.state import render_user_picker

st.set_page_config(page_title="Methodology — Resona AI", page_icon="🎧", layout="wide")
render_user_picker()
st.title("Methodology")
st.caption("What Resona is built on, how each layer actually works, and where it's honestly limited.")

st.header("Datasets")
datasets = [
    ("Last.fm 1K", "Behavioral data — 992 real users, 288,965 listening events, sessionized. Powers Listening DNA, Context Intelligence, Persona Discovery, and the hybrid Recommendation Engine.", "No audio features, genre, or skip/duration data exists for these tracks."),
    ("Beyond the Big Five (Kleć et al., 2023)", "279 real research participants with self-reported BFI-2 Big Five scores and real per-song audio/emotion features. The only dataset with legitimate personality-model inputs.", "Not linked to Last.fm users — no personality data exists for the behavioral demo listeners."),
    ("Million Song Dataset (sample)", "Track/artist identity metadata (1M tracks, 13,850 artists with geolocation).", "No audio features in the metadata-only subset used here."),
    ("DEAM", "1,802 real valence/arousal emotion annotations plus per-track genre metadata.", "Own disjoint track catalog — not linked to Last.fm or MSD track identities."),
]
cols = st.columns(2)
for i, (name, use, limit) in enumerate(datasets):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{name}**")
            st.write(use)
            st.caption(f"Limit: {limit}")

st.header("Pipeline")
pipeline = [
    ("Listening DNA", "10 behavioral features computed directly from real event timestamps and artist identity. Audio-content features are explicitly reported unavailable — never approximated."),
    ("Personality model", "Linear Regression, Random Forest, and XGBoost trained on the 279-participant research dataset, plus a GPU-trained PyTorch feed-forward network, compared on identical test-set MAE. Random Forest won on the actual numbers — the neural net did not."),
    ("Persona discovery", "KMeans over real Listening DNA features, k selected by silhouette score (k=3, silhouette 0.239). DBSCAN was tried and found no useful structure. Cluster names are auto-derived — never hard-coded."),
    ("Context intelligence", "Rule-based classification from real behavioral shift signals vs. a listener's own prior baseline. No trained classifier, no ground-truth labels to score against."),
    ("Recommendation engine", "Candidate generation from the top-1,500 Last.fm items by unique listeners → filtering → weighted scoring → MMR diversity rerank. Beat a most-popular baseline on every offline metric."),
    ("Explainability", "Every recommendation persists its full score breakdown as structured evidence in SQLite. The explanation text is deterministically generated from that stored evidence — never an LLM."),
    ("Feedback loop", "like / dislike / skip / save / replay / hide feed a simple, bounded per-artist preference multiplier and a hard exclusion list — no reinforcement learning, no bandits."),
]
for title, body in pipeline:
    st.markdown(f"**{title}**")
    st.write(body)

st.header("A recorded GPU training run")
st.info("Actual recorded values — not live-fetched")
r1, r2 = st.columns(2)
with r1:
    st.write("**Model**: PyTorch feed-forward net (32→64→32→5), MSE loss, Adam")
    st.write("**Device**: CUDA")
    st.write("**GPU**: NVIDIA GeForce RTX 3050 Ti Laptop GPU")
with r2:
    st.write("**PyTorch / CUDA**: 2.14.0+cu126 / 12.6")
    st.write("**Epochs requested / completed**: 100 / 88 (early stopped)")
    st.write("**Best epoch**: 78 (val loss 0.5653)")
st.caption("Outcome: Not selected — Random Forest had lower test-set MAE (0.615 vs 0.643). Kept as an experimental artifact.")

st.header("Limitations")
st.markdown(
    "- 279 personality participants is small for 5-target regression on 32 features — "
    "R² is negative for nearly every trait/model.\n"
    "- Last.fm behavioral data and the personality/audio-feature datasets have disjoint "
    "identity spaces — no listener has both real behavioral and real personality data.\n"
    "- Recommendation candidate pool capped at the 1,500 most-listened-to items for "
    "tractability — absolute precision/recall are low as a genuine consequence.\n"
    "- night/weekend listening ratios use UTC timestamps, not the listener's true local "
    "time zone (not present in source data)."
)

st.header("Privacy & Data Handling")
st.write(
    "This is a college research MVP using only public research datasets — no real "
    "individuals' private data is collected by this app. Recommendation evidence and "
    "feedback you submit while using this demo are stored locally in this instance's "
    "SQLite database for the explainability and feedback-loop features to function, "
    "and are not sent anywhere else."
)
