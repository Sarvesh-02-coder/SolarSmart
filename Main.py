import pandas as pd 
import numpy as np
import os
import math
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import re


panel_csv_path= os.path.join(os.path.dirname(__file__),"Solar_panel_dataset.csv")
panel_df=pd.read_csv(panel_csv_path)

def get_perf_factor(material,manufacturer=None):
    if manufacturer():
        filtered= panel_df[
            (panel_df["Material/Technology"].str.lower()== material.lower()) & 
            (panel_df["Manufacturer"].str.lower()==manufacturer.lower())
                       ]
    else:
        filtered= panel_df[
            (panel_df["Material/Technology"].str.lower()== material.lower())]
    if not filtered.empty:
        return filtered["performance Factor"].values[0]  # get the sected material's row and there in the performance factor extract the value.
    else:
        raise ValueError("Material or manufacturer not found.")

def train_model(power_path, weather_path, perf_factor):

    power_df=pd.read_csv(power_path)
    weather_df=pd.read_csv(weather_path)

    power_df["datetime"]=pd.to_datetime(power_df["Localtime"]) #converts date and time from text to an object.
    weather_df["datetime"]=pd.to_datetime(weather_df[["YEAR","MO","DY","HR"]]) #convert the columns to datetime object.

    merged= pd.merge(power_df,weather_df, on="datetime") #joins the datas with datetime.

    merged["adjusted_GHI"] = merged["GHI_W/m2"] * perf_factor
    merged["hour"] = merged["datetime"].dt.hour
    merged["dayofyear"] = merged["datetime"].dt.dayofyear
    merged["power_kW_per_m2"] = (merged["Power(MW)"] * 1000) / 32500.0

    x=merged[["adjusted_GHI", "Temp_C", "WindSpeed_m/s", "hour", "dayofyear"]]
    y=merged['power_kW_per_m2']

    scaler=StandardScaler()
    x_scaled=scaler.fit_transform(x)

    model=RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(x_scaled, y)

    return model, scaler, merged

