
from dash import Dash, html, dcc

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Weather you lose or win, isn't our problem"),
        html.Div(
            [
                html.Div("Testing Div 1",
                    style={
                        "backgroundColor": "#E0D4E7",
                        "padding": "8px",
                        "margin": "4px",
                        # "height": "100%",
                        "width": "50%",
                    }
                ),
                html.Div(
                    [
                    html.Div("Testing Div 2",
                        style={
                            "backgroundColor": "#FEC89A",
                            "padding": "8px",
                            "margin": "4px",
                            "flex": "1",

                        }
                    ),
                    html.Div("Testing Div 3",
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
                        "height": "100%",
                    }
                )
            ],
            style={
                "display": "flex",
                "width": "100%",
                "flex": "1",
                "height": "100%",
                # "padding": "8px"
            }
            
        )
        
    ],
    style={
        "display": "flex",
        "flexDirection":"column",
        "height": "100vh",
        "padding": "8px"
    }
)

if __name__ == "__main__":
    app.run(debug=True)