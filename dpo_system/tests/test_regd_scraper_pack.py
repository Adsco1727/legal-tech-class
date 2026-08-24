from __future__ import annotations

import csv
import json
from pathlib import Path

from dpo_system.src.regd_scraper_pack import parse_regd_atom, run_regd_scrape


ATOM_SAMPLE = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<feed xmlns=\"http://www.w3.org/2005/Atom\">
  <entry>
    <title>D - Example Issuer Inc</title>
    <id>tag:sec.gov,2008:accession-number=0001234567-26-000001</id>
    <updated>2026-08-12T12:00:00-04:00</updated>
    <summary>Filed: 2026-08-12 AccNo: 0001234567-26-000001</summary>
        <link href=\"https://www.sec.gov/Archives/edgar/data/1234567/0001234567-26-000001-index.htm\"/>
  </entry>
</feed>
"""

DETAIL_SAMPLE = """
<html>
<body>
Rule 506(b)
Issuer CIK 0001234567
</body>
</html>
"""


def test_parse_regd_atom_extracts_entries() -> None:
    entries = parse_regd_atom(ATOM_SAMPLE)

    assert len(entries) == 1
    assert entries[0]["title"] == "D - Example Issuer Inc"
    assert entries[0]["link"].startswith("https://www.sec.gov/Archives")


def test_run_regd_scrape_writes_outputs(tmp_path: Path) -> None:
    def fake_fetch(url: str, user_agent: str) -> str:
        if "output=atom" in url:
            return ATOM_SAMPLE
        return DETAIL_SAMPLE

    manifest = run_regd_scrape(
        output_dir=tmp_path,
        user_agent="TestAgent/1.0",
        max_entries=1,
        page_size=1,
        fetcher=fake_fetch,
    )

    assert manifest["records"] == 1
    assert manifest["errors"] == 0

    csv_path = Path(manifest["csv"])
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["filing_type"] == "RegD"
    assert rows[0]["jurisdiction"] == "US"
    assert rows[0]["issuer_name"] == "Example Issuer Inc"
    assert rows[0]["exemption_type"] == "506(b)"
    assert rows[0]["accession_number"] == "0001234567-26-000001"
    assert rows[0]["cik"] == "0001234567"

    enrichment_csv_path = Path(manifest["enrichment_csv"])
    with enrichment_csv_path.open("r", encoding="utf-8", newline="") as handle:
        enrichment_rows = list(csv.DictReader(handle))

    assert len(enrichment_rows) == 1
    assert enrichment_rows[0]["lead_id"] == "0001234567-26-000001"
    assert enrichment_rows[0]["action_type"] == "enrich"
    assert enrichment_rows[0]["phone_number"] == ""
    assert enrichment_rows[0]["enrichment_status"] == "pending_phone_lookup"

    manifest_path = tmp_path / "regd_run_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["records"] == 1
    assert payload["enrichment_csv"] == str(enrichment_csv_path)
