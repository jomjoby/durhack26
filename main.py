
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import random
from database.connection import get_connection

app = Dash(__name__)

import warnings

warnings.filterwarnings(
    "ignore",
    message="pandas only supports SQLAlchemy connectable"
)

# -----------------------------
# LOAD DATA FROM TIGERDATA
# -----------------------------

def load_weather_data(city):

    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                time AS date,
                temperature AS temperature_2m,
                humidity AS relative_humidity_2m
            FROM weather_observations
            WHERE city = %s
            ORDER BY time
            """,
            conn,
            params=(city,)
        )

    df["date"] = pd.to_datetime(df["date"], utc=True)

    return df


def load_stock_data(symbol):

    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                time,
                open,
                high,
                low,
                close,
                volume
            FROM stock_prices
            WHERE symbol = %s
            ORDER BY time
            """,
            conn,
            params=(symbol,)
        )

    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time")

    return df


# Load weather from TigerData
london_data = load_weather_data("London")
tokyo_data = load_weather_data("Tokyo")
sydney_data = load_weather_data("Sydney")
newyork_data = load_weather_data("New York")
shanghai_data = load_weather_data("Shanghai")

# Load stocks from TigerData
apple_data = load_stock_data("AAPL")
tesla_data = load_stock_data("TSLA")
microsoft_data = load_stock_data("MSFT")

# -----------------------------
# STOCK DATA HELPERS
# -----------------------------

def get_close(data):
    return data["close"]

# -----------------------------
# AVAILABLE WEATHER DATES
# -----------------------------

available_dates = sorted(
    pd.to_datetime(london_data["date"]).dt.date.unique().tolist()
)

if not available_dates:
    raise ValueError("No historical weather dates were downloaded.")

default_date = available_dates[-1]


# -----------------------------
# PREPARE STOCK CHART DATA
# -----------------------------

stock_prices = pd.concat(
    [
        get_close(apple_data).rename("Apple"),
        get_close(tesla_data).rename("Tesla"),
        get_close(microsoft_data).rename("Microsoft")
    ],
    axis=1
).dropna()

if not stock_prices.empty:
    normalised_prices = (
        stock_prices.div(stock_prices.iloc[0]).mul(100)
    )

    fig = px.line(
        normalised_prices,
        x=normalised_prices.index,
        y=["Apple", "Tesla", "Microsoft"],
        title="Stock Performance - Last Year",
        color_discrete_map={
            "Apple": "#8B5CF6",
            "Tesla": "#F28C68",
            "Microsoft": "#269C91"
        }
    )
else:
    fig = px.line(title="No stock data available")


# -----------------------------
# STYLE THE GRAPH
# -----------------------------

fig.update_layout(
    template="plotly_white",
    paper_bgcolor="#E0D4E7",
    plot_bgcolor="#F8F3FA",
    font=dict(
        family="Arial",
        color="#493D50"
    ),
    title=dict(
        text="Stock Performance - Last Year",
        x=0.03,
        font=dict(size=22)
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    xaxis=dict(
        title="Date",
        showgrid=False,
        linecolor="#C9B8D1"
    ),
    yaxis=dict(
        title="Performance (starting at 100)",
        gridcolor="#E6DCEB",
        zeroline=False
    ),
    margin=dict(l=45, r=25, t=85, b=45),
    hovermode="x unified"
)

fig.update_traces(
    line=dict(width=3),
    hovertemplate="%{y:.2f}<extra>%{fullData.name}</extra>"
)


# -----------------------------
# CARD STYLES
# -----------------------------

card_style = {
    "padding": "5px 12px",
    # "borderRadius": "8px",
    "textAlign": "left",
    "minHeight": "35px",
    "display": "flex",
    "flexDirection": "row",
    "alignItems": "center",
    "justifyContent": "space-between",
    "gap": "8px"
}

grid_style = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "6px"
}


def make_card(title, value="", subtitle="", background="#FFF1E5"):
    return html.Div(
        [
            html.Span(
                title,
                style={
                    "fontWeight": "bold",
                    "color": "#493D50",
                    "flex": "1"
                }
            ),
            html.Span(
                value,
                style={
                    "fontWeight": "bold",
                    "color": "#493D50"
                }
            ),
            html.Span(
                subtitle,
                style={
                    "fontSize": "12px",
                    "color": "#817489",
                    "textAlign": "right"
                }
            )
        ],
        style={
            **card_style,
            "backgroundColor": background
        }
    )


# -----------------------------
# WEATHER AND STOCK CARD DATA
# -----------------------------

weather_locations = [
    ("London", london_data),
    ("Tokyo", tokyo_data),
    ("Sydney", sydney_data),
    ("New York", newyork_data),
    ("Shanghai", shanghai_data)
]

stock_locations = [
    ("Apple", apple_data),
    ("Tesla", tesla_data),
    ("Microsoft", microsoft_data)
]


