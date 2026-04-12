#!/usr/bin/env python3

"""
Zenodo Community Metadata Extraction Script

Extracts metadata and usage metrics from a Zenodo community
and exports them to a CSV file for analysis.

Usage example:
    python script.py --community gedis --out dataset.csv

Requirements:
    - Python 3.x
    - requests library

Author: Juan-José Boté-Vericad
Year: 2026
"""

import argparse
import csv
import requests
import time


def get_records(community, size=25):
    """
    Generator that retrieves records from a Zenodo community.
    """
    url = "https://zenodo.org/api/records"
    params = {
        "communities": community,
        "size": size,
        "all_versions": False,
        "sort": "newest"
    }

    while True:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise Exception(f"Error fetching data: {response.status_code}")

        data = response.json()
        records = data.get("hits", {}).get("hits", [])

        for r in records:
            yield r

        next_url = data.get("links", {}).get("next")
        if not next_url:
            break

        url = next_url
        params = None
        time.sleep(0.2)


def extract_record(r):
    """
    Extract relevant metadata fields from a Zenodo record.
    """
    metadata = r.get("metadata", {})

    return {
        "id": r.get("id"),
        "title": metadata.get("title"),
        "language": metadata.get("language"),
        "downloads": r.get("stats", {}).get("downloads", 0),
        "views": r.get("stats", {}).get("views", 0),
        "doi": r.get("doi"),
        "publication_date": metadata.get("publication_date"),
        "created": r.get("created"),
        "resource_type": metadata.get("resource_type", {}).get("type")
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata and usage metrics from a Zenodo community."
    )
    parser.add_argument("--community", required=True, help="Zenodo community name")
    parser.add_argument("--out", default="zenodo_stats.csv", help="Output CSV file")

    args = parser.parse_args()

    rows = []

    print(f"Fetching records from community: {args.community}")

    for record in get_records(args.community):
        rows.append(extract_record(record))

    if not rows:
        print("No records found.")
        return

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Export completed: {args.out}")
    print(f"Total records exported: {len(rows)}")


if __name__ == "__main__":
    main()