# --- main.py ---
import os
import pandas as pd
import numpy as np
import math
import re
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

from live_data import get_live_weather_df

#Constants
plant_area_m2 = 32500.0
price_per_kwh = 7
solar_panel_path = os.path.join(os.path.dirname(__file__), "Solar_panel_Dataset.csv")
panel_df = pd.read_csv(solar_panel_path)

# Load Saved Model 
def load_model_if_exists():
    if os.path.exists("trained_model.pkl") and os.path.exists("scaler.pkl"):
        model = joblib.load("trained_model.pkl")
        scaler = joblib.load("scaler.pkl")
        print("Loaded trained model and scaler.")
        return model, scaler
    else:
        print("Model files not found.")
        return None, None

global_model, global_scaler = load_model_if_exists()

#Get Performance Factor
def get_perf_factor(manufacturer, material):
    if manufacturer:
        filtered = panel_df[
            (panel_df["Manufacturer"].str.lower() == manufacturer.lower()) &
            (panel_df["Material/Technology"].str.lower() == material.lower())
        ]
    else:
        filtered = panel_df[
            (panel_df["Material/Technology"].str.lower() == material.lower())
        ]

    if not filtered.empty:
        return filtered["Performance Factor"].values[0]
    else:
        raise ValueError(" Material not found (check manufacturer or technology).")

#Train Model on One Dataset
def train_model(power_path, weather_path):
    power_df = pd.read_csv(power_path)
    weather_df = pd.read_csv(weather_path)

    # Parse datetime correctly
    weather_df.rename(columns={"YEAR": "year", "MO": "month", "DY": "day", "HR": "hour"}, inplace=True)
    weather_df["datetime"] = pd.to_datetime(weather_df[["year", "month", "day", "hour"]])

    power_df["datetime"] = pd.to_datetime(power_df["LocalTime"])
    merged = pd.merge(power_df, weather_df, on="datetime")

    is_upv = "UPV" in os.path.basename(power_path).upper()
    perf_factor = panel_df[panel_df["Material/Technology"].str.contains("Mono" if is_upv else "Poly", case=False)]["Performance Factor"].mean()

    merged["adjusted_GHI"] = merged["GHI_W/m2"] * perf_factor
    merged["hour"] = merged["datetime"].dt.hour
    merged["dayofyear"] = merged["datetime"].dt.dayofyear
    merged["power_kW_per_m2"] = (merged["Power(MW)"] * 1000) / plant_area_m2

    X = merged[["adjusted_GHI", "Temp_C", "WindSpeed_m/s", "hour", "dayofyear"]]
    y = merged["power_kW_per_m2"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)

    return model, scaler, merged

# Load and Combine All Datasets
def load_and_combine_all_datasets():
    print("Loading and matching datasets from 'Datasets/'...")
    combined_df = pd.DataFrame()

    power_files = [f for f in os.listdir("Datasets") if f.lower().endswith(".csv") and "_weather" not in f.lower()]
    weather_files = [f for f in os.listdir("Datasets") if "weather" in f.lower() and f.endswith(".csv")]

    for power_file in power_files:
        match = re.search(r"([-+]?\d+\.\d+)_([-+]?\d+\.\d+)", power_file)
        if not match:
            print(f"Skipping {power_file} — no lat/lon pattern found.")
            continue

        lat, lon = match.groups()
        weather_match = next((wf for wf in weather_files if lat in wf and lon in wf), None)
        if not weather_match:
            print(f" No weather file matching {lat}, {lon} for {power_file}")
            continue

        power_path = os.path.join("Datasets", power_file)
        weather_path = os.path.join("Datasets", weather_match)

        try:
            _, _, merged = train_model(power_path, weather_path)
            combined_df = pd.concat([combined_df, merged], ignore_index=True)

        except Exception as e:
            print(f" Failed to process {power_file}: {e}")

    print(f" Total rows combined: {len(combined_df)}")
    return combined_df

#Train Global Model 
if __name__ == "__main__":
    combined_df = load_and_combine_all_datasets()

    X = combined_df[["adjusted_GHI", "Temp_C", "WindSpeed_m/s", "hour", "dayofyear"]]
    y = combined_df["power_kW_per_m2"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)

    joblib.dump(model, "trained_model.pkl")
    joblib.dump(scaler, "scaler.pkl")
    print(" Model trained on all datasets and saved.")

# Predict using Live Data 
def run_model_with_inputs(pincode, material, manufacturer, area, tilt):
    try:
        weather_df = get_live_weather_df(pincode)
    except Exception as e:
        raise ValueError(f"Weather fetch failed: {e}")

    perf_factor = get_perf_factor(manufacturer, material)
    cosine_factor = max(0.5, math.cos(math.radians(tilt)))

    weather_df.dropna(subset=["GHI_W/m2"], inplace=True)
    weather_df["adjusted_GHI"] = weather_df["GHI_W/m2"] * perf_factor * cosine_factor
    weather_df["hour"] = weather_df["datetime"].dt.hour
    weather_df["dayofyear"] = weather_df["datetime"].dt.dayofyear

    X = weather_df[["adjusted_GHI", "Temp_C", "WindSpeed_m/s", "hour", "dayofyear"]]
    X_scaled = global_scaler.transform(X)

    predicted_kW_per_m2 = global_model.predict(X_scaled)
    predicted_kW = predicted_kW_per_m2 * area

    weather_df["predicted_kWh"] = predicted_kW
    weather_df["date"] = weather_df["datetime"].dt.date

    daily_energy = weather_df.groupby("date")["predicted_kWh"].sum().mean()
    monthly_energy = daily_energy * 30
    yearly_energy = daily_energy * 365
    money_saved = yearly_energy * price_per_kwh

    daily_totals = weather_df.groupby("date")["predicted_kWh"].sum()
    last_month_kwh = daily_totals.tail(30).tolist()
    forecast_10_days_kwh = daily_totals.head(10).tolist()

    return {
        "current_power": round(predicted_kW[-1], 2),
        "daily_avg": round(daily_energy, 2),
        "monthly_avg": round(monthly_energy, 2),
        "yearly_avg": round(yearly_energy, 2),
        "money_saved": round(money_saved, 2),
        "last_month_kwh": [round(val, 2) for val in last_month_kwh],
        "forecast_10_days_kwh": [round(val, 2) for val in forecast_10_days_kwh]
    }
