"""Shared demo-listener selection, persisted in Streamlit session state
across pages — this MVP has no auth, so a real Last.fm user must be picked
explicitly (mirrors apps/web/src/lib/user-context.tsx)."""

import streamlit as st

from lib import api
from lib.style import inject_css


@st.cache_data(ttl=300)
def _load_users() -> list[dict]:
    return api.list_users()["users"]


def render_user_picker() -> str | None:
    inject_css()
    st.sidebar.markdown(
        '<div class="resona-brand">🎧 Resona AI</div>',
        unsafe_allow_html=True,
    )

    try:
        users = _load_users()
    except api.ApiError as e:
        st.sidebar.error(f"Could not load listeners: {e.message}")
        return None
    if not users:
        st.sidebar.warning("No listeners available.")
        return None

    users_sorted = sorted(users, key=lambda u: u["user_id"])
    ids = [u["user_id"] for u in users_sorted]
    labels = {u["user_id"]: f"{u['user_id']} ({u['n_events']} plays)" for u in users_sorted}

    if "user_id" not in st.session_state or st.session_state.user_id not in ids:
        st.session_state.user_id = ids[0]

    st.sidebar.caption("DEMO LISTENER")
    selected = st.sidebar.selectbox(
        "Demo listener",
        ids,
        index=ids.index(st.session_state.user_id),
        format_func=lambda uid: labels[uid],
        key="user_id_select",
        label_visibility="collapsed",
    )
    st.session_state.user_id = selected
    st.sidebar.caption(f"{len(ids)} real Last.fm listeners available")
    st.sidebar.divider()
    return selected
