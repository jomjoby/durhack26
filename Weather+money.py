import os
import sys
import numpy as np
import pandas as pd
import requests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

START, END = "2025-11-13", "2026-11-14"
DATA = "data"
LOOKBACK_DAYS = 30
THRESHOLD_C = 0.0
COST_BPS = 5
SAFE = "IEF"
SP500_TK = "^GSPC"  #S&P 500

CITIES = {
    "London": (51.51, -0.13, "^FTSE"),
    "New York": (40.71, -74.01, "^NYA"),
    "Sydney": (-33.86, 151.21, "^AXJO"),
    "Shanghai": (31.23, 121.47, "000001.SS"),
    "Hong Kong": (22.32, 114.17, "^HSI"),
}
def price_path(tk):
    return f"{DATA}/px_{tk.replace('^', '').replace('.', '_')}.csv"

def download_prices():
    os.makedirs(DATA, exist_ok=True)
    tickers = {c[2] for c in CITIES.values()} | {SAFE, SP500_TK}
    for tk in tickers:
        if os.path.exists(price_path(tk)):
            continue
        import yfinance as yf
        df = yf.download(tk, start=START, end=END, interval="1h", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df.to_csv(price_path(tk))

def load_daily_close(path):
    with open(path) as f:
        f.readline()
        second = f.readline()
    skip = [1, 2] if second.startswith("Ticker") else None
    df = pd.read_csv(path, index_col=0, skiprows=skip)
    local_date = pd.to_datetime(df.index.astype(str).str[:10])
    s = pd.Series(df["Close"].values, index=pd.to_datetime(df.index, utc=True))
    s.index = local_date
    return s.groupby(level=0).last().dropna()

def weather_path(city):
    return f"{DATA}/wx_{city.replace(' ', '_')}.csv"

def download_weather():
    os.makedirs(DATA, exist_ok=True)
    end = min(pd.Timestamp(END), pd.Timestamp.today().normalize() - pd.Timedelta(days=6))
    start = pd.Timestamp(START) - pd.Timedelta(days=LOOKBACK_DAYS + 5)
    for city, (lat, lon, _) in CITIES.items():
        if os.path.exists(weather_path(city)):
            continue
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_mean",
            "timezone": "auto"
        }, timeout=60)
        r.raise_for_status()
        d = r.json()["daily"]
        pd.DataFrame({"date": d["time"], "temp": d["temperature_2m_mean"]}).to_csv(weather_path(city), index=False)

def load_weather(city):
    return pd.read_csv(weather_path(city), parse_dates=["date"]).set_index("date")["temp"]

def metrics(r, name):
    r = r.dropna()
    total_ret = (1 + r).prod() - 1
    return {"strategy": name, "total_return_%": round(total_ret * 100, 2)}

def main():
    download_prices()
    download_weather()
    safe_close = load_daily_close(price_path(SAFE))
    sp500_close = load_daily_close(price_path(SP500_TK))
    risky_close = {c: load_daily_close(price_path(v[2])) for c, v in CITIES.items()}
    cal = pd.bdate_range(START, END)

    def rets(close):
        return close.reindex(cal).ffill().pct_change().fillna(0)

    safe_ret = rets(safe_close)
    sp500_ret = rets(sp500_close)

    sleeves = {}
    table_rows = []

    for city, (_, _, tk) in CITIES.items():
        temp = load_weather(city)
        anomaly = temp - temp.rolling(LOOKBACK_DAYS).mean()
        hot = (anomaly > THRESHOLD_C).astype(float)
        pos = hot.reindex(cal, method="ffill").shift(1).fillna(0)

        r = pos * rets(risky_close[city]) + (1 - pos) * safe_ret
        r -= pos.diff().abs().fillna(0) * COST_BPS / 1e4
        sleeves[city] = r
        table_rows.append(metrics(r, f"Weather Strategy ({city})"))

    table_rows.append(metrics(sp500_ret, "S&P 500 (^GSPC)"))
    table_rows.append(metrics(safe_ret, f"Always safe ({SAFE})"))

    table = pd.DataFrame(table_rows).round(2)
    print(table.to_string(index=False))


    fig, ax = plt.subplots(figsize=(11, 6))
    for city, r in sleeves.items():
        ax.plot((1 + r).cumprod(), label=f"Weather ({city})", linewidth=1.5)
    ax.plot((1 + sp500_ret).cumprod(), label="S&P 500 (^GSPC)", color="black", linewidth=2.5, linestyle="--")
    ax.plot((1 + safe_ret).cumprod(), label=f"Safe ({SAFE})", color="gray", linewidth=1.5, linestyle=":")

    ax.set_title("Weather Strategy by City vs. S&P 500 (Growth of $1)")
    ax.set_ylabel("Portfolio Value")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("1city_weather_vs_sp500.png", dpi=130)
    print("\nSaved chart -> 1city_weather_vs_sp500.png")

if __name__ == "__main__":
    main()
