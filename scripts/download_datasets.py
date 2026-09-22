"""Download Resona AI research datasets into data/raw/<dataset_name>/.

Reads dataset entries from data/registry.yaml (the single source of truth
for URLs/licenses/sizes) and downloads each dataset's files directly —
no manual steps unless the source requires authentication, in which case
this script stops and reports the exact blocker.

Usage:
    python scripts/download_datasets.py                 # all datasets
    python scripts/download_datasets.py --dataset deam   # one dataset
    python scripts/download_datasets.py --list           # show registry entries
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import requests
import yaml
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "data" / "registry.yaml"
RAW_DIR = REPO_ROOT / "data" / "raw"

HEADERS = {"User-Agent": "Mozilla/5.0 (ResonaAI college project data pipeline)"}


def load_registry() -> list[dict]:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["datasets"]


def download_file(url: str, dest: Path, verify_md5: str | None = None) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        if verify_md5 and _md5(dest) != verify_md5:
            print(f"  existing file failed checksum, re-downloading: {dest.name}")
        else:
            print(f"  already present, skipping: {dest.name} ({dest.stat().st_size:,} bytes)")
            return True

    try:
        resp = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  DOWNLOAD FAILED: {url} -> {e}")
        return False

    total = int(resp.headers.get("content-length", 0))
    tmp_dest = dest.with_suffix(dest.suffix + ".part")
    with open(tmp_dest, "wb") as f, tqdm(
        total=total or None, unit="B", unit_scale=True, desc=dest.name
    ) as bar:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))
    tmp_dest.rename(dest)

    if verify_md5:
        actual = _md5(dest)
        if actual != verify_md5:
            print(f"  CHECKSUM MISMATCH for {dest.name}: expected {verify_md5}, got {actual}")
            return False
        print(f"  checksum verified (md5): {actual}")
    return True


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_dataset(entry: dict) -> bool:
    name = entry["name"]
    if entry.get("authentication_required"):
        print(f"[{name}] BLOCKED: authentication required. Source: {entry['source_url']}")
        return False

    print(f"[{name}] {entry['display_name']}")
    out_dir = RAW_DIR / name
    urls = [entry["download_url"]]
    if entry.get("secondary_download_url"):
        urls.append(entry["secondary_download_url"])

    checksum = entry.get("checksum") or {}
    verify_md5 = checksum.get("value") if checksum.get("algorithm") == "md5" else None

    ok = True
    for url in urls:
        filename = url.rsplit("/", 1)[-1]
        dest = out_dir / filename
        ok = download_file(url, dest, verify_md5=verify_md5 if len(urls) == 1 else None) and ok
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", help="download only this dataset name")
    parser.add_argument("--list", action="store_true", help="list registry entries and exit")
    args = parser.parse_args()

    entries = load_registry()
    if args.list:
        for e in entries:
            print(f"{e['name']:24s} {e['approximate_size']:30s} auth={e.get('authentication_required')}")
        return 0

    if args.dataset:
        entries = [e for e in entries if e["name"] == args.dataset]
        if not entries:
            print(f"Unknown dataset: {args.dataset}")
            return 1

    results = {}
    for entry in entries:
        results[entry["name"]] = download_dataset(entry)
        print()

    print("Summary:")
    for name, ok in results.items():
        print(f"  {name}: {'OK' if ok else 'FAILED/BLOCKED'}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
