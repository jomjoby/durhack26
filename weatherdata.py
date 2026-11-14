import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import matplotlib as mpl

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

locations = {
    "uk": [54.00, 2.00],
    "Tokyo": [35.69, 139.69],
    "Ny" : [40.71, -74.01],
    "Shang" : [31.22, 121.46],
    "Australia" : [-25, 135]
}

latitudes = [loc[0] for loc in locations.values()]
longitudes = [loc[1] for loc in locations.values()]

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": latitudes,
    "longitude": longitudes,

    "start_date": "2026-11-01",
    "end_date": pd.Timestamp.today().strftime('%Y-%m-%d'),
    "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
    "hourly": ["temperature_2m", "relative_humidity_2m"],
}

responses = openmeteo.weather_api(url, params = params)

for i, response in enumerate(responses):
    location_name = list(locations.keys())[i]

    current = response.Current()
    current_time = pd.to_datetime(current.Time(), unit="s", utc=True)

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
           start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
           end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
           freq = pd.Timedelta(seconds = hourly.Interval()),
           inclusive = "left"
        ),
        "temperature_2m": hourly_temperature_2m,
        "relative_humidity_2m": hourly_relative_humidity_2m
    }

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    hourly_dataframe.to_csv(f"weather_data_{location_name}.csv", index=False)
