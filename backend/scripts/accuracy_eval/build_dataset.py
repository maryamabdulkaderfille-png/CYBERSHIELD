"""Assembles a labelled URL dataset for the Objective 4 accuracy evaluation
(see run_evaluation.py in this same directory).

Sources:
  - Phishing (label="phishing"): OpenPhish's free community feed
    (https://openphish.com/feed.txt). PhishTank's public feed was tried
    first, since it's the source named in the original task, but two
    consecutive live requests during development returned inconsistent
    results (one real JSON payload, one CloudFront-served placeholder
    image) — consistent with the rate-limiting PhishTank has added to its
    unauthenticated tier. OpenPhish is used instead: no API key required,
    verified stable across repeated requests, and it's already cited in
    this thesis's Chapter 2 literature review (Bell & Komisarczuk, 2020),
    so it isn't an unexplained substitution.
  - Legitimate (label="legitimate"): the Tranco top sites list
    (https://tranco-list.eu), a research-grade ranking maintained
    specifically to be a more citation-appropriate alternative to
    Alexa/Chrome UX Report for this kind of academic use.

This script only builds and saves the dataset — it does not call the
scanner. Run it once (or whenever you want a fresh dataset); run_evaluation.py
then reads the saved CSV so the evaluation itself is reproducible without
re-downloading.
"""

import csv
import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests

OUTPUT_DIR = Path(__file__).parent
DATASET_CSV = OUTPUT_DIR / "dataset.csv"
METADATA_JSON = OUTPUT_DIR / "dataset_metadata.json"

OPENPHISH_FEED_URL = "https://openphish.com/feed.txt"
TRANCO_ZIP_URL = "https://tranco-list.eu/top-1m.csv.zip"
TRANCO_LEGITIMATE_COUNT = 250

REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "CyberShield-Thesis-AccuracyEval/1.0"


def fetch_openphish() -> list[str]:
    response = requests.get(OPENPHISH_FEED_URL, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    urls = [line.strip() for line in response.text.splitlines() if line.strip()]
    if not urls:
        raise RuntimeError("OpenPhish feed returned no URLs — check https://openphish.com/feed.txt manually.")
    return urls


def fetch_tranco(limit: int) -> list[str]:
    response = requests.get(TRANCO_ZIP_URL, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        csv_name = archive.namelist()[0]
        with archive.open(csv_name) as f:
            domains = []
            for line in f:
                _, domain = line.decode("utf-8").strip().split(",", 1)
                domains.append(domain)
                if len(domains) >= limit:
                    break
    if len(domains) < limit:
        raise RuntimeError(f"Tranco list only yielded {len(domains)} domains, expected {limit}.")
    return domains


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme in {"http", "https"} and parsed.hostname)


def main() -> None:
    print(f"Fetching phishing URLs from OpenPhish: {OPENPHISH_FEED_URL}")
    phishing_urls = [u for u in fetch_openphish() if _is_valid_url(u)]
    print(f"  -> {len(phishing_urls)} valid phishing URLs")

    print(f"Fetching top {TRANCO_LEGITIMATE_COUNT} legitimate domains from Tranco: {TRANCO_ZIP_URL}")
    legitimate_domains = fetch_tranco(TRANCO_LEGITIMATE_COUNT)
    legitimate_urls = [f"https://{domain}" for domain in legitimate_domains]
    print(f"  -> {len(legitimate_urls)} legitimate URLs")

    rows = [{"url": u, "true_label": "phishing", "source": "OpenPhish"} for u in phishing_urls]
    rows += [{"url": u, "true_label": "legitimate", "source": "Tranco"} for u in legitimate_urls]

    with open(DATASET_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "true_label", "source"])
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "phishing_source": "OpenPhish free community feed",
        "phishing_source_url": OPENPHISH_FEED_URL,
        "phishing_count": len(phishing_urls),
        "phishing_source_note": (
            "PhishTank's public feed (the source originally specified) was found to be "
            "unreliably rate-limited during development — one request returned real data, "
            "the next returned a CloudFront placeholder image instead of JSON. OpenPhish was "
            "substituted: no API key needed, verified stable, and already cited in this "
            "thesis's Chapter 2 literature review."
        ),
        "legitimate_source": "Tranco top sites list",
        "legitimate_source_url": TRANCO_ZIP_URL,
        "legitimate_count": len(legitimate_urls),
        "legitimate_source_note": (
            "Tranco publishes a new dated list daily; this dataset used whatever list was "
            "current as of built_at_utc above. Cite Tranco with the date this was built, "
            "consistent with Tranco's own citation guidance for research use."
        ),
        "total_count": len(rows),
    }
    with open(METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nWrote {len(rows)} labelled rows to {DATASET_CSV}")
    print(f"Wrote dataset metadata to {METADATA_JSON}")


if __name__ == "__main__":
    main()
