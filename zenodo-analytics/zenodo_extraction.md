# Zenodo Community Metadata Extraction Script

## Description

This script extracts metadata and usage metrics from a Zenodo community using the public API and exports the results into a structured CSV file.

It is designed to support the analysis of Open Educational Resources (OERs) and enables the creation of reproducible datasets for studying multilingual dissemination, usage patterns, and knowledge circulation.

## Functionality

The script retrieves records from a specified Zenodo community and extracts the following variables:

- record identifier  
- title  
- language  
- downloads  
- views  
- DOI  
- publication date  
- creation date  
- resource type  

The extracted data are exported to a CSV file for further analysis.

## Usage

Run the script from the command line:

python zenodo_extraction.py --community <community_name> --out <output_file.csv>

### Example
python zenodo_extraction.py --community gedis --out dataset.csv


## Requirements

- Python 3.x  
- requests library  

Install dependencies:

pip install requests


## Output

The script generates a CSV file containing structured metadata and usage metrics for all records in the selected Zenodo community.

## Notes

- Data are retrieved via the Zenodo REST API  
- Only aggregated metadata are collected  
- No personal or user-identifiable information is included  
- A small delay between requests is implemented to respect API usage  

## Reproducibility

This script is part of a reproducible research workflow. The dataset generated using this script is published separately with a DOI.

## Author

Juan-José Boté-Vericad  
Universitat de Barcelona
