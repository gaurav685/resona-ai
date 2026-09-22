import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))

from data.schemas import (  # noqa: E402
    Artist,
    ListeningEvent,
    PersonalityRecord,
    Track,
    User,
    parse_timestamp,
)


def test_user_id_is_stripped():
    u = User(user_id="  user_000123  ", source_dataset="test")
    assert u.user_id == "user_000123"


def test_listening_event_requires_valid_timestamp():
    with pytest.raises(ValidationError):
        ListeningEvent(
            event_id="e1",
            user_id="u1",
            played_at="not-a-timestamp",
            source_dataset="test",
        )


def test_listening_event_accepts_iso_timestamp():
    ev = ListeningEvent(
        event_id="e1",
        user_id="u1",
        played_at="2009-04-08T01:57:47Z",
        source_dataset="test",
    )
    assert ev.played_at == datetime(2009, 4, 8, 1, 57, 47, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2009-04-08T01:57:47Z", datetime(2009, 4, 8, 1, 57, 47, tzinfo=timezone.utc)),
        ("2009-04-08", datetime(2009, 4, 8, tzinfo=timezone.utc)),
        ("", None),
        (None, None),
        ("garbage", None),
    ],
)
def test_parse_timestamp(raw, expected):
    assert parse_timestamp(raw) == expected


def test_track_optional_fields_default_none():
    t = Track(track_id="T1", title="Song", source_dataset="test")
    assert t.artist_id is None
    assert t.duration_sec is None


def test_artist_name_required():
    with pytest.raises(ValidationError):
        Artist(artist_id="A1", source_dataset="test")


def test_personality_record_holds_raw_facets():
    rec = PersonalityRecord(
        participant_id="16",
        openness=3.0,
        conscientiousness=2.8,
        extraversion=3.1,
        agreeableness=3.4,
        neuroticism=3.3,
        raw_facets={"sociability": 2.75, "assertiveness": 3.25},
        source_dataset="beyond_big_five",
    )
    assert rec.raw_facets["sociability"] == 2.75
