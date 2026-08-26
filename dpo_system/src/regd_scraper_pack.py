from __future__ import annotations

import csv
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from dpo_system.src.sqlite_manager import DPODatabaseManager

REGD_ATOM_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&type=D&company=&dateb=&owner=include&start={start}&count={count}&output=atom"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_text(url: str, user_agent: str, timeout_sec: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout_sec) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_regd_atom(feed_xml: str) -> list[dict[str, str]]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(feed_xml)
    entries: list[dict[str, str]] = []

    for node in root.findall("atom:entry", ns):
        title = (node.findtext("atom:title", default="", namespaces=ns) or "").strip()
        entry_id = (node.findtext("atom:id", default="", namespaces=ns) or "").strip()
        updated = (node.findtext("atom:updated", default="", namespaces=ns) or "").strip()
        summary = (node.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        link_node = node.find("atom:link", ns)
        link = ""
        if link_node is not None:
            link = (link_node.attrib.get("href") or "").strip()

        entries.append(
            {
                "title": title,
                "entry_id": entry_id,
                "updated": updated,
                "summary": summary,
                "link": link,
            }
        )
    return entries


def _extract_accession(link: str) -> str:
    match = re.search(r"accession_number=([0-9-]+)", link)
    if match:
        return match.group(1)
    match = re.search(r"/([0-9]{10}-[0-9]{2}-[0-9]{6})(?:-index\.htm|/|$)", link)
    if match:
        return match.group(1)
    return ""


def _extract_date(text: str) -> str:
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if date_match:
        return date_match.group(1)
    return ""


def _extract_issuer_from_title(title: str) -> str:
    if " - " in title:
        return title.split(" - ", 1)[-1].strip()
    return title.strip()


def _extract_exemption(detail_html: str) -> str:
    match = re.search(r"(?:Rule|Section)\s+([0-9]+\([a-z]\)(?:\([0-9]+\))?)", detail_html, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def _extract_cik(detail_html: str) -> str:
    match = re.search(r"CIK\s*[:#]?\s*([0-9]{10})", detail_html, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def normalize_regd_entry(entry: dict[str, str], detail_html: str) -> dict[str, str]:
    source_url = entry.get("link", "")
    filing_date = _extract_date(entry.get("updated", "")) or _extract_date(entry.get("summary", ""))
    accession = _extract_accession(source_url)
    issuer_name = _extract_issuer_from_title(entry.get("title", ""))
    exemption = _extract_exemption(detail_html)
    cik = _extract_cik(detail_html)

    return {
        "filing_id": accession or entry.get("entry_id", ""),
        "filing_type": "RegD",
        "jurisdiction": "US",
        "issuer_name": issuer_name,
        "exemption_type": exemption,
        "filing_date": filing_date,
        "source_url": source_url,
        "accession_number": accession,
        "cik": cik,
        "fetched_at": _utc_now_iso(),
        "parser_version": "regd_scraper_pack_v1",
    }


def build_regd_enrichment_targets(filings: list[dict[str, str]]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for filing in filings:
        filing_id = str(filing.get("filing_id") or "").strip()
        issuer_name = str(filing.get("issuer_name") or "").strip()
        if not filing_id or not issuer_name:
            continue

        notes_parts = [
            "rss_seed_missing_phone",
            f"filing_type={str(filing.get('filing_type') or '').strip()}",
            f"issuer_name={issuer_name}",
            f"filing_date={str(filing.get('filing_date') or '').strip()}",
            f"source_url={str(filing.get('source_url') or '').strip()}",
        ]
        cik = str(filing.get("cik") or "").strip()
        accession_number = str(filing.get("accession_number") or "").strip()
        if cik:
            notes_parts.append(f"cik={cik}")
        if accession_number:
            notes_parts.append(f"accession_number={accession_number}")

        targets.append(
            {
                "lead_id": filing_id,
                "action_type": "enrich",
                "priority": "1",
                "jurisdiction": str(filing.get("jurisdiction") or "US").strip() or "US",
                "filing_type": str(filing.get("filing_type") or "").strip(),
                "issuer_name": issuer_name,
                "filing_date": str(filing.get("filing_date") or "").strip(),
                "source_url": str(filing.get("source_url") or "").strip(),
                "cik": cik,
                "accession_number": accession_number,
                "phone_number": "",
                "enrichment_status": "pending_phone_lookup",
                "notes": " | ".join(part for part in notes_parts if part),
            }
        )
    return targets


def run_regd_scrape(
    output_dir: str | Path,
    user_agent: str,
    max_entries: int = 200,
    page_size: int = 100,
    fetcher: Callable[[str, str], str] = fetch_text,
) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    filings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    fetched_entries = 0

    start = 0
    while fetched_entries < max_entries:
        url = REGD_ATOM_URL.format(start=start, count=page_size)
        try:
            feed_xml = fetcher(url, user_agent)
            entries = parse_regd_atom(feed_xml)
        except Exception as exc:
            errors.append({"stage": "feed_fetch", "url": url, "error": str(exc), "timestamp": _utc_now_iso()})
            break

        if not entries:
            break

        for entry in entries:
            if fetched_entries >= max_entries:
                break
            fetched_entries += 1
            detail_url = entry.get("link", "")
            detail_html = ""
            if detail_url:
                try:
                    detail_html = fetcher(detail_url, user_agent)
                except Exception as exc:
                    errors.append(
                        {
                            "stage": "detail_fetch",
                            "url": detail_url,
                            "entry_id": entry.get("entry_id", ""),
                            "error": str(exc),
                            "timestamp": _utc_now_iso(),
                        }
                    )
            filings.append(normalize_regd_entry(entry, detail_html))

        start += page_size

    csv_path = destination / "regd_filings.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "filing_id",
            "filing_type",
            "jurisdiction",
            "issuer_name",
            "exemption_type",
            "filing_date",
            "source_url",
            "accession_number",
            "cik",
            "fetched_at",
            "parser_version",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filings)

    enrichment_csv_path = destination / "regd_enrichment_targets.csv"
    enrichment_rows = build_regd_enrichment_targets(filings)
    with enrichment_csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "lead_id",
            "action_type",
            "priority",
            "jurisdiction",
            "filing_type",
            "issuer_name",
            "filing_date",
            "source_url",
            "cik",
            "accession_number",
            "phone_number",
            "enrichment_status",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enrichment_rows)

    raw_jsonl_path = destination / "regd_raw_entries.jsonl"
    with raw_jsonl_path.open("w", encoding="utf-8") as handle:
        for filing in filings:
            handle.write(json.dumps(filing, ensure_ascii=True) + "\n")

    error_jsonl_path = destination / "regd_error_ledger.jsonl"
    with error_jsonl_path.open("w", encoding="utf-8") as handle:
        for error in errors:
            handle.write(json.dumps(error, ensure_ascii=True) + "\n")

    manifest = {
        "run_at": _utc_now_iso(),
        "records": len(filings),
        "errors": len(errors),
        "max_entries": max_entries,
        "page_size": page_size,
        "csv": str(csv_path),
        "enrichment_csv": str(enrichment_csv_path),
        "raw_jsonl": str(raw_jsonl_path),
        "error_jsonl": str(error_jsonl_path),
    }

    manifest_path = destination / "regd_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest


def seed_regd_feed_to_db(
    db_path: str | Path,
    output_dir: str | Path,
    user_agent: str,
    max_entries: int = 200,
    page_size: int = 100,
    fetcher: Callable[[str, str], str] = fetch_text,
) -> dict[str, Any]:
    """Scrape the SEC RegD Atom feed and ingest every filing as a standard lead."""
    manifest = run_regd_scrape(
        output_dir=output_dir,
        user_agent=user_agent,
        max_entries=max_entries,
        page_size=page_size,
        fetcher=fetcher,
    )

    csv_path = Path(manifest["csv"])
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        return {
            "records_ingested": 0,
            "lead_keys": [],
            "source_system": "SEC_REGD_RSS",
            "manifest": manifest,
        }

    manager = DPODatabaseManager(str(db_path))
    lead_keys: list[str] = []
    for row in rows:
        lead_key = manager.ingest_lead(
            lane_type="standard",
            raw_id=row.get("filing_id") or row.get("accession_number") or row.get("issuer_name") or "SEC-RegD",
            source_system="SEC_REGD_RSS",
            entity_name=row.get("issuer_name") or "Unknown SEC Issuer",
            email=None,
            phone=None,
            segment="regd_enrichment",
        )
        lead_keys.append(lead_key)

    return {
        "records_ingested": len(lead_keys),
        "lead_keys": lead_keys,
        "source_system": "SEC_REGD_RSS",
        "manifest": manifest,
    }
