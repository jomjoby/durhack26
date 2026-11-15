import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from weatherdata import getPastYear
from stockdata import getStockData, moving_average_strategy, get_sp500_strategy

# --------------------------------
# 1. DOWNLOAD WEATHER DATA
# --------------------------------

weather_locations = {
    "London": getPastYear("London"),
    "Tokyo": getPastYear("Tokyo"),
    "Sydney": getPastYear("Sydney"),
    "New York": getPastYear("New York"),
    "Shanghai": getPastYear("Shanghai")
}


# --------------------------------
# 2. PREPARE WEATHER FEATURES
# --------------------------------

weather_features = []

for city, data in weather_locations.items():

    data = data.copy()

    data["date"] = pd.to_datetime(data["date"]).dt.date

    daily_weather = data.groupby("date").agg(
        temperature=("temperature_2m", "mean"),
        humidity=("relative_humidity_2m", "mean"),
        rain=("precipitation", "sum"),        # total mm per day
        cloud=("cloud_cover", "mean")         # average % per day
    )

    daily_weather = daily_weather.rename(
        columns={
            "temperature": f"{city}_temperature",
            "humidity": f"{city}_humidity",
            "rain": f"{city}_rain",
            "cloud": f"{city}_cloud"
        }
    )

    weather_features.append(daily_weather)


weather_data = pd.concat(weather_features, axis=1)


# --------------------------------
# 3. DOWNLOAD STOCK DATA
# --------------------------------

stock_data = getStockData("AAPL")


def get_close(data):

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    return close


stock_prices = get_close(stock_data).dropna()

stock_prices.index = pd.to_datetime(
    stock_prices.index
).date

stock_prices.index.name = "date"


# --------------------------------
# 4. COMBINE WEATHER AND STOCK DATA
# --------------------------------

combined_data = pd.DataFrame({
    "Close": stock_prices
})

combined_data = combined_data.join(
    weather_data,
    how="inner"
)

combined_data = combined_data.sort_index()


# Add previous day's stock movement
combined_data["previous_return"] = (
    combined_data["Close"].pct_change()
)


# --------------------------------
# 4b. WEATHER RULES
#     sunny / warm  -> buy
#     rainy / cold  -> sell
# --------------------------------

# Thresholds you can tweak
RAIN_MM = 1       # more than this many mm in a day counts as "rainy"
SUNNY_CLOUD = 30  # less than this % cloud cover counts as "sunny"
SCORE_CUTOFF = 0.5

weather_scores = pd.DataFrame(index=combined_data.index)

for city in weather_locations:

    temp = combined_data[f"{city}_temperature"]

    # "Warm" or "cold" compared with the recent past (30 trading days),
    # not an absolute number, so seasons don't dominate
    temp_vs_normal = temp - temp.rolling(30, min_periods=10).mean()

    weather_scores[city] = (
        np.sign(temp_vs_normal)                                      # warm +1, cold -1
        + np.where(combined_data[f"{city}_rain"] > RAIN_MM, -1, 0)   # rainy -1
        + np.where(combined_data[f"{city}_cloud"] < SUNNY_CLOUD, 1, 0)  # sunny +1
    )

# Average across all cities
# (to use only New York, replace this with weather_scores["New York"])
combined_data["weather_score"] = weather_scores.mean(axis=1)

combined_data["rule_signal"] = np.select(
    [
        combined_data["weather_score"] > SCORE_CUTOFF,
        combined_data["weather_score"] < -SCORE_CUTOFF
    ],
    [
        1,   # BUY
        -1   # SELL
    ],
    default=0  # HOLD
)


# --------------------------------
# 5. CREATE THE TARGET
# --------------------------------

# Calculate the next trading day's percentage change

combined_data["future_return"] = (
    combined_data["Close"].shift(-1)
    / combined_data["Close"] - 1
)


# Decide what the model should learn

