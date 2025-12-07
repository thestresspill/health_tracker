import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from data_processing import load_and_process, EXCEL_PATH

st.set_page_config(
    page_title="Food & Fitness Dashboard",
#    layout="wide",
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



# ---------- LOAD DATA ----------
@st.cache_data
def get_data():
    return load_and_process(EXCEL_PATH)

try:
    data = get_data()

except FileNotFoundError:
    st.error(f"Excel file `{EXCEL_PATH}` not found. Place it in the same folder as app.py.")
    st.stop()

except Exception as e:
    st.error(f"Error while loading data: {e}")
    st.stop()

# unpack data dictionaries
daily_df      = data["daily_df"]
avg_week_df   = data["avg_week_df"]
wt_avg        = data["wt_avg"]
day_name_avg  = data["day_name_avg"]
workout_agg   = data["workout_agg"]
summary_df    = data["summary_df"]


# ---------- TOP SUMMARY CARDS ----------
latest_week = int(avg_week_df["week"].max())
latest_week_cal = avg_week_df.loc[avg_week_df["week"] == latest_week, "calories"].iloc[0]
latest_weight = wt_avg.loc[wt_avg["week"] == latest_week, "weight_kg"].iloc[0]

latest_workout = workout_agg.loc[workout_agg["week"] == latest_week, :]
latest_workout_cal = (
    latest_workout["Calories Burned"].iloc[0]
    if not latest_workout.empty
    else 0
)

col1, col2, col3 = st.columns(3)

col1.metric("Latest Week", latest_week)
col2.metric("Avg Calories (Latest Week)", f"{latest_week_cal:,.0f} kcal")
col3.metric("Avg Weight (Latest Week)", f"{latest_weight:,.1f} kg")

# ---------- WEEKLY CALORIES vs WEIGHT ----------

st.subheader("📈 Weekly Calories vs Weight Trend")

fig, ax1 = plt.subplots(figsize=(8, 4))

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


# ---------- BODY COMPOSITION ----------
st.subheader("🧍 Body Composition Trends by Week")

fig2, ax3 = plt.subplots(figsize=(8, 4))
ax3.plot(wt_avg["week"], wt_avg["skeletal_muscle_kg"], marker="o", label="Skeletal Muscle")
ax3.plot(wt_avg["week"], wt_avg["fat_mass_kg"], marker="o", label="Fat Mass")
ax3.plot(wt_avg["week"], wt_avg["body_water_kg"], marker="o", label="Body Water")

ax3.set_xlabel("Week")
ax3.set_ylabel("Kg")
ax3.legend()
ax3.grid(True)
fig2.tight_layout()
st.pyplot(fig2)

# ---------- MACROS ----------
st.subheader("🍱 Average Macronutrient Intake by Week")

fig3, ax4 = plt.subplots(figsize=(8, 4))
ax4.plot(avg_week_df["week"], avg_week_df["protein"], marker="o", label="Protein")
ax4.plot(avg_week_df["week"], avg_week_df["carbs"], marker="o", label="Carbs")
ax4.plot(avg_week_df["week"], avg_week_df["fat"], marker="o", label="Fat")

ax4.set_xlabel("Week")
ax4.set_ylabel("Grams")
ax4.legend()
ax4.grid(True)
fig3.tight_layout()
st.pyplot(fig3)

# ---------- DAY OF WEEK ----------
st.subheader("📅 Average Calorie Intake by Day of Week")

fig4, ax5 = plt.subplots(figsize=(8, 4))
ax5.plot(day_name_avg["day_name"], day_name_avg["calories"], marker="o")
ax5.set_xlabel("Day")
ax5.set_ylabel("Calories (kcal)")
ax5.grid(True)
fig4.tight_layout()
st.pyplot(fig4)

# ---------- WEEKLY SUMMARY TABLE ----------
st.subheader("📋 Weekly Summary")

st.dataframe(summary_df)

from io import BytesIO

def df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
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
