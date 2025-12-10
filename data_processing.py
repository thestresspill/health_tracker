import pandas as pd


# ---------- CONFIG ----------
EXCEL_PATH = "Food Log Main.xlsx"

# Keep sheet names in one place so you can change easily later
SHEET_MAIN   = "Main Format 12 oct"
SHEET_DAILY  = "Daily 23 to 11oct"
SHEET_WEIGHT = "Weight Tracker 23sep"
SHEET_WORKOUT = "Workouts 19oct"


# ---------- CORE HELPERS ----------
def date_format(df, date_col="date"):
    df[date_col] = pd.to_datetime(df[date_col])
    df["year"] = df[date_col].dt.year
    df["week"] = df[date_col].dt.isocalendar().week
    df["day_name"] = df[date_col].dt.day_name()
    return df


def daily_agg(df):
    df_sum = df.groupby(["date"], as_index=False).agg(
        {
            "calories": "sum",
            "protein": "sum",
            "carbs": "sum",
            "fat": "sum",
            "sugar": "sum",
            "fiber": "sum",
        }
    )
    return df_sum


def week_agg(df):
    df_sum = df.groupby(["week"], as_index=False).agg(
        {
            "calories": "sum",
            "protein": "sum",
            "carbs": "sum",
            "fat": "sum",
            "sugar": "sum",
            "fiber": "sum",
        }
    )
    return df_sum


def week_avg(df):
    df_sum = df.groupby(["week"], as_index=False).agg(
        {
            "calories": "mean",
            "protein": "mean",
            "carbs": "mean",
            "fat": "mean",
            "sugar": "mean",
            "fiber": "mean",
        }
    ).round(2)
    return df_sum


def start_format(df1, df2):
    df1 = date_format(df1)
    daily_sum_df = daily_agg(df1)

    # Clean second sheet
    df2 = df2.copy()
    df2.drop(columns=["time", "entry_id", "item"], inplace=True, errors="ignore")
    df2.dropna(inplace=True)

    sum_df = pd.concat([daily_sum_df, df2], ignore_index=True)
    return sum_df


# ---------- MAIN PIPELINE ----------
def load_and_process(excel_path: str = EXCEL_PATH):
    # Read raw sheets
    inp1_df = pd.read_excel(excel_path, engine="openpyxl", sheet_name=SHEET_MAIN)
    inp2_df = pd.read_excel(excel_path, engine="openpyxl", sheet_name=SHEET_DAILY)
    inp3_df = pd.read_excel(excel_path, engine="openpyxl", sheet_name=SHEET_WEIGHT)
    inp4_df = pd.read_excel(excel_path, engine="openpyxl", sheet_name=SHEET_WORKOUT)

    # FOOD: daily + weekly
    daily_df = start_format(inp1_df, inp2_df)
    daily_df = date_format(daily_df)

    week_agg_df = week_agg(daily_df)
    avg_week_df = week_avg(daily_df)

    # Day-name averages
    day_name_avg = (
        daily_df.groupby(["day_name"], as_index=False)
        .agg(
            {
                "calories": "mean",
                "protein": "mean",
                "carbs": "mean",
                "fat": "mean",
                "sugar": "mean",
                "fiber": "mean",
            }
        )
        .round(2)
    )

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    day_name_avg["day_name"] = pd.Categorical(
        day_name_avg["day_name"], categories=day_order, ordered=True
    )
    day_name_avg = day_name_avg.sort_values("day_name").reset_index(drop=True)

    # WEIGHT
    wt_df = inp3_df.copy()
    wt_df.drop(columns=["source"], inplace=True, errors="ignore")
    wt_df = date_format(wt_df)
    wt_avg = (
        wt_df.groupby(["week"], as_index=False)
        .agg(
            {
                "weight_kg": "mean",
                "skeletal_muscle_kg": "mean",
                "fat_mass_kg": "mean",
                "body_water_kg": "mean",
            }
        )
        .round(1)
    )

    # WORKOUTS
    wk_df = inp4_df.copy()
    wk_df = date_format(wk_df)
    wk_df.drop(columns=["Day"], inplace=True, errors="ignore")

    workout_daily_agg = (
        wk_df.groupby(["date"], as_index=False)
        .agg({"Duration (min)": "sum", "Calories Burned": "sum"})
        .rename(columns={"Duration (min)": "duration_min"})
    )

    workout_agg = (
        wk_df.groupby(["week"], as_index=False)
        .agg({"Duration (min)": "sum", "Calories Burned": "sum"})
        .rename(columns={"Duration (min)": "duration_min"})
    )

    workout_avg = (
        wk_df.groupby(["week"], as_index=False)
        .agg({"Duration (min)": "mean", "Calories Burned": "mean"})
        .rename(columns={"Duration (min)": "duration_min"})
    )

    # COMBINED WEEKLY SUMMARY
    combined = pd.merge(wt_avg, avg_week_df, on="week", how="inner")
    combined = pd.merge(combined, workout_agg, on="week", how="outer")

    summary_list = ["week", "weight_kg", "calories", "Calories Burned"]
    summary_df = combined[summary_list]
    summary_df = summary_df.rename(
        columns={
            "week": "Week",
            "weight_kg": "Weight",
            "calories": "Avg Calorie Intake",
            "Calories Burned": "Total Calories Burned by Exercise",
        }
    )
    summary_df.fillna(0, inplace=True)

    return {
        "daily_df": daily_df,
        "week_agg_df": week_agg_df,
        "avg_week_df": avg_week_df,
        "day_name_avg": day_name_avg,
        "wt_avg": wt_avg,
        "workout_daily_agg": workout_daily_agg,
        "workout_agg": workout_agg,
        "workout_avg": workout_avg,
        "summary_df": summary_df,
    }
