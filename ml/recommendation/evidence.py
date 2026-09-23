"""Part A/B — structured recommendation evidence, reason codes, and
deterministic (non-LLM) explanation text.

Every reason code is emitted only when the actual stored evidence crosses
a stated threshold — never guessed. Evidence types this MVP cannot
support (genre_preference, energy_match — no genre/audio-feature dataset
is joined to Last.fm track identifiers; personality_signal — no
personality labels exist for Last.fm users) are explicitly reported as
unavailable rather than omitted or faked, matching every other phase's
non-fabrication pattern.
"""

from __future__ import annotations

REASON_CODE_THRESHOLDS = {
    "similar_to_recent_listening": 0.3,  # co_listening_similarity
    "matches_current_context": 0.7,  # context_alignment
    "exploration_candidate": 0.6,  # novelty
    "behavioral_signal": 0.5,  # artist_preference
}

UNAVAILABLE_EVIDENCE = {
    "genre_preference": "no genre labels joined to Last.fm track identifiers",
    "energy_match": "no audio-feature dataset joined to Last.fm track identifiers",
    "personality_signal": "no personality labels exist for Last.fm users",
}


def build_evidence(score_breakdown: dict, popularity: float, is_new_artist: bool) -> dict:
    evidence = {
        "co_listening_similarity": score_breakdown["co_listening_similarity"],
        "artist_preference": score_breakdown["artist_preference"],
        "context_alignment": score_breakdown["context_alignment"],
        "novelty": score_breakdown["novelty"],
        "popularity": popularity,
        "is_new_artist": is_new_artist,
    }
    for key, reason in UNAVAILABLE_EVIDENCE.items():
        evidence[key] = None
        evidence[f"{key}_unavailable_reason"] = reason
    return evidence


def derive_reason_codes(evidence: dict, context_label: str) -> list[str]:
    codes = []
    if evidence["co_listening_similarity"] >= REASON_CODE_THRESHOLDS["similar_to_recent_listening"]:
        codes.append("similar_to_recent_listening")
    if (
        evidence["context_alignment"] >= REASON_CODE_THRESHOLDS["matches_current_context"]
        and context_label not in ("Routine", "Unknown")
    ):
        codes.append("matches_current_context")
    if evidence["is_new_artist"]:
        codes.append("introduces_new_artist")
    if evidence["novelty"] >= REASON_CODE_THRESHOLDS["exploration_candidate"]:
        codes.append("exploration_candidate")
    if evidence["artist_preference"] >= REASON_CODE_THRESHOLDS["behavioral_signal"] and not evidence["is_new_artist"]:
        codes.append("behavioral_signal")
    if not codes:
        codes.append("general_match")
    return codes


_TEMPLATES = {
    "similar_to_recent_listening": lambda ev, ctx: (
        f"it's behaviorally similar to tracks you've listened to (co-listening similarity {ev['co_listening_similarity']:.2f})"
    ),
    "matches_current_context": lambda ev, ctx: f"it matches your current {ctx} listening context",
    "introduces_new_artist": lambda ev, ctx: "it introduces an artist you haven't listened to before",
    "exploration_candidate": lambda ev, ctx: f"it's a novel pick outside your usual listening (novelty {ev['novelty']:.2f})",
    "behavioral_signal": lambda ev, ctx: f"it's by an artist you already listen to frequently (preference {ev['artist_preference']:.2f})",
    "general_match": lambda ev, ctx: "it scored highest among the available candidates on this run",
}


def generate_explanation(
    evidence: dict, reason_codes: list[str], context_label: str, artist_name: str, track_title: str
) -> str:
    clauses = [_TEMPLATES[code](evidence, context_label) for code in reason_codes if code in _TEMPLATES]
    if not clauses:
        clauses = [_TEMPLATES["general_match"](evidence, context_label)]

    if len(clauses) == 1:
        reason_text = clauses[0]
    elif len(clauses) == 2:
        reason_text = f"{clauses[0]}, and {clauses[1]}"
    else:
        reason_text = ", ".join(clauses[:-1]) + f", and {clauses[-1]}"

    return f'"{track_title}" by {artist_name} was recommended because {reason_text}.'
