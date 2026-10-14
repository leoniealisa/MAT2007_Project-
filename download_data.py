
## download_data.py
## downloads hourly wave height and wave period (ERA5-Ocean reanalysis, via the
## Open-Meteo Marine API) for three atlantic surf regions and saves one CSV.

## Run:  python3 download_data.py
## Output: wave_data.csv  (columns: region, time, wave_height, wave_period)


import time ## time.sleep: wait between requests so that the website doesn't crash or reject us
import pandas as pd ## pandas: tables and saving to CSV
import requests ## requests: download data from a web address

## --- settings 

## coordinates (latitude, longitude) are slightly offshore. ERA5-Ocean has a
## ~50 km grid, so the API uses the nearest grid point.
REGIONS = {
    "Hossegor": (43.7, -2.0),
    "Peniche": (39.4, -9.8),
    "Taghazout": (30.5, -10.2),
}
START_YEAR = 2016 ## first year to download
END_YEAR = 2025 ## last year (full years only; ERA5 lags real time by ~5 days)
OUTFILE = "wave_data.csv" ## name of the file that is saved

URL = "https://marine-api.open-meteo.com/v1/marine" ## address of the API

## ---

def fetch_year(lat, lon, year):
    ## download one year of hourly data for one coordinate

    params = { ## the "question" we send to the API
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01", ## first day of the year
        "end_date": f"{year}-12-31", ## last day of the year
        "hourly": "wave_height,wave_period", ## the two variables we want
        "models": "era5_ocean", ## use the ERA5-Ocean reanalysis
        "timezone": "GMT", ## times in GMT
    }
    response = requests.get(URL, params=params, timeout=60) ## send the request (give up after 60 s)
    response.raise_for_status() ## stop with a clear error if the request failed
    hourly = response.json()["hourly"] ## the answer is JSON; take the "hourly" part
    return pd.DataFrame(hourly) ## turn it into a table (time, wave_height, wave_period)


def check_grid():
    ## print which ERA5-Ocean grid point the API actually uses for each region

    print("\nGrid points used by the API:")
    for region, (lat, lon) in REGIONS.items(): ## loop over the three regions
        r = requests.get(URL, params={ ## request just 2 days: we only want the coordinates
            "latitude": lat, "longitude": lon,
            "start_date": "2020-01-01", "end_date": "2020-01-02",
            "hourly": "wave_height", "models": "era5_ocean"}, timeout=60)
        data = r.json() ## the answer as a Python dictionary
        print(f"  {region}: requested ({lat}, {lon}) -> "
              f"grid point ({data['latitude']}, {data['longitude']})") ## API returns the grid point it used


def main():
    frames = [] ## list that collects one table per region and year
    for region, (lat, lon) in REGIONS.items(): ## loop over the three regions
        for year in range(START_YEAR, END_YEAR + 1): ## loop over the years (END_YEAR + 1 because range stops before the end)
            print(f"Downloading {region} {year} ...") ## progress message
            df = fetch_year(lat, lon, year) ## download this region and year
            df["region"] = region ## add a column saying which region it is
            frames.append(df) ## store the table in the list
            time.sleep(1) ## wait 1 second to be polite to the free API

    data = pd.concat(frames, ignore_index=True) ## stack all tables into one big table
    data = data[["region", "time", "wave_height", "wave_period"]] ## put the columns in a fixed order
    data.to_csv(OUTFILE, index=False) ## save as CSV (without the row numbers)

    ## quick sanity check
    print(f"\nSaved {len(data)} rows to {OUTFILE}")
    print(data.groupby("region")[["wave_height", "wave_period"]].describe().T) ## summary numbers per region
    print("\nMissing values per column:")
    print(data.isna().sum()) ## count missing values (should be 0)

    check_grid() ## show which grid points were used


if __name__ == "__main__": ## run main() only when this file is run directly, not when imported
    main()