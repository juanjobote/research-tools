# Zenodo Analytics

This module contains tools for extracting metadata and usage metrics from Zenodo communities.

## Description

The purpose of this component is to provide a reproducible and structured way to retrieve Open Educational Resources (OERs) metadata from Zenodo using its public API. The extracted data serve as the foundational layer for subsequent analysis of multilingual dissemination, usage patterns, and knowledge circulation.

## Scope

The tools included in this directory are designed to:

- retrieve records from a specified Zenodo community  
- extract key metadata and usage indicators (e.g. downloads, views, language)  
- export the data into structured formats (CSV) for further analysis  

## Main Script

- `zenodo_extraction.py`  
  Script for metadata extraction and dataset generation.

## Output

The script generates a dataset containing:

- record identifier  
- title  
- language  
- downloads  
- views  
- DOI  
- publication date  
- creation date  
- resource type  

This dataset is used as the empirical basis for analysing OER dissemination and usage.

## Reproducibility

This module is part of a reproducible research workflow. The dataset generated using these tools is published separately with a DOI and can be used to replicate the analyses presented in related studies.

## Context

This work is developed within the broader research framework on:

- Open Educational Resources (OER)  
- multilingual knowledge circulation  
- information behaviour in digital repositories  

## Author

Juan-José Boté-Vericad  
Universitat de Barcelona
