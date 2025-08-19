# MRI Temperature Correlation Analysis

This script processes MRI-derived metrics (**FA, MD, T1, T2, T2\***)
across deep gray matter regions and correlates them with forehead temperature
measurements taken during scanning.  

## Features
- **Input**  
  - Subject-wise CSV outputs from NIfTI-based MRI analysis  
  - Excel file with corresponding forehead temperatures  

- **Processing**  
  - Merges MRI parameter data  
  - Maps MRI metrics to relevant temperature values  
  - Computes Pearson correlations, linear regressions, R², slopes, and confidence intervals  

- **Output**  
  - Publication-ready scatter plots with regression lines (**PNG** & **SVG**)  
  - Summary table with correlation statistics (**CSV**)  
  - Standalone color-coded region legend  

## Customization
- Adjustable input/output paths  
- Flexible grouping of brain structures  
- Configurable plot style and font sizes  

---

This workflow provides an automated pipeline for exploring relationships between forehead temperature and MRI parameters in deep gray matter substructures.
The fitted linear models (intercept a and slope b) can be used to correct postmortem MRI parameters for temperature.
