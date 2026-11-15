
import pandas as pd

from database.connection import get_connection
from stockdata import getStockData
from psycopg2.extras import execute_values
from weatherdata import getAllPastYear


# -----------------------------
# CONFIGURATION
# -----------------------------

WEATHER_LOCATIONS = {
    "London": "United Kingdom",
    "Tokyo": "Japan",
    "New York": "United States",
    "Shanghai": "China",
    "Sydney": "Australia"
}

STOCK_SYMBOLS = ["AAPL", "TSLA", "MSFT"]


# -----------------------------
# DATABASE SETUP
# -----------------------------

def setup_database():

    with get_connection() as conn:
        with conn.cursor() as cur:

            with open("database/schema.sql", "r") as file:
                schema = file.read()

            cur.execute(schema)

            print("Successfully connected to TigerData!")
            print("Database schema created successfully!")

            cur.execute("""
                SELECT hypertable_name
                FROM timescaledb_information.hypertables;
            """)

            for row in cur.fetchall():
                print("Hypertable:", row[0])


# -----------------------------
# WEATHER DATA INGESTION
# -----------------------------
def insert_weather_data():

    print("\nStarting weather ingestion...")

    all_data = getAllPastYear()

    total_records = 0

    with get_connection() as conn:
        with conn.cursor() as cur:

            for city, country in WEATHER_LOCATIONS.items():

                df = all_data[city]

                records = []

                for row in df.itertuples(index=False):

                    records.append((
                        pd.to_datetime(row.date, utc=True).to_pydatetime(),
                        city,
                        country,
                        None if pd.isna(row.temperature_2m)
                        else float(row.temperature_2m),
                        None if pd.isna(row.relative_humidity_2m)
                        else float(row.relative_humidity_2m)
                    ))

                execute_values(
                    cur,
                    """
                    INSERT INTO weather_observations
                    (time, city, country, temperature, humidity)
                    VALUES %s
                    ON CONFLICT (time, city) DO NOTHING;
                    """,
                    records,
                    page_size=1000
                )

                conn.commit()

                total_records += len(records)

                print(f"{city}: {len(records)} records processed")

    print(f"Weather ingestion complete: {total_records}")


# -----------------------------
# STOCK DATA HELPERS
# -----------------------------

def get_stock_column(data, field):

    if isinstance(data.columns, pd.MultiIndex):

        if field in data.columns.get_level_values(0):
            values = data[field]

        else:
            values = data.xs(
                field,
                axis=1,
                level=1
            )

    else:
        values = data[field]

    if isinstance(values, pd.DataFrame):
        values = values.iloc[:, 0]

    return values


# -----------------------------
# STOCK DATA INGESTION
# -----------------------------

def insert_stock_data():

    print("\nStarting stock ingestion...")

    total_records = 0

    with get_connection() as conn:
        with conn.cursor() as cur:

            for symbol in STOCK_SYMBOLS:

                print(f"Fetching {symbol}...")

                df = getStockData(symbol)

                if df.empty:
                    print(f"No data for {symbol}")
                    continue

                records = []

                columns = {
                    name: get_stock_column(df, name)
                    for name in [
                        "Open", "High", "Low",
                        "Close", "Volume"
                    ]
                }

                for i, timestamp in enumerate(df.index):

                    def clean(value):
                        return None if pd.isna(value) else float(value)

                    volume = columns["Volume"].iloc[i]

                    records.append((
                        pd.to_datetime(timestamp, utc=True).to_pydatetime(),
                        symbol,
                        clean(columns["Open"].iloc[i]),
                        clean(columns["High"].iloc[i]),
                        clean(columns["Low"].iloc[i]),
                        clean(columns["Close"].iloc[i]),
                        None if pd.isna(volume) else int(volume)
                    ))

                execute_values(
                    cur,
                    """
                    INSERT INTO stock_prices
                    (time, symbol, open, high, low, close, volume)
                    VALUES %s
                    ON CONFLICT (time, symbol) DO NOTHING;
                    """,
                    records,
                    page_size=1000
                )

                conn.commit()

                total_records += len(records)

                print(f"{symbol}: {len(records)} records processed")

    print(f"Stock ingestion complete: {total_records}")


# -----------------------------
# VERIFY DATABASE
# -----------------------------

def verify_database():

    with get_connection() as conn:
        with conn.cursor() as cur:

            for table in [
                "weather_observations",
                "stock_prices"
            ]:

                cur.execute(
                    f"SELECT COUNT(*) FROM {table}"
                )

                count = cur.fetchone()[0]

                print(f"{table}: {count} records")


# -----------------------------
# MAIN
# -----------------------------

def main():

    try:

        setup_database()

        insert_weather_data()

        insert_stock_data()

        print("\n---------- DATABASE SUMMARY ----------")

        verify_database()

        print("\nAll operations completed successfully!")

    except Exception as error:

        print("\nDatabase operation failed:")
        print(error)


if __name__ == "__main__":
    main()