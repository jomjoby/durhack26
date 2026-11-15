import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Same thresholds as main.py
RAIN_MM = 1
SUNNY_CLOUD = 30
SCORE_CUTOFF = 0.5


def prepare_weather(weather_dict):
    """weather_dict = {"London": london_data, ...} (hourly dataframes).
    Returns one row per day with temperature, humidity, rain and cloud per city."""
    frames = []

    for city, data in weather_dict.items():
        data = data.copy()
        data["date"] = pd.to_datetime(data["date"]).dt.date

        daily = data.groupby("date").agg(
            **{
                f"{city}_temperature": ("temperature_2m", "mean"),
                f"{city}_humidity": ("relative_humidity_2m", "mean"),
                f"{city}_rain": ("precipitation", "sum"),
                f"{city}_cloud": ("cloud_cover", "mean"),
            }
        )
        frames.append(daily)

    return pd.concat(frames, axis=1)


def _build_frame(close, weather, cities):
    """Joins prices and weather, and adds the weather score, rule signal
    and next-day return (same logic as main.py)."""
    close = close.dropna().copy()
    close.index = pd.to_datetime(close.index).date
    close.index.name = "date"

    df = pd.DataFrame({"Close": close}).join(weather, how="inner").sort_index()
    df["previous_return"] = df["Close"].pct_change()

    scores = pd.DataFrame(index=df.index)
    for city in cities:
        temp = df[f"{city}_temperature"]
        vs_normal = temp - temp.rolling(30, min_periods=10).mean()

        scores[city] = (
            np.sign(vs_normal)
            + np.where(df[f"{city}_rain"] > RAIN_MM, -1, 0)
            + np.where(df[f"{city}_cloud"] < SUNNY_CLOUD, 1, 0)
        )

    df["weather_score"] = scores.mean(axis=1)
    df["rule_signal"] = np.select(
        [df["weather_score"] > SCORE_CUTOFF, df["weather_score"] < -SCORE_CUTOFF],
        [1, -1],
        default=0,
    )

    df["future_return"] = df["Close"].shift(-1) / df["Close"] - 1
    df["signal"] = np.select(
        [df["future_return"] > 0.002, df["future_return"] < -0.002],
        [1, -1],
        default=0,
    )
    return df


def weather_rule_curve(close, weather, cities):
    """Performance of the weather rule (invested on BUY days, cash otherwise),
    starting at 100. No training involved, so the whole year is a fair test."""
    df = _build_frame(close, weather, cities)

    returns = (df["rule_signal"].clip(lower=0) * df["future_return"]).fillna(0)
    curve = (1 + returns).cumprod() * 100
    curve.index = pd.to_datetime(curve.index)
    return curve


def random_forest_curve(close, weather, cities):
    """Performance of the random forest on its unseen test period only
    (trained on the first 80% of days), starting at 100 on the first test day."""
    df = _build_frame(close, weather, cities)

    features = [
        c for c in df.columns
        if c.endswith(("_temperature", "_humidity", "_rain", "_cloud"))
    ] + ["previous_return", "weather_score"]

    data = df.dropna(subset=features + ["future_return"])
    split = int(len(data) * 0.8)

    if split < 20 or len(data) - split < 5:
        return pd.Series(dtype=float)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(data[features].iloc[:split], data["signal"].iloc[:split])

    test = data.iloc[split:]
    predictions = pd.Series(model.predict(test[features]), index=test.index)

    returns = predictions.clip(lower=0) * test["future_return"]
    curve = (1 + returns).cumprod() * 100
    curve.index = pd.to_datetime(curve.index)
    return curve