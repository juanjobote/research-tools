#!/usr/bin/env python3
"""
extract_disinfo_claims.py
=========================

Reproducible extraction and normalisation pipeline for the EUvsDisinfo
electoral disinformation dataset (2024–2025).

This script transforms the raw list of records exported from EUvsDisinfo
(https://euvsdisinfo.eu) into a structured tabular dataset suitable for
qualitative content analysis and downstream computational modelling.

Pipeline:
    1. Read raw EUvsDisinfo export (alternating date / title lines).
    2. Normalise dates from dd.mm.yyyy to dd/mm/yyyy (ISO-style fallback also produced).
    3. Strip the editorial prefix "DISINFO: " from each claim.
    4. Validate pairing and detect duplicates.
    5. Export to CSV (";" delimiter, UTF-8 BOM) and to XLSX.

Author : Juan-José Boté-Vericad — Universitat de Barcelona
License: CC-BY 4.0 (data) / MIT (code)
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

DISINFO_PREFIX_RE = re.compile(r"^DISINFO:\s*", flags=re.IGNORECASE)


def parse_raw(path: Path) -> list[dict]:
    """Parse an EUvsDisinfo raw export.

    The expected format alternates a date line (dd.mm.yyyy) and a title
    line prefixed with 'DISINFO: '. Blank lines are ignored.
    """
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(lines) % 2 != 0:
        raise ValueError(
            f"Odd number of non-empty lines ({len(lines)}). "
            "Each record must consist of a date line followed by a title line."
        )

    records: list[dict] = []
    for i in range(0, len(lines), 2):
        raw_date, raw_title = lines[i], lines[i + 1]
        try:
            d = datetime.strptime(raw_date, "%d.%m.%Y")
        except ValueError as exc:
            raise ValueError(f"Invalid date at line {i + 1}: {raw_date!r}") from exc

        title = DISINFO_PREFIX_RE.sub("", raw_title).strip()

        records.append(
            {
                "date_eu": d.strftime("%d/%m/%Y"),
                "date_iso": d.strftime("%Y-%m-%d"),
                "year": d.year,
                "title": title,
            }
        )
    return records


def report_duplicates(records: list[dict]) -> None:
    """Report duplicate titles, if any."""
    titles = [r["title"] for r in records]
    seen, dups = set(), []
    for t in titles:
        if t in seen:
            dups.append(t)
        seen.add(t)
    if dups:
        print(f"[warn] {len(dups)} duplicate title(s) detected:", file=sys.stderr)
        for t in dups:
            print(f"  - {t}", file=sys.stderr)
    else:
        print(f"[ok] {len(records)} unique records, no duplicates.")


def write_csv(records: list[dict], out_path: Path) -> None:
    """Write the dataset to CSV with ';' delimiter and UTF-8 BOM (Excel-friendly)."""
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Date", "Title"])
        for r in records:
            writer.writerow([r["date_eu"], r["title"]])
    print(f"[ok] CSV written: {out_path}")


def write_xlsx(records: list[dict], out_path: Path) -> None:
    """Optional XLSX export (requires openpyxl)."""
    try:
        from openpyxl import Workbook
    except ImportError:
        print("[skip] openpyxl not installed; XLSX export skipped.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Claims"
    ws.append(["ID", "Date", "Year", "Title"])
    for idx, r in enumerate(records, start=1):
        ws.append([idx, r["date_eu"], r["year"], r["title"]])
    wb.save(out_path)
    print(f"[ok] XLSX written: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to raw EUvsDisinfo text export.")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path("."),
        help="Output directory (default: current directory).",
    )
    parser.add_argument("--no-xlsx", action="store_true", help="Skip XLSX export.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    records = parse_raw(args.input)
    report_duplicates(records)

    write_csv(records, args.output_dir / "disinfo_claims.csv")
    if not args.no_xlsx:
        write_xlsx(records, args.output_dir / "disinfo_claims.xlsx")

    print(f"[done] {len(records)} records processed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
