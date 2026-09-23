import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml" / "recommendation"))

from evidence import build_evidence, derive_reason_codes, generate_explanation, UNAVAILABLE_EVIDENCE  # noqa: E402


def _breakdown(co_sim=0.0, artist_pref=0.0, context_align=0.5, novelty=0.0):
    return {
        "co_listening_similarity": co_sim,
        "artist_preference": artist_pref,
        "context_alignment": context_align,
        "novelty": novelty,
    }


def test_unavailable_evidence_always_null_with_reason():
    evidence = build_evidence(_breakdown(), popularity=0.5, is_new_artist=False)
    for key, reason in UNAVAILABLE_EVIDENCE.items():
        assert evidence[key] is None
        assert evidence[f"{key}_unavailable_reason"] == reason


def test_similar_to_recent_listening_requires_threshold():
    below = build_evidence(_breakdown(co_sim=0.2), popularity=0.5, is_new_artist=False)
    above = build_evidence(_breakdown(co_sim=0.5), popularity=0.5, is_new_artist=False)
    assert "similar_to_recent_listening" not in derive_reason_codes(below, "Routine")
    assert "similar_to_recent_listening" in derive_reason_codes(above, "Routine")


def test_context_match_not_emitted_for_routine():
    evidence = build_evidence(_breakdown(context_align=0.9), popularity=0.5, is_new_artist=False)
    assert "matches_current_context" not in derive_reason_codes(evidence, "Routine")
    assert "matches_current_context" in derive_reason_codes(evidence, "Exploratory")


def test_new_artist_reason_code_reflects_evidence_flag():
    evidence = build_evidence(_breakdown(), popularity=0.9, is_new_artist=True)
    codes = derive_reason_codes(evidence, "Routine")
    assert "introduces_new_artist" in codes


def test_no_signals_falls_back_to_general_match():
    evidence = build_evidence(_breakdown(co_sim=0.0, artist_pref=0.0, context_align=0.5, novelty=0.0), popularity=0.9, is_new_artist=False)
    codes = derive_reason_codes(evidence, "Routine")
    assert codes == ["general_match"]


def test_explanation_only_references_present_reason_codes():
    evidence = build_evidence(_breakdown(co_sim=0.9), popularity=0.5, is_new_artist=False)
    codes = ["similar_to_recent_listening"]
    text = generate_explanation(evidence, codes, "Routine", "Test Artist", "Test Song")
    assert "Test Artist" in text
    assert "Test Song" in text
    assert "0.90" in text
    # must not mention unrelated signals never computed
    assert "genre" not in text.lower()
    assert "energy" not in text.lower()


def test_explanation_never_claims_new_artist_when_flag_false():
    evidence = build_evidence(_breakdown(co_sim=0.9), popularity=0.5, is_new_artist=False)
    codes = derive_reason_codes(evidence, "Routine")
    assert "introduces_new_artist" not in codes
    text = generate_explanation(evidence, codes, "Routine", "Artist", "Song")
    assert "haven't listened to before" not in text
