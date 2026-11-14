import os
import time
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


trading_client = TradingClient(
    api_key="PKOO5JTCRLE656RZTR63JBVMPU",
    secret_key="4aASv9Fe24ZTTGXcyXAYw2Dt9PBaMHenGhEW438tWUgb",
    paper=True
)


NYdf = pd.read_csv("weather_data_Ny.csv")
AUdf = pd.read_csv("weather_data_Australia.csv")
SHdf = pd.read_csv("weather_data_Shang.csv")
UKdf = pd.read_csv("weather_data_uk.csv")
TOdf = pd.read_csv("weather_data_Tokyo.csv")

date_col = "date" if "date" in NYdf.columns else NYdf.columns[0]

all_temps = pd.DataFrame({
    "date": pd.to_datetime(NYdf[date_col]),
    "NY": NYdf["temperature_2m"],
    "AU": AUdf["temperature_2m"],
    "SH": SHdf["temperature_2m"],
    "UK": UKdf["temperature_2m"],
    "TO": TOdf["temperature_2m"]
})


all_temps = all_temps.sort_values(by="date").reset_index(drop=True)

all_temps["avg_temp"] = all_temps[["NY", "AU", "SH", "UK", "TO"]].mean(axis=1)



def place_buy_order(symbol, qty):
    try:
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(order_data=market_order_data)
        print(f"  -> Paper BUY placed: {qty} {symbol} | Order ID: {order.id}")
    except Exception as e:
        print(f"  -> Order failed for {symbol}: {e}")



def High_risk():
    print("  Strategy: HIGH RISK (Stocks)")
    place_buy_order("QQQ", 1)
    place_buy_order("NVDA", 1)


def Low_risk():
    print("  Strategy: LOW RISK (Gold & Bonds)")
    place_buy_order("GLD", 1)
    place_buy_order("IEF", 1)



START_DATE = "2026-01-01"
TEMP_THRESHOLD = 20.0


filtered_df = all_temps[all_temps["date"] >= START_DATE]

print(f"Starting execution from {START_DATE} ({len(filtered_df)} records found)...\n")

for index, row in filtered_df.iterrows():
    current_date = row["date"]
    avg_temp = row["avg_temp"]

    print(f"[{current_date}] 5-City Avg Temp: {avg_temp:.2f}°")

    if avg_temp >= TEMP_THRESHOLD:
        High_risk()
    else:
        Low_risk()


    time.sleep(0.5)