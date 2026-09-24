"""Shared demo-listener selection, persisted in Streamlit session state
across pages — this MVP has no auth, so a real Last.fm user must be picked
explicitly (mirrors apps/web/src/lib/user-context.tsx)."""

import streamlit as st

from lib import api


@st.cache_data(ttl=300)
def _load_users() -> list[dict]:
    return api.list_users()["users"]


def render_user_picker() -> str | None:
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

    selected = st.sidebar.selectbox(
        "Demo listener",
        ids,
        index=ids.index(st.session_state.user_id),
        format_func=lambda uid: labels[uid],
        key="user_id_select",
    )
    st.session_state.user_id = selected
    return selected
