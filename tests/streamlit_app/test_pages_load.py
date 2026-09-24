"""Headless verification that every Streamlit page actually runs without a
Python exception, against the real running FastAPI backend — using
Streamlit's own AppTest runtime (not a browser, but real script execution,
not just a syntax check).

Requires the backend to be reachable at RESONA_API_URL (default
http://localhost:8000); skipped otherwise rather than failing on an
environment where the backend isn't running.
"""

from pathlib import Path

import pytest
import requests
from streamlit.testing.v1 import AppTest

STREAMLIT_APP_DIR = Path(__file__).resolve().parents[2] / "streamlit_app"
API_URL = "http://localhost:8000"


def _backend_reachable() -> bool:
    try:
        return requests.get(f"{API_URL}/api/v1/health", timeout=2).ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(not _backend_reachable(), reason="backend not running at " + API_URL)

PAGES = [STREAMLIT_APP_DIR / "Home.py"] + sorted((STREAMLIT_APP_DIR / "pages").glob("*.py"))


@pytest.mark.parametrize("page_path", PAGES, ids=[p.name for p in PAGES])
def test_page_runs_without_exception(page_path):
    at = AppTest.from_file(str(page_path), default_timeout=30)
    at.session_state["user_id"] = "user_000001"
    at.run()
    assert not at.exception, f"{page_path.name} raised: {at.exception}"
