"""Objective 4 accuracy evaluation — runs the EXISTING, UNMODIFIED URL
scanner (`app.services.url_scanner.engine.scan_url`) against the labelled
dataset built by build_dataset.py, and reports real Precision, Recall,
F1-score, and Accuracy.

This is a standalone, additive measurement script. It imports and calls
scan_url() directly (no HTTP round-trip), and does not alter any rule or
scoring logic in url_scanner/ — changing the detection logic to improve
this number would defeat the purpose of an honest evaluation.

Usage (from the backend/ directory, e.g. inside the backend container):
    python scripts/accuracy_eval/run_evaluation.py

Requires dataset.csv to already exist (run build_dataset.py first) and a
working database connection (blacklist_check and the rule on/off registry
both query the database) — this deliberately evaluates the system exactly
as it is currently configured, not a stripped-down stand-in for it.
"""

import csv
import os
import sys
import time
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
DATASET_CSV = SCRIPT_DIR / "dataset.csv"
MISCLASSIFIED_CSV = SCRIPT_DIR / "misclassified.csv"

# Both scan_url() and the Flask app import from `app.*`; running this script
# from backend/ (or /app inside the container) puts that package on the path
# already, but this makes it work from any cwd too.
sys.path.insert(0, str(SCRIPT_DIR.parent.parent))

load_dotenv()

from app import create_app  # noqa: E402
from app.services.url_scanner.engine import scan_url  # noqa: E402
from app.utils.errors import APIError  # noqa: E402

PHISHING_RISK_LEVELS_LENIENT = {"Suspicious", "Dangerous"}
PHISHING_RISK_LEVELS_STRICT = {"Dangerous"}

# Per-rule signals that distinguish "this network lookup genuinely failed"
# from "this rule doesn't apply to this URL" — both cases otherwise look
# similar in the RuleResult (see engine.py / the three rule modules for the
# exact branches these correspond to). Traced by reading the rule source,
# not guessed.
NETWORK_RULE_NAMES = {"ssl_certificate", "domain_age", "redirect_check"}


def _rule_network_failed(rule_name: str, rule_result) -> bool:
    if rule_result is None:
        return False
    # Engine-level: the rule didn't finish within the shared timeout, or
    # raised an exception the engine caught on its behalf.
    if rule_result.detail == "timeout":
        return True
    if rule_result.message == "This check failed unexpectedly and was skipped.":
        return True

    if rule_name == "ssl_certificate":
        # detail=="unknown" is shared between "not HTTPS, not applicable"
        # (triggered=False) and "handshake/lookup genuinely failed"
        # (triggered=True) — see ssl_certificate.py.
        return rule_result.detail == "unknown" and rule_result.triggered
    if rule_name == "domain_age":
        return rule_result.message == "Domain registration date could not be determined."
    if rule_name == "redirect_check":
        return rule_result.message == "Redirect chain could not be checked."
    return False


def load_dataset() -> list[dict]:
    if not DATASET_CSV.exists():
        raise SystemExit(f"{DATASET_CSV} not found — run build_dataset.py first.")
    with open(DATASET_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_metrics(tp: int, fp: int, tn: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


def print_mapping_report(title: str, tp: int, fp: int, tn: int, fn: int) -> None:
    m = compute_metrics(tp, fp, tn, fn)
    print(f"\n--- {title} ---")
    print(f"  True Positives  (phishing correctly flagged):     {tp}")
    print(f"  False Positives (legitimate wrongly flagged):     {fp}")
    print(f"  True Negatives  (legitimate correctly cleared):   {tn}")
    print(f"  False Negatives (phishing missed):                {fn}")
    print(f"  Precision: {m['precision']:.4f}")
    print(f"  Recall:    {m['recall']:.4f}")
    print(f"  F1-score:  {m['f1']:.4f}")
    print(f"  Accuracy:  {m['accuracy']:.4f}")


def main() -> None:
    rows = load_dataset()
    print(f"Loaded {len(rows)} labelled URLs from {DATASET_CSV}")
    print(
        "\nBinary mapping used for this evaluation (stated explicitly for the thesis defense):\n"
        "  LENIENT mapping: Safe + Low Risk -> predicted legitimate; Suspicious + Dangerous -> predicted phishing.\n"
        "  STRICT mapping:  everything except Dangerous -> predicted legitimate; only Dangerous -> predicted phishing.\n"
    )

    app = create_app(os.environ.get("FLASK_ENV", "development"))

    counts_lenient = Counter()
    counts_strict = Counter()
    network_failure_counts = Counter()
    urls_with_any_network_failure = 0
    skipped_private_target = []
    skipped_errors = []
    misclassified_rows = []

    started_at = time.monotonic()

    with app.app_context():
        for i, row in enumerate(rows, start=1):
            url = row["url"]
            true_label = row["true_label"]
            true_is_phishing = true_label == "phishing"

            try:
                report = scan_url(url)
            except APIError as exc:
                skipped_private_target.append({"url": url, "reason": exc.message})
                continue
            except Exception as exc:  # a single bad/unreachable URL must not kill a 500+ URL run
                skipped_errors.append({"url": url, "reason": f"{type(exc).__name__}: {exc}"})
                continue

            risk_level = report.risk_level
            predicted_phishing_lenient = risk_level in PHISHING_RISK_LEVELS_LENIENT
            predicted_phishing_strict = risk_level in PHISHING_RISK_LEVELS_STRICT

            for mapping_name, counts, predicted_phishing in (
                ("lenient", counts_lenient, predicted_phishing_lenient),
                ("strict", counts_strict, predicted_phishing_strict),
            ):
                if true_is_phishing and predicted_phishing:
                    counts["tp"] += 1
                elif true_is_phishing and not predicted_phishing:
                    counts["fn"] += 1
                elif not true_is_phishing and predicted_phishing:
                    counts["fp"] += 1
                else:
                    counts["tn"] += 1

            rule_results_by_name = {r.rule: r for r in report.rule_results}
            had_network_failure = False
            for rule_name in NETWORK_RULE_NAMES:
                if _rule_network_failed(rule_name, rule_results_by_name.get(rule_name)):
                    network_failure_counts[rule_name] += 1
                    had_network_failure = True
            if had_network_failure:
                urls_with_any_network_failure += 1

            lenient_wrong = true_is_phishing != predicted_phishing_lenient
            strict_wrong = true_is_phishing != predicted_phishing_strict
            if lenient_wrong or strict_wrong:
                triggered_rules = [r.rule for r in report.rule_results if r.triggered]
                misclassified_rows.append(
                    {
                        "url": url,
                        "true_label": true_label,
                        "trust_score": report.trust_score,
                        "risk_level": risk_level,
                        "predicted_phishing_lenient": predicted_phishing_lenient,
                        "predicted_phishing_strict": predicted_phishing_strict,
                        "wrong_under_lenient": lenient_wrong,
                        "wrong_under_strict": strict_wrong,
                        "had_network_failure": had_network_failure,
                        "triggered_rules": ";".join(triggered_rules),
                    }
                )

            if i % 25 == 0 or i == len(rows):
                elapsed = time.monotonic() - started_at
                print(f"  scanned {i}/{len(rows)} ({elapsed:.0f}s elapsed)...")

    elapsed_total = time.monotonic() - started_at

    scanned_total = len(rows) - len(skipped_private_target) - len(skipped_errors)
    print(f"\nCompleted {scanned_total} scans in {elapsed_total:.0f}s "
          f"({len(skipped_private_target)} rejected as private targets, "
          f"{len(skipped_errors)} raised an unexpected error and were skipped).")

    if skipped_errors:
        print("\nURLs skipped due to an unexpected error (not counted in any metric below):")
        for item in skipped_errors[:10]:
            print(f"  {item['url']} -> {item['reason']}")
        if len(skipped_errors) > 10:
            print(f"  ... and {len(skipped_errors) - 10} more")

    print("\n=== Network-dependent rule reliability ===")
    print(
        "(ssl_certificate, domain_age, redirect_check make live network calls; a failure here "
        "means the rule could not reach a verdict, NOT that it passed or failed the URL — it "
        "contributed 0 impact to that scan's score either way.)"
    )
    for rule_name in sorted(NETWORK_RULE_NAMES):
        failed = network_failure_counts[rule_name]
        pct = (failed / scanned_total * 100) if scanned_total else 0.0
        print(f"  {rule_name}: {failed}/{scanned_total} lookups failed ({pct:.1f}%)")
    pct_any = (urls_with_any_network_failure / scanned_total * 100) if scanned_total else 0.0
    print(f"  URLs with at least one network-rule failure: {urls_with_any_network_failure}/{scanned_total} ({pct_any:.1f}%)")

    phishing_scanned = sum(1 for r in rows if r["true_label"] == "phishing")
    legitimate_scanned = sum(1 for r in rows if r["true_label"] == "legitimate")
    print(f"\nDataset composition: {phishing_scanned} phishing URLs, {legitimate_scanned} legitimate URLs "
          f"({len(rows)} total in dataset.csv; {scanned_total} actually scored above).")

    print_mapping_report(
        "LENIENT mapping (Suspicious + Dangerous = predicted phishing)",
        counts_lenient["tp"], counts_lenient["fp"], counts_lenient["tn"], counts_lenient["fn"],
    )
    print_mapping_report(
        "STRICT mapping (only Dangerous = predicted phishing)",
        counts_strict["tp"], counts_strict["fp"], counts_strict["tn"], counts_strict["fn"],
    )

    if misclassified_rows:
        with open(MISCLASSIFIED_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(misclassified_rows[0].keys()))
            writer.writeheader()
            writer.writerows(misclassified_rows)
        print(f"\nWrote {len(misclassified_rows)} misclassified URLs (wrong under either mapping) to {MISCLASSIFIED_CSV}")
    else:
        print("\nNo misclassified URLs under either mapping — no misclassified.csv written.")


if __name__ == "__main__":
    main()
