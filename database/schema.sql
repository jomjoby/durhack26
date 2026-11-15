CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Weather observations
CREATE TABLE IF NOT EXISTS weather_data (
    time TIMESTAMPTZ NOT NULL,
    location TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION
);

SELECT create_hypertable(
    'weather_data',
    'time',
    if_not_exists => TRUE
);

-- Market price observations
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION
);

SELECT create_hypertable(
    'market_data',
    'time',
    if_not_exists => TRUE
);

-- Trading signals
CREATE TABLE IF NOT EXISTS trading_signals (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    signal TEXT NOT NULL,
    confidence DOUBLE PRECISION,
    explanation TEXT
);