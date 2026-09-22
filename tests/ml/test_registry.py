from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "registry.yaml"

REQUIRED_FIELDS = {
    "name",
    "source_url",
    "download_url",
    "license",
    "citation",
    "approximate_size",
    "expected_files",
    "download_method",
    "authentication_required",
    "commercial_use",
    "intended_use",
    "checksum",
}


def load_entries():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["datasets"]


def test_registry_has_four_datasets():
    entries = load_entries()
    names = {e["name"] for e in entries}
    assert names == {"beyond_big_five", "lastfm_1k", "million_song_dataset", "deam"}


def test_registry_entries_have_required_fields():
    for entry in load_entries():
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"{entry.get('name')} missing fields: {missing}"


def test_registry_no_authentication_required():
    for entry in load_entries():
        assert entry["authentication_required"] is False, (
            f"{entry['name']} requires authentication — should have been "
            "reported as a blocker, not silently included"
        )


def test_registry_checksum_never_fabricated():
    for entry in load_entries():
        checksum = entry["checksum"]
        if checksum["value"] != "unknown":
            assert checksum["algorithm"] != "unknown"
            assert checksum.get("source"), "verified checksum must cite its source"
