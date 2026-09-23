import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    """Ensure all SQLAlchemy tables exist before any test runs.

    FastAPI's lifespan startup (which normally calls Base.metadata.create_all)
    only fires when TestClient is used as a context manager; several tests
    construct `TestClient(app)` directly at module scope for readability, so
    this fixture creates the tables independently, once per test session.
    """
    from app.db.session import Base, engine
    from app import models  # noqa: F401  (registers models on Base.metadata)

    Base.metadata.create_all(bind=engine)
