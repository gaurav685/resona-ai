import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.graph_objects as go
import streamlit as st

from lib import api, theme
from lib.format import fmt_feature_name, fmt_num
from lib.state import render_user_picker
from lib.style import render_header, render_footer

st.set_page_config(page_title="Persona — Resona AI", page_icon="🎧", layout="wide")
user_id = render_user_picker()

if not user_id:
    st.stop()

render_header("Listener Persona", icon="🎭")

try:
    persona = api.get_persona(user_id)
except api.ApiError as e:
    st.info(f"Not enough listening history yet. {e.message}")
    st.stop()

st.caption(
    f"Discovered behavioral cluster for {user_id}, from unsupervised KMeans over "
    "real Listening DNA features."
)

with st.container(border=True):
    st.markdown(f"### {persona['persona_name']}")
    st.caption(
        "Cluster name is auto-derived from this cluster's two most distinguishing "
        "features — never a hard-coded label."
    )

    c1, c2 = st.columns(2)
    c1.metric("Cluster size", f"{persona['cluster_size']} listeners")
    c2.metric("Silhouette score", fmt_num(persona["silhouette_score"], 3), help="Cluster separation quality")

st.write("")

z_scores = persona["cluster_feature_z_scores"]
entries = sorted(z_scores.items(), key=lambda kv: kv[1], reverse=True)
top2 = sorted(entries, key=lambda kv: abs(kv[1]), reverse=True)[:2]

with st.container(border=True):
    if len(top2) == 2:
        (f1, z1), (f2, z2) = top2
        st.markdown(
            f"**Why this cluster?** Most distinguished by "
            f"**{'high' if z1 >= 0 else 'low'} {fmt_feature_name(f1).lower()}** "
            f"({z1:+.2f}σ vs. the average listener) and "
            f"**{'high' if z2 >= 0 else 'low'} {fmt_feature_name(f2).lower()}** ({z2:+.2f}σ)."
        )

    names = [fmt_feature_name(k) for k, _ in entries]
    values = [v for _, v in entries]
    colors = [theme.SERIES[1] if v >= 0 else theme.SERIES[8] for v in values]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h", marker_color=colors))
    fig.add_vline(x=0, line_color=theme.MUTED)
    fig.update_layout(
        height=max(240, len(names) * 32),
        margin=dict(l=0, r=20, t=10, b=10),
        xaxis_title="σ from average listener",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "σ = standard deviations from the average listener across all clustered users, "
        "on each real Listening DNA feature."
    )

render_footer()
