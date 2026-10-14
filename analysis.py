
## analysis.py
## question: in which month is the swell most surfable in hossegor, peniche and taghazout, and how consistent is that from year to year?
## input: wave_data.csv (from download_data.py)
## output: monthly_results.csv, surfable_fraction.png, winter_by_year.png (also prints the share of days above H_MAX)
## run: python3 analysis.py

import numpy as np ## for the maths
import pandas as pd ## for tables ("DataFrames") and grouping
import matplotlib.pyplot as plt ## for plotting

# --- settings 

INFILE = "wave_data.csv" ## the data file made by download_data.py
H_MIN, H_MAX = 1.0, 3 ## surfable wave height range [m]
T_MIN = 8.0 ## minimum wave period [s]
SEASON_MONTHS = [12, 1, 2] ## months used for the year-by-year plot (Dec-Feb)
SEASON_NAME = "Dec-Feb" ## label for that season in titles and prints

## plot colour per region 
COLORS = {"Hossegor": "cadetblue", "Peniche": "burlywood", "Taghazout": "green"}

## ---

## month names for the x axis (index 0 = January)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_and_clean(path):
    ## read the CSV, drop missing values, and build daily means

    df = pd.read_csv(path, parse_dates=["time"]) ## read file, turn "time" column into dates
    df = df.dropna(subset=["wave_height", "wave_period"]) ## remove rows with a missing value (safety; there are none)
    df["date"] = df["time"].dt.floor("D") ## cut the hour off: 2020-01-05 13:00 -> 2020-01-05
    daily = (df.groupby(["region", "date"]) ## one group per region and day
               [["wave_height", "wave_period"]] ## use only these two columns
               .mean().reset_index()) ## mean of the 24 hourly values = daily mean
    daily["year"] = daily["date"].dt.year ## add a year column
    daily["month"] = daily["date"].dt.month ## add a month column (1-12)
    ## a day is surfable if height is between H_MIN and H_MAX AND period >= T_MIN
    ## (result is True/False for each day)
    daily["surfable"] = (daily["wave_height"].between(H_MIN, H_MAX)
                         & (daily["wave_period"] >= T_MIN))
    return daily ## table with one row per region and day


def yearly_subsamples(daily):
    ## one value per (region, month, year): the subsample is one year

    return (daily.groupby(["region", "month", "year"]) ## e.g. peniche, january, 2018
                 .agg(surfable_pct=("surfable", lambda s: 100 * s.mean()), ## mean of True/False = fraction; x100 = percent
                      mean_height=("wave_height", "mean")) ## average wave height in that month
                 .reset_index()) ## make the group labels normal columns again


def summarise(sub):
    ## mean over years and standard error s / sqrt(N_years)

    def sem(x): ## standard error of a list of values x
        return x.std(ddof=1) / np.sqrt(len(x)) ## s / sqrt(N); ddof=1 divides by N-1
    out = (sub.groupby(["region", "month"]) ## one group per region and month (10 years each)
              .agg(surfable_mean=("surfable_pct", "mean"), ## mean over the 10 years
                   surfable_err=("surfable_pct", sem), ## standard error over the 10 years
                   height_mean=("mean_height", "mean"), ## same two numbers for wave height
                   height_err=("mean_height", sem),
                   n_years=("year", "nunique")) ## number of years (should be 10)
              .reset_index()) ## group labels back to columns
    return out ## the results table


def season_table(sub):
    ## surfable days [%] in the season months of each year, per region

    return (sub[sub["month"].isin(SEASON_MONTHS)] ## keep only dec, jan, feb rows
            .groupby(["region", "year"])["surfable_pct"] ## one group per region and year
            .mean() ## mean of the three monthly percentages
            .unstack("region")) ## years as rows, one column per region


def big_day_share(daily):
    ## share of days [%] with daily mean wave height above H_MAX, per region

    big = daily["wave_height"] > H_MAX  ## true for days that are too big
    monthly = (big.groupby([daily["region"], daily["month"]]) ## share of big days per region and month
                  .mean().unstack("region") * 100) ## months as rows, regions as columns, in percent
    season = (big[daily["month"].isin(SEASON_MONTHS)] ## only the season days (dec-feb)
              .groupby(daily["region"]).mean() * 100) ## share of big days per region, in percent
    return monthly, season