combined_data["signal"] = np.select(
    [
        combined_data["future_return"] > 0.002,
        combined_data["future_return"] < -0.002
    ],
    [
        1,   # BUY
        -1   # SELL
    ],
    default=0  # HOLD
)


# Return from following the weather rule:
# BUY = invested for the next day, SELL/HOLD = in cash
combined_data["rule_return"] = (
    combined_data["rule_signal"].clip(lower=0)
    * combined_data["future_return"]
)


# --------------------------------
# 6. SELECT MODEL INPUTS
# --------------------------------

features = [
    column for column in combined_data.columns
    if column.endswith("_temperature")
    or column.endswith("_humidity")
    or column.endswith("_rain")
    or column.endswith("_cloud")
]

features.append("previous_return")
features.append("weather_score")


# Remove rows with missing information
training_data = combined_data.dropna(
    subset=features + ["future_return"]
).copy()

X = training_data[features]
y = training_data["signal"]


# --------------------------------
# 7. SPLIT THE DATA CHRONOLOGICALLY
# --------------------------------

split = int(len(training_data) * 0.8)

if split < 20 or len(training_data) - split < 5:
    raise ValueError(
        "Not enough overlapping weather and stock data "
        "to train and test the model."
    )

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]


# --------------------------------
# 8. TRAIN THE MODEL
# --------------------------------

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=5,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)


# --------------------------------
# 9. TEST THE MODEL
# --------------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nMODEL RESULTS")
print("-----------------------")

print("Accuracy:", round(accuracy * 100, 2), "%")

print(
    classification_report(
        y_test,
        predictions,
        labels=[-1, 0, 1],
        target_names=["SELL", "HOLD", "BUY"],
        zero_division=0
    )
)


# Which inputs did the model actually use?
importances = pd.Series(
    model.feature_importances_,
    index=features
).sort_values(ascending=False)

print("\nTOP 10 FEATURES")
print("-----------------------")
print(importances.head(10).round(3))


# --------------------------------
# 9b. TEST THE WEATHER RULE
#     (on the same unseen test period as the model)
# --------------------------------

test_rows = training_data.iloc[split:]

# Model-based strategy: invested when the model says BUY
model_return = (
    pd.Series(predictions, index=test_rows.index).clip(lower=0)
    * test_rows["future_return"]
)

print("\nSTRATEGY COMPARISON (test period, average daily return)")
print("-----------------------")
print("Weather rule:  ", round(test_rows["rule_return"].mean() * 100, 4), "%")
print("Random forest: ", round(model_return.mean() * 100, 4), "%")
print("Buy & hold:    ", round(test_rows["future_return"].mean() * 100, 4), "%")

print("\nWeather rule signal counts (full year):")
print(
    combined_data["rule_signal"]
    .map({1: "BUY", 0: "HOLD", -1: "SELL"})
    .value_counts()
)


# --------------------------------
# 10. TRAIN ON ALL AVAILABLE DATA
# --------------------------------

model.fit(X, y)


# --------------------------------
# 11. MAKE A NEW PREDICTION
# --------------------------------

latest_data = combined_data.dropna(
    subset=features
)

if latest_data.empty:
    raise ValueError("No data available for prediction.")

latest_row = latest_data.iloc[[-1]]

prediction = model.predict(
    latest_row[features]
)[0]

signals = {
    1: "BUY",
    0: "HOLD",
    -1: "SELL"
}

print("\nLATEST MODEL PREDICTION")
print("-----------------------")

print("Date:", latest_row.index[-1])
print("Apple closing price:", latest_row["Close"].iloc[0])
print("Weather score:", round(latest_row["weather_score"].iloc[0], 2))
print("Weather rule decision:", signals[latest_row["rule_signal"].iloc[0]])
print("Model decision:", signals[prediction])

probabilities = model.predict_proba(
    latest_row[features]
)[0]

print("\nPrediction probabilities:")

for signal, probability in zip(model.classes_, probabilities):
    print(
        signals[signal],
        ":",
        round(probability * 100, 2),
        "%"
    )