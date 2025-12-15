import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

# Assuming data_processing.py and EXCEL_PATH are defined correctly
from data_processing import load_and_process, EXCEL_PATH 

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Food & Fitness Dashboard",
    # layout="wide", # Uncomment if you prefer a wider layout
)

st.markdown("""
    <style>
        .main {
            max-width: 900px;
            margin: 0 auto;
        }
    </style>
""", unsafe_allow_html=True)


st.title("📊 Food, Weight & Workout Dashboard")


# --- DATA LOADING ---
@st.cache_data
def get_data():
    """Loads and processes data, cached for performance."""
    return load_and_process(EXCEL_PATH)

try:
    data = get_data()

except FileNotFoundError:
    st.error(f"Excel file `{EXCEL_PATH}` not found. Place it in the same folder as app.py.")
    st.stop()

except Exception as e:
    st.error(f"Error while loading data: {e}")
    st.stop()

# Unpack data dictionaries
daily_df        = data["daily_df"]
avg_week_df     = data["avg_week_df"]
wt_avg          = data["wt_avg"]
day_name_avg    = data["day_name_avg"]
workout_agg     = data["workout_agg"]
summary_df      = data["summary_df"]


# --- TOP SUMMARY CARDS (REVISED FOR ROBUSTNESS) ---

# Find the latest week number. Use 0 if the DataFrame is empty.
latest_week = int(avg_week_df["week"].max()) if not avg_week_df.empty else 0

# --- Safely retrieve Calories ---
# Checks if the filter returns any row before calling .iloc[0]
cal_series = avg_week_df.loc[avg_week_df["week"] == latest_week, "calories"]
latest_week_cal = cal_series.iloc[0] if not cal_series.empty else 0

# --- Safely retrieve Weight ---
weight_series = wt_avg.loc[wt_avg["week"] == latest_week, "weight_kg"]
# Use None if missing, and we will handle the display later
latest_weight = weight_series.iloc[0] if not weight_series.empty else None 

# --- Safely retrieve Workout Calories ---
latest_workout = workout_agg.loc[workout_agg["week"] == latest_week, :]
latest_workout_cal = (
    latest_workout["Calories Burned"].iloc[0]
    if not latest_workout.empty and "Calories Burned" in latest_workout.columns
    else 0
)

col1, col2, col3 = st.columns(3)

col1.metric("Latest Week", latest_week)
col2.metric("Avg Calories (Latest Week)", f"{latest_week_cal:,.0f} kcal")

# Handle missing weight gracefully in the display
weight_display = f"{latest_weight:,.1f} kg" if latest_weight is not None else "N/A"
col3.metric("Avg Weight (Latest Week)", weight_display)


# --- WEEKLY CALORIES vs WEIGHT TREND ---
st.subheader("📈 Weekly Calories vs Weight Trend")

fig, ax1 = plt.subplots(figsize=(8, 4))
fig.suptitle("Weekly Calories and Weight Trend", fontsize=14)

cal_color = "tab:blue"
wt_color  = "tab:orange"

# ---- Calories line + left axis ----
ax1.plot(
    avg_week_df["week"],
    avg_week_df["calories"],
    marker="o",
    label="Calories (kcal)",
    color=cal_color,
)
ax1.set_xlabel("Week")
ax1.set_ylabel("Calories (kcal)", color=cal_color)
ax1.tick_params(axis="y", labelcolor=cal_color)
ax1.grid(True)

# ---- Weight line + right axis ----
ax2 = ax1.twinx()
ax2.plot(
    wt_avg["week"],
    wt_avg["weight_kg"],
    marker="o",
    linestyle="--",
    label="Weight (kg)",
    color=wt_color,
)
ax2.set_ylabel("Weight (kg)", color=wt_color)
ax2.tick_params(axis="y", labelcolor=wt_color)

fig.tight_layout()
st.pyplot(fig)


# --- BODY COMPOSITION ---
st.subheader("🧍 Body Composition Trends by Week")

fig2, ax3 = plt.subplots(figsize=(8, 4))
fig2.suptitle("Body Composition Trend", fontsize=14)

ax3.plot(wt_avg["week"], wt_avg["skeletal_muscle_kg"], marker="o", label="Skeletal Muscle")
ax3.plot(wt_avg["week"], wt_avg["fat_mass_kg"], marker="o", label="Fat Mass")
ax3.plot(wt_avg["week"], wt_avg["body_water_kg"], marker="o", label="Body Water")

ax3.set_xlabel("Week")
ax3.set_ylabel("Mass (kg)")
ax3.legend()
ax3.grid(True)
fig2.tight_layout()
st.pyplot(fig2)

# --- MACROS (REVISED TO USE MATPLOTLIB) ---
st.subheader("🍱 Average Macronutrient Intake by Week")

# 1. Create the Matplotlib figure and axes
fig3, ax4 = plt.subplots(figsize=(8, 4))
fig3.suptitle("Average Macronutrient Intake by Week", fontsize=14)

# 2. Plot the data
ax4.plot(avg_week_df["week"], avg_week_df["protein"], marker="o", label="Protein")
ax4.plot(avg_week_df["week"], avg_week_df["carbs"], marker="o", label="Carbs")
ax4.plot(avg_week_df["week"], avg_week_df["fat"], marker="o", label="Fat")

# 3. Set labels and styling
ax4.set_xlabel("Week")
ax4.set_ylabel("Grams")
ax4.legend()
ax4.grid(True) # Adds the grid lines for the Matplotlib look

# 4. Render the figure in Streamlit
fig3.tight_layout()
st.pyplot(fig3)


# --- DAY OF WEEK ---
st.subheader("📅 Average Calorie Intake by Day of Week")

fig4, ax5 = plt.subplots(figsize=(8, 4))
fig4.suptitle("Average Calorie Intake by Day", fontsize=14)
ax5.plot(day_name_avg["day_name"], day_name_avg["calories"], marker="o")
ax5.set_xlabel("Day")
ax5.set_ylabel("Calories (kcal)")
ax5.grid(True)
fig4.tight_layout()
st.pyplot(fig4)


# --- WEEKLY SUMMARY TABLE ---
st.subheader("📋 Weekly Summary")

st.dataframe(summary_df)

# --- DOWNLOAD BUTTON LOGIC ---
def df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    """Converts a DataFrame to an Excel file in memory (BytesIO)."""
    output = BytesIO()
    # create an Excel writer that writes into the BytesIO buffer
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary")
    # go back to the start of the buffer
    output.seek(0)
    return output

excel_bytes = df_to_excel_bytes(summary_df)

st.download_button(
    label="Download Weekly Summary (Excel)",
    data=excel_bytes,
    file_name="weekly_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)