def plot(res, column, err_column, ylabel, title, filename):
    ## monthly plot with error bars, one line per region

    fig, ax = plt.subplots(figsize=(8, 5.5)) ## create an empty figure (8 x 5.5 inches)
    for region, g in res.groupby("region"): ## loop over the three regions
        ax.errorbar(g["month"], g[column], yerr=g[err_column], ## x = month, y = value, error bar = standard error
                    marker="o", capsize=3, label=region, ## round markers, small caps on bars, legend label
                    color=COLORS[region]) ## colour from the settings at the top
    ax.set_xticks(range(1, 13)) ## one tick for each month 1-12
    ax.set_xticklabels(MONTHS) ## write jan, feb, ... instead of 1, 2, ...
    ax.set_xlabel("Month") ## x axis label
    ax.set_ylabel(ylabel) ## y axis label (given as input)
    ax.set_title(title) ## title (given as input)
    ax.grid(alpha=0.3) ## light grid lines
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ## legend below the plot ...
              ncol=3, frameon=False) ## ... in one row, without a frame
    fig.subplots_adjust(left=0.11, right=0.97, top=0.92, bottom=0.27) ## fixed margins: all plots get the same size
    fig.savefig(filename, dpi=200) ## save as PNG file
    plt.close(fig) ## close the figure to free memory


def plot_season(season, filename):
    ## season value per year, one line per region

    fig, ax = plt.subplots(figsize=(8, 5.5)) ## same figure size as the other plot
    for region in season.columns: ## loop over the three regions
        ax.plot(season.index, season[region], marker="o", ## x = years, y = season value
                linewidth=2, color=COLORS[region], label=region)
    ax.set_xticks(list(season.index)) ## one tick per year
    ax.set_xticklabels([str(y) for y in season.index]) ## year numbers as text (no decimals)
    ax.set_xlabel("Year") ## x axis label
    ax.set_ylabel("Surfable days [%]") ## y axis label
    ax.set_title(f"Surfable days per year ({SEASON_NAME})") ## title with the season name
    ax.grid(alpha=0.3) ## light grid lines
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ## legend below the plot, as in plot()
              ncol=3, frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.92, bottom=0.27) ## same margins as plot()
    fig.savefig(filename, dpi=200) ## save as PNG file
    plt.close(fig) ## close the figure


def main():
    daily = load_and_clean(INFILE) ## step 1: daily data with a surfable True/False
    sub = yearly_subsamples(daily) ## step 2: one value per region, month and year
    res = summarise(sub) ## step 3: mean and standard error over the years
    res.to_csv("monthly_results.csv", index=False) ## save the results table

    plot(res, "surfable_mean", "surfable_err", ## main plot: surfable days per month
         "Surfable days [%]",
         f"Surfable days per month ({H_MIN}-{H_MAX} m, period >= {T_MIN:.0f} s)",
         "surfable_fraction.png")

    print("Best month per region (mean over years +/- standard error):")
    for region, g in res.groupby("region"): ## loop over the regions
        best = g.loc[g["surfable_mean"].idxmax()] ## row with the highest surfable percentage
        print(f"  {region}: {MONTHS[int(best['month']) - 1]}, " ## month name
              f"{best['surfable_mean']:.1f} +/- {best['surfable_err']:.1f} % " ## value +/- error
              f"surfable days (N = {int(best['n_years'])} years)")

    ## year-by-year consistency
    season = season_table(sub) ## dec-feb value for each year and region
    plot_season(season, "winter_by_year.png") ## plot it
    print(f"\nSurfable days per year ({SEASON_NAME}) [%]:")
    print(season.round(1)) ## table of the yearly values
    print("\nMean, standard deviation, min and max over the years:")
    print(season.agg(["mean", "std", "min", "max"]).round(1)) ## summary numbers per region

    ## days that are too big (mean height above H_MAX)
    monthly_big, season_big = big_day_share(daily) ## share of days above H_MAX
    print(f"\nDays with mean wave height above {H_MAX} m [%], per month:")
    monthly_big.index = MONTHS ## use month names instead of 1-12
    print(monthly_big.round(1))
    print(f"\nDays above {H_MAX} m in {SEASON_NAME} [%]:")
    print(season_big.round(1))

    n = len(season) ## number of years (10)
    for other in ["Peniche", "Hossegor"]: ## compare taghazout with each other region
        k = (season["Taghazout"] > season[other]).sum() ## count the years where taghazout is higher
        print(f"Taghazout > {other} in {k} of {n} years")


if __name__ == "__main__": ## run main() only when this file is run directly, not when imported
    main()