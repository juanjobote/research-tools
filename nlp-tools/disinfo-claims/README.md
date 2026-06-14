# Electoral Disinformation Claims — EUvsDisinfo (2024–2025)

Reproducible extraction pipeline for the dataset of electoral disinformation
claims used in the study *"Narrativas de desinformación electoral: framing,
legitimidad y estructuras discursivas en contextos geopolíticos"*.

## Overview

The raw export from the EUvsDisinfo database (https://euvsdisinfo.eu) lists
records as alternating lines:

```
21.02.2025
DISINFO: German election result known in advance
17.03.2024
DISINFO: Pope Francis congratulated Putin on his re-election
...
```

This script normalises the export into a tabular dataset:

| Date       | Title                                            |
|------------|--------------------------------------------------|
| 21/02/2025 | German election result known in advance          |
| 17/03/2024 | Pope Francis congratulated Putin on his re-election |

## Pipeline steps

1. **Read** the raw EUvsDisinfo export.
2. **Normalise dates** from `dd.mm.yyyy` to `dd/mm/yyyy` (and ISO `yyyy-mm-dd`).
3. **Strip** the editorial prefix `DISINFO: ` from each claim.
4. **Validate** pairing and report duplicate titles.
5. **Export** to CSV (`;`-delimited, UTF-8 BOM, Excel-friendly) and XLSX.

## Usage

```bash
python extract_disinfo_claims.py raw_input.txt -o output/
```

Options:

- `-o, --output-dir`  output directory (default: current).
- `--no-xlsx`         skip XLSX export.

Requires Python ≥ 3.9. Optional dependency: `openpyxl` (for XLSX export).

```bash
pip install openpyxl
```

## Methodological note

Initial record retrieval from EUvsDisinfo was performed using the keyword
`election` over the period 2024–2025, returning 347 candidate cases. A
systematic sample of 120 cases was then exported and processed through this
pipeline. The remaining qualitative coding (narrative categorisation,
country attribution, inclusion criteria, semantic repetition clusters) was
performed in ATLAS.ti v26; intercoder reliability was assessed via
Krippendorff's alpha (α = 0.82).

The final analytical corpus contains 98 cases meeting the inclusion criterion
(explicit reference to elections, electoral processes, referenda or vote
integrity). The 22 excluded cases are retained in the dataset with
`Inclusion = 0` for transparency.

## Data and citation

- **Dataset** (curated, with narrative coding): Zenodo, DOI: *to be assigned*.
- **Code**: this repository.

## License

- Code: MIT
- Data: CC-BY 4.0

## Author

Juan-José Boté-Vericad
Universitat de Barcelona — Facultat d'Informació i Mitjans Audiovisuals
UBICS — Institut de Sistemes Complexos
`juanjo.botev@ub.edu`

