from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(label: str, cmd: list[str]) -> None:
    print(f"[RUN] {label}: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(f"[FAIL] {label} (exit={result.returncode})")
    print(f"[OK] {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scraper + normalize pipeline")
    parser.add_argument("--python", default=sys.executable, help="Python executable")
    parser.add_argument(
        "--scraper",
        action="append",
        default=[],
        help="Path to scraper script (repeatable). Example: --scraper scrapers/scrape_source_a.py",
    )
    parser.add_argument(
        "--normalize",
        default="pipelines/normalize_feeds.py",
        help="Normalizer script path",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]

    for scraper in args.scraper:
        run_step(f"scraper:{scraper}", [args.python, str(repo_root / scraper)])

    run_step("normalize", [args.python, str(repo_root / args.normalize)])

    print("[DONE] Ingestion pipeline completed successfully.")


if __name__ == "__main__":
    main()
