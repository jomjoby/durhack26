from dash import Dash, html, dcc
from weatherdata import getTemp

app = Dash(__name__)

lnd_temp = getTemp("london")
tky_temp = getTemp("tokyo")
syd_temp = getTemp("sydney")
ny_temp = getTemp("new york")
sh_temp = getTemp("shanghai")


app.layout = html.Div(
    [
        html.H1("Weather you lose or win, isn't our problem"),

        # Main content row
        html.Div(
            [
                # LEFT SIDE
                html.Div(
                    "Testing Div 1",
                    style={
                        "backgroundColor": "#E0D4E7",
                        "padding": "8px",
                        "margin": "4px",
                        "flex": "1",
                    }
                ),

                # RIGHT SIDE
                html.Div(
                    [
                        # Testing Div 2
                        html.Div(
                            [
                                html.Div("Testing Div 2"),
                                html.Div(
                                    f"London: {lnd_temp:.1f} °C",
                                    style={
                                        "backgroundColor": "#FFDAB9",
                                        "padding": "8px",
                                        "margin": "4px",
                                    }
                                ),
                                html.Div(
                                    f"Tokyo: {tky_temp:.1f} °C",
                                    style={
                                        "backgroundColor": "#FFDAB9",
                                        "padding": "8px",
                                        "margin": "4px",
                                    }
                                ),
                                html.Div(
                                    f"Sydney: {syd_temp:.1f} °C",
                                    style={
                                        "backgroundColor": "#FFDAB9",
                                        "padding": "8px",
                                        "margin": "4px",
                                    }
                                ),
                                html.Div(
                                    f"New York: {ny_temp:.1f} °C",
                                    style={
                                        "backgroundColor": "#FFDAB9",
                                        "padding": "8px",
                                        "margin": "4px",
                                    }
                                ),
                                html.Div(
                                    f"Shanghai: {sh_temp:.1f} °C",
                                    style={
                                        "backgroundColor": "#FFDAB9",
                                        "padding": "8px",
                                        "margin": "4px",
                                    }
                                ),
                            ],
                            style={
                                "backgroundColor": "#FEC89A",
                                "padding": "8px",
                                "margin": "4px",
                                "flex": "1",
                            }
                        ),

                        # Testing Div 3
                        html.Div(
                            "Testing Div 3",
                            style={
                                "backgroundColor": "#A9E4DE",
                                "padding": "8px",
                                "margin": "4px",
                                "flex": "1",
                            }
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "flex": "1",
                        "minHeight": "0",
                    }
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "row",
                "flex": "1",
                "minHeight": "0",
            }
        ),
    ],
    style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "padding": "8px",
        "boxSizing": "border-box",
    }
)

if __name__ == "__main__":
    app.run(debug=True)
