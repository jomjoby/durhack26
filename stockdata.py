
import yfinance as yf

def getStockData(ticker):
    data = yf.download(
        ticker,
        period="1y",
        interval="1d",
        auto_adjust=True
    )

    return data
