

\# Diamond Value Model (DVM)



\## Overview

Diamond Value Model is a Python-based MLB player

performance and economic valuation project.



DVM combines baseball statistics with financial

analysis to explore player value.



\## Current Version

Pipeline v0.1 — 2025 Los Angeles Dodgers



\## Features

\- Automated MLB statistics retrieval

\- Baseball-Reference batting and pitching WAR

\- Player matching using MLBAM IDs

\- Combined WAR for two-way players

\- Preliminary WAR-based market valuations

\- Excel reports with three worksheets

\- Automated data validation



\## Valuation Methodology

Base Market Value = Total bWAR × $8,000,000



The $8 million per WAR figure is an illustrative

assumption, not an independently calibrated

market valuation.



\## Data Sources

\- MLB Stats API

\- Baseball-Reference data through pybaseball



\## Running the Pipeline

Install dependencies from requirements.txt.



Run:

python run\_dvm.py



\## Limitations

\- Currently supports the 2025 Dodgers.

\- Contract costs and economic surplus are not yet integrated.

\- Injury and age risk adjustments are planned.

\- Negative WAR produces negative theoretical values.

\- The model has not yet been backtested.



\## Roadmap

\- Expand to additional MLB teams

\- Integrate player contracts and economic surplus

\- Develop injury and age risk adjustments

\- Build interactive Power BI dashboards

\- Develop trade and extension analysis



