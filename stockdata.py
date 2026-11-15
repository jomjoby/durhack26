import pandas as pd
import yfinance as yf
import requests
from io import StringIO

def getStockData(ticker):
    data = yf.download(
        ticker,
        period="1y",
        interval="1d",
        auto_adjust=True
    )

    return data



def moving_average_strategy(data):
    # Get the closing prices
    close = data["Close"]

    # Handle yfinance returning multiple columns
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()

    # Calculate moving averages
    short_average = close.rolling(window=20).mean()
    long_average = close.rolling(window=50).mean()

    # BUY when the 20-day average is above the 50-day average
    signals = (short_average > long_average).astype(int)

    # Use yesterday's signal to avoid using today's closing price
    position = signals.shift(1).fillna(0)

    # Calculate daily stock returns
    daily_returns = close.pct_change().fillna(0)

    # Calculate returns from our strategy
    strategy_returns = position * daily_returns

    # Start with £100 (or 100 units) of simulated money
    portfolio = (1 + strategy_returns).cumprod() * 100

    return portfolio



def get_sp500_strategy():
    # Get the current S&P 500 company list
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    # companies = pd.read_html(url, attrs={"id": "constituents"})[0]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    companies = pd.read_html(
        StringIO(response.text),
        attrs={"id": "constituents"}
    )[0]

    tickers = companies["Symbol"].str.replace(".", "-", regex=False).tolist()

    print(f"Downloading data for {len(tickers)} S&P 500 companies...")

    # Download all stock prices together
    prices = yf.download(
        tickers,
        period="1y",
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        threads=True,
        progress=False
    )

    strategy_returns = []
    normal_returns = []

    for ticker in tickers:
        try:
            # Find this company's closing prices
            if ticker in prices.columns.get_level_values(0):
                close = prices[ticker]["Close"]
            elif ticker in prices.columns.get_level_values(1):
                close = prices.xs(ticker, axis=1, level=1)["Close"]
            else:
                continue

            close = close.dropna()

            if len(close) < 50:
                continue

            # Moving averages
            short_average = close.rolling(20).mean()
            long_average = close.rolling(50).mean()

            # Strategy: buy when short average is above long average
            signal = (short_average > long_average).astype(int)

            # Use yesterday's signal
            position = signal.shift(1).fillna(0)

            # Daily returns
            daily_returns = close.pct_change()

            # Strategy returns and buy-and-hold returns
            strategy_returns.append(position * daily_returns)
            normal_returns.append(daily_returns)

        except (KeyError, TypeError):
            continue

    if not strategy_returns:
        raise ValueError("No S&P 500 stock data was successfully downloaded.")

    # Combine the returns into equally weighted portfolios
    strategy_daily = pd.concat(strategy_returns, axis=1).mean(axis=1)
    normal_daily = pd.concat(normal_returns, axis=1).mean(axis=1)

    # Start both portfolios at £100
    model_portfolio = (1 + strategy_daily.fillna(0)).cumprod() * 100
    buy_and_hold = (1 + normal_daily.fillna(0)).cumprod() * 100

    print(f"Successfully processed {len(strategy_returns)} stocks.")

    return model_portfolio, buy_and_hold
