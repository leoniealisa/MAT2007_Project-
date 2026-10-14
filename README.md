## MAT2007_Project
When to surf the Atlantic coast?
In which months is the swell most surfable in Hossegor, Peniche, and Taghazout, and how consistent is that from year to year?

---
## Dataset

Hourly wave height and wave period for 2016 - 2025 from the ERA5-Ocean reanalysis, downloaded through the free Open-Meteo Marine API (no account or key needed). The downloaded data is also included as wave_data.cvs.
Cleaning: no manual cleaning is needed, the data has no missing values. analysis.py averages the hourly values to daily means as part of the analysis. 

---
## Files

- download_data.py : downloads the data and saves wave_data.csv
- analysis.py : computes the results and makes the plots
- report.pdf : a 2-page report

---
## Requirements 

- Python 3
- Packages: pandas, requests, matplotlib

---
## How to run

pip3 install pandas requests matplotlib
python3 download_data.py
python3 analysis.py 
