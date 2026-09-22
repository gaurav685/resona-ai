"""Validate raw datasets in data/raw/ against data/registry.yaml expectations.

Checks performed (real, on the actual downloaded files):
  - file exists / non-empty
  - archive integrity (zip/tar) where applicable
  - expected member/file presence
  - basic content sanity (row counts, column presence) for text/CSV members

Usage:
    python scripts/validate_datasets.py
    python scripts/validate_datasets.py --dataset deam
"""

from __future__ import annotations

import argparse
import sys
import tarfile
import zipfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "data" / "registry.yaml"
RAW_DIR = REPO_ROOT / "data" / "raw"


def load_registry() -> list[dict]:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["datasets"]


def validate_beyond_big_five(out_dir: Path) -> list[str]:
    issues = []
    f = out_dir / "PER_dataset.xls"
    if not f.exists():
        return [f"missing file: {f.name}"]
    import pandas as pd

    df = pd.read_excel(f)
    if df.shape[0] == 0:
        issues.append("PER_dataset.xls has 0 rows")
    required_cols = {"userId", "songId", "Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"}
    missing = required_cols - set(df.columns)
    if missing:
        issues.append(f"missing expected columns: {missing}")
    print(f"  PER_dataset.xls: {df.shape[0]} rows, {df.shape[1]} cols, "
          f"{df['userId'].nunique()} unique users, {df.duplicated().sum()} exact-duplicate rows, "
          f"{int(df.isnull().sum().sum())} null cells")
    return issues


def validate_lastfm(out_dir: Path) -> list[str]:
    issues = []
    f = out_dir / "lastfm-dataset-1K.tar.gz"
    if not f.exists():
        return [f"missing file: {f.name}"]
    size = f.stat().st_size
    print(f"  {f.name}: {size:,} bytes")
    try:
        with tarfile.open(f, "r:gz") as tar:
            names = tar.getnames()
    except tarfile.TarError as e:
        return [f"archive failed to open: {e}"]
    print(f"  archive contains {len(names)} members")
    expected_suffixes = ["userid-profile.tsv", "userid-timestamp-artid-artname-traid-traname.tsv"]
    for suffix in expected_suffixes:
        if not any(n.endswith(suffix) for n in names):
            issues.append(f"expected member ending in '{suffix}' not found in archive")
    return issues


def validate_msd(out_dir: Path) -> list[str]:
    issues = []
    tracks = out_dir / "unique_tracks.txt"
    if not tracks.exists():
        issues.append("missing file: unique_tracks.txt")
    else:
        n_lines = 0
        bad_lines = 0
        with open(tracks, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                n_lines += 1
                if line.count("<SEP>") != 3:
                    bad_lines += 1
        print(f"  unique_tracks.txt: {n_lines:,} lines, {bad_lines:,} malformed (expected 3 <SEP> per line)")
        if n_lines == 0:
            issues.append("unique_tracks.txt is empty")

    loc = out_dir / "artist_location.txt"
    if not loc.exists():
        issues.append("missing file: artist_location.txt")
    else:
        with open(loc, "r", encoding="utf-8", errors="replace") as f:
            n = sum(1 for _ in f)
        print(f"  artist_location.txt: {n:,} lines")
    return issues


def validate_deam(out_dir: Path) -> list[str]:
    issues = []
    ann = out_dir / "DEAM_Annotations.zip"
    meta = out_dir / "metadata.zip"
    for f in (ann, meta):
        if not f.exists():
            issues.append(f"missing file: {f.name}")
            continue
        try:
            with zipfile.ZipFile(f) as z:
                bad = z.testzip()
                if bad:
                    issues.append(f"{f.name}: corrupt member {bad}")
                else:
                    print(f"  {f.name}: {len(z.namelist())} members, integrity OK")
        except zipfile.BadZipFile as e:
            issues.append(f"{f.name}: not a valid zip ({e})")
    return issues


VALIDATORS = {
    "beyond_big_five": validate_beyond_big_five,
    "lastfm_1k": validate_lastfm,
    "million_song_dataset": validate_msd,
    "deam": validate_deam,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", help="validate only this dataset name")
    args = parser.parse_args()

    entries = load_registry()
    if args.dataset:
        entries = [e for e in entries if e["name"] == args.dataset]

    all_ok = True
    for entry in entries:
        name = entry["name"]
        print(f"[{name}]")
        out_dir = RAW_DIR / name
        validator = VALIDATORS.get(name)
        if validator is None:
            print("  no validator registered")
            continue
        issues = validator(out_dir)
        if issues:
            all_ok = False
            for issue in issues:
                print(f"  ISSUE: {issue}")
        else:
            print("  OK")
        print()

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
