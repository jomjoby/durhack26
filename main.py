
from dash import Dash, html, dcc, Input, Output
from weatherdata import getPastYear
from stockdata import getStockData
import pandas as pd
import plotly.express as px
import random
from stockdata import getStockData, moving_average_strategy, get_sp500_strategy

app = Dash(__name__)


# -----------------------------
# DOWNLOAD DATA
# -----------------------------

london_data = getPastYear("London")
tokyo_data = getPastYear("Tokyo")
sydney_data = getPastYear("Sydney")
newyork_data = getPastYear("New York")
shanghai_data = getPastYear("Shanghai")

apple_data = getStockData("AAPL")
tesla_data = getStockData("TSLA")
microsoft_data = getStockData("MSFT")

apple_model = moving_average_strategy(apple_data)
sp500_model, sp500_buy_hold = get_sp500_strategy()


# -----------------------------
# STOCK DATA HELPERS
# -----------------------------

def get_close(data):
    close = data["Close"]

    # Handle yfinance MultiIndex columns
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    return close


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

    # Normalise individual stock prices to start at 100
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

    # Add S&P 500 model performance
    fig.add_scatter(
        x=sp500_model.index,
        y=sp500_model.values,
        mode="lines",
        name="S&P 500 Model",
        line=dict(color="#E09F3E", width=3)
    )

    # Add S&P 500 buy and hold performance
    fig.add_scatter(
        x=sp500_buy_hold.index,
        y=sp500_buy_hold.values,
        mode="lines",
        name="S&P 500 Buy & Hold",
        line=dict(color="#493D50", width=3, dash="dash")
    )

    # Graph styling
    fig.update_layout(
        plot_bgcolor="#F8F3FA",
        paper_bgcolor="#E0D4E7",
        yaxis_title="Performance (starting at 100)",
        xaxis_title="Date",
        hovermode="x unified",
        legend_title="Stocks and Strategies"
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
