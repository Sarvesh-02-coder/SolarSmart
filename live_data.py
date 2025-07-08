import requests 
import pandas as pd 
from datetime import datetime, timedelta, timezone
from geopy.geocoders import Nominatim
#Nominatim is a specific tool inside geopy that lets you search for places using OpenStreetMap.

def pincode_to_latlon(pincode):
    geolocator= Nominatim(user_agent="solar_ml_project") #creating a geocoder object from Nominatim. This will connect to OpenStreetMap’s servers.
    location= geolocator.geocode(f"{pincode}, India")
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError("Invalid pincode or location not found.")

def fetch_nasa_power_data(lat, lon, start_date, end_date):
    base_url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    params= {
        "parameters": "ALLSKY_SFC_SW_DWN,T2M,WS2M",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON"
    }
    
    for attempt in range(3):
        try:
            response= requests.get(base_url, params=params, headers={"User-Agent": "solar-ml-client"})
            print(f"\nAttempt {attempt + 1} URL: {response.url}")
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise

    data=response.json()
    records= data["properties"]["parameter"]
    timeseries= list(records["ALLSKY_SFC_SW_DWN"].keys()) #records is where NASA stores the actual weather numbers.
    #timeseries is a list of all the timestamps, like "2025070809" for 8 July 2025, 9 AM.

    rows=[]
    for time_str in timeseries:
        dt= datetime.strptime(time_str, "%Y%m%d%H")
        row = {
            "YEAR": dt.year,
            "MO": dt.month,
            "DY": dt.day,
            "HR": dt.hour,
            "GHI_W/m2": records["ALLSKY_SFC_SW_DWN"].get(time_str, -999),
            "Temp_C": records["T2M"].get(time_str, -999),
            "WindSpeed_m/s": records["WS2M"].get(time_str, -999)
        }
        rows.append(row)

        #If the value is missing, insert -999 as a placeholder.

#now we clean and convert the data into dataframe 
    df = pd.DataFrame(rows)
    df.replace(-999.0, 0, inplace=True)

    df[["GHI_W/m2", "Temp_C", "WindSpeed_m/s"]] = df[["GHI_W/m2", "Temp_C", "WindSpeed_m/s"]].apply(pd.to_numeric, errors="coerce")
    df["Temp_C"] = df["Temp_C"].interpolate(method="linear")
    df["WindSpeed_m/s"] = df["WindSpeed_m/s"].interpolate(method="linear")
    #Use linear interpolation to fill small gaps in Temp and Wind columns (e.g. if one value is missing, it estimates it from nearby values).

    if df.empty:
        raise ValueError("Fetched weather data is empty after cleaning. ")
    return df

def main(pincode):
    try:
        lat,lon = pincode_to_latlon(pincode)
        print(f" Coordinates for pincode {pincode}: {lat}, {lon}")

        today= datetime.now(timezone.utc).date()
        start_date= today - timedelta(days=30)
        end_date= today + timedelta(days=10)
         
        #Get the current date in UTC. and Subtract 30 days and add 10 days using timedelta.

        weather_df= fetch_nasa_power_data(lat,lon, start_date, end_date)
        print(f"\nData fetched successfully for {len(weather_df)} rows.")

        filename= f"weather_data_{pincode}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        weather_df.to_csv(filename, index=False)
        print(f"Saved as: {filename}")
    except Exception as e:
        print(f"Error: {e}")


def get_live_weather_df(pincode):
    lat, lon = pincode_to_latlon(pincode)
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=30)
    end_date = today + timedelta(days=10)

    weather_df = fetch_nasa_power_data(lat, lon, start_date, end_date)

    weather_df.rename(columns={
        "YEAR": "year",
        "MO": "month",
        "DY": "day",
        "HR": "hour"
    }, inplace=True)

    required_cols = ["year", "month", "day", "hour"]
    missing_cols = [col for col in required_cols if col not in weather_df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns from weather data: {missing_cols}")

    weather_df.dropna(subset=required_cols, inplace=True)
    weather_df["datetime"] = pd.to_datetime(weather_df[["year", "month", "day", "hour"]])

    filename = f"live_weather_{pincode}_{today.strftime('%Y%m%d')}.csv"
    weather_df.to_csv(filename, index=False)
    print(f"Live weather data saved as: {filename}")
    print(weather_df.head())
    print(f" {len(weather_df)} rows fetched.")

    return weather_df