def build_weather_cards(selected_date):

    selected_day = pd.to_datetime(selected_date).date()

    cards = []

    for name, data in weather_locations:

        dates = pd.to_datetime(data["date"]).dt.date
        day_data = data.loc[dates == selected_day]

        if day_data.empty:
            temperature = "No data"
        else:
            temperature = (
                f"{day_data['temperature_2m'].mean():.1f}°C"
            )

        cards.append(
            make_card(
                name,
                temperature,
                "Average temperature",
                "#FFF1E5"
            )
        )

    return cards


def build_stock_cards(selected_date):

    selected_day = pd.to_datetime(selected_date).date()

    cards = []

    for name, data in stock_locations:

        close = get_close(data).dropna()

        # Find the latest closing price on or before selected date
        dates = pd.to_datetime(close.index).date
        available_prices = close.loc[dates <= selected_day]

        if available_prices.empty:
            price = "No data"
            subtitle = "No earlier trading day"
        else:
            price = f"${available_prices.iloc[-1]:.2f}"

            price_date = available_prices.index[-1].strftime(
                "%d/%m/%Y"
            )

            subtitle = f"Closing price: {price_date}"

        cards.append(
            make_card(
                name,
                price,
                subtitle,
                "#E0F5F1"
            )
        )

    return cards


# -----------------------------
# MAIN APP LAYOUT
# -----------------------------

app.layout = html.Div(
    [
        # HEADER
        html.H1(
            "Weather you lose or win, isn't our problem",
            style={
                "textAlign": "center",
                "color": "#493D50",
                "margin": "5px 0 15px 0",
                "fontSize": "28px"
            }
        ),

        # DATE PICKER AND RANDOM BUTTON
        html.Div(
            [
                dcc.DatePickerSingle(
                    id="date-picker",
                    date=default_date.isoformat(),
                    min_date_allowed=available_dates[0].isoformat(),
                    max_date_allowed=available_dates[-1].isoformat(),
                    display_format="DD/MM/YYYY"
                ),

                html.Button(
                    "Random date",
                    id="random-date",
                    n_clicks=0,
                    style={
                        "padding": "8px 15px",
                        # "borderRadius": "8px",
                        "border": "none",
                        "backgroundColor": "#A9E4DE",
                        "cursor": "pointer",
                        "color": "#493D50"
                    }
                )
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "justifyContent": "center",
                "marginBottom": "10px"
            }
        ),

        # MAIN CONTENT
        html.Div(
            [
                # LEFT: STOCK GRAPH
                html.Div(
                    [
                        dcc.Graph(
                            figure=fig,
                            style={"height": "100%"},
                            config={"responsive": True}
                        )
                    ],
                    style={
                        "backgroundColor": "#E0D4E7",
                        "padding": "12px",
                        "margin": "5px",
                        "flex": "1.6",
                        "minWidth": "0",
                        "minHeight": "0"
                    }
                ),

                # RIGHT SIDE
                html.Div(
                    [
                        # TOP RIGHT: WEATHER
                        html.Div(
                            [
                                html.H3(
                                    "Historical Weather",
                                    style={"color": "#493D50"}
                                ),

                                html.Div(
                                    build_weather_cards(default_date),
                                    id="weather-cards",
                                    style=grid_style
                                )
                            ],
                            style={
                                "backgroundColor": "#FEC89A",
                                "padding": "12px",
                                "margin": "5px",
                                "flex": "1",
                                "overflowY": "auto"
                            }
                        ),

                        # BOTTOM RIGHT: STOCKS
                        html.Div(
                            [
                                html.H3(
                                    "Stock Prices",
                                    style={"color": "#493D50"}
                                ),

                                html.Div(
                                    build_stock_cards(default_date),
                                    id="stock-cards",
                                    style=grid_style
                                )
                            ],
                            style={
                                "backgroundColor": "#A9E4DE",
                                "padding": "12px",
                                "margin": "5px",
                                "flex": "1",
                                "overflowY": "auto"
                            }
                        )
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "flex": "1",
                        "minWidth": "0",
                        "minHeight": "0"
                    }
                )
            ],
            style={
                "display": "flex",
                "flexDirection": "row",
                "flex": "1",
                "minHeight": "0"
            }
        )
    ],
    style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "padding": "8px",
        "boxSizing": "border-box"
    }
)


# -----------------------------
# RANDOM DATE CALLBACK
# -----------------------------

@app.callback(
    Output("date-picker", "date"),
    Input("random-date", "n_clicks"),
    prevent_initial_call=True
)
def choose_random_date(n_clicks):
    return random.choice(available_dates).isoformat()


# -----------------------------
# UPDATE CARDS WHEN DATE CHANGES
# -----------------------------

@app.callback(
    Output("weather-cards", "children"),
    Output("stock-cards", "children"),
    Input("date-picker", "date")
)
def update_cards(selected_date):

    if not selected_date:
        return [], []

    weather_cards = build_weather_cards(selected_date)
    stock_cards = build_stock_cards(selected_date)

    return weather_cards, stock_cards


# -----------------------------
# RUN APP
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
