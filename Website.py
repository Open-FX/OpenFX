import dash
from dash import dcc, html, callback, Input, Output, State
import pandas as pd 
import yfinance as yf 
from datetime import datetime, timedelta
import plotly.graph_objects as go
from functools import lru_cache
 
# Initialize Dash app
app = dash.Dash(__name__)
app.title = "OpenFX Live Dashboard"

# Default FX pairs
DEFAULT_PAIRS = [
    "EURUSD=X", 
    "USDJPY=X", 
    "GBPUSD=X", 
    "USDCHF=X", 
    "USDCAD=X", 
    "AUDUSD=X"
]

# Fetch FX Data 
@lru_cache(maxsize=32)
def get_live_fx(pair="EURUSD=X"): 
    try:
        ticker = yf.Ticker(pair) 
        df = ticker.history(period="1d", interval="1m")
        return df if not df.empty else pd.DataFrame()
    except: 
        return pd.DataFrame()

# Percent Change 
def calculate_percent_change(df, lookback=5):
    if len(df) < lookback:
        return 0.0
    current_price = df["Close"].iloc[-1]
    old_price = df["Close"].iloc[-lookback]
    return ((current_price - old_price) / old_price) * 100

# Alert Logic 
def classify_alert(pct):
    if abs(pct) < 0.1:
        return None
    if abs(pct) < 0.5:
        return "minor"
    return "major"

# App Layout
app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),
    
    html.Div([
        # Header
        html.Div([
            html.H1("OpenFX Live Volatility Dashboard", style={'textAlign': 'center', 'marginBottom': '10px'}),
            html.P("Real‑time FX monitoring with alerts and live charts.", style={'textAlign': 'center', 'color': '#666'}),
        ], style={'borderBottom': '2px solid #ddd', 'paddingBottom': '20px', 'marginBottom': '20px'}),
        
        # Main container with sidebar
        html.Div([
            # Sidebar
            html.Div([
                html.H3("Settings"),
                
                html.Label("Select FX Pairs:", style={'fontWeight': 'bold', 'marginTop': '20px'}),
                dcc.Dropdown(
                    id='pair-selector',
                    options=[{'label': pair.replace('=X', ''), 'value': pair} for pair in DEFAULT_PAIRS],
                    value=DEFAULT_PAIRS,
                    multi=True,
                    style={'width': '100%'}
                ),
                
                html.Div([
                    html.Label("Lookback (minutes):", style={'fontWeight': 'bold', 'marginTop': '20px'}),
                    dcc.Slider(
                        id='lookback-slider',
                        min=1,
                        max=30,
                        value=5,
                        marks={1: '1', 10: '10', 20: '20', 30: '30'},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ]),
                
                html.Div([
                    html.Label("Refresh every (seconds):", style={'fontWeight': 'bold', 'marginTop': '20px'}),
                    dcc.Slider(
                        id='refresh-slider',
                        min=10,
                        max=120,
                        value=60,
                        marks={10: '10s', 30: '30s', 60: '60s', 120: '120s'},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ]),
                
                
                html.Div([
                    html.P("Dashboard auto‑refreshes at selected interval.", 
                           style={'marginTop': '30px', 'padding': '10px', 'backgroundColor': "#ab447b", 
                                  'borderLeft': '4px solid #2196F3', 'borderRadius': '4px', 'fontSize': '13px'})
                ]),
                
            ], style={
                'width': '22%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'padding': '20px',
                'backgroundColor': '#f9f9f9',
                'borderRight': '1px solid #ddd',
                'minHeight': '100vh'
            }),
            
            # Main content
            html.Div([
                html.Div(id='last-update', style={'textAlign': 'right', 'color': '#999', 'marginBottom': '20px'}),
                
                # Live Prices Section
                html.Div([
                    html.H2("Live FX Prices", style={'marginBottom': '20px'}),
                    html.Div(id='metrics-container', style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),
                ]),
                
                # Alerts Section
                html.Div([
                    html.H2("Alerts", style={'marginBottom': '20px'}),
                    html.Div(id='alerts-container'),
                ], style={'marginBottom': '30px'}),
                
                # Charts Section
                html.Div([
                    html.H2("Price Charts", style={'marginBottom': '20px'}),
                    html.Div(id='charts-container')
                ]),
                
            ], style={
                'width': '78%',
                'display': 'inline-block',
                'padding': '20px',
                'verticalAlign': 'top'
            })
        ], style={'display': 'flex'}),
        
    ], style={'maxWidth': '1400px', 'margin': '0 auto'})
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#fff', 'padding': '20px'})

# Callbacks
@callback(
   Output('interval-component', 'interval'),
   Input('refresh-slider', 'value')
)
def update_refresh_rate(refresh_seconds):
    return refresh_seconds * 1000

@callback(
    Output('last-update', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_timestamp(n):
    return f"Updated {datetime.now().strftime('%H:%M:%S')}"

@callback(
    [Output('metrics-container', 'children'),
     Output('alerts-container', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('pair-selector', 'value'),
     Input('lookback-slider', 'value')],
    prevent_initial_call=False
)
def update_dashboard(n_intervals, selected_pairs, lookback):
    if not selected_pairs:
        selected_pairs = DEFAULT_PAIRS
    
    metrics = []
    alerts = []
    
    for pair in selected_pairs:
        df = get_live_fx(pair)
        
        if df.empty:
            metrics.append(
                html.Div([
                    html.H4(pair.replace('=X', '')),
                    html.P("No data available", style={'color': '#d32f2f'})
                ], style={'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'backgroundColor': '#fff3e0'})
            )
            continue
        
        pct = calculate_percent_change(df, lookback)
        price = df["Close"].iloc[-1]
        alert_type = classify_alert(pct)
        
        # Metric card
        color = "#4caf50" if pct >= 0 else "#d32f2f"
        metrics.append(
            html.Div([
                html.H4(pair.replace('=X', ''), style={'margin': '0 0 10px 0'}),
                html.H2(f"{price:.5f}", style={'margin': '10px 0', 'color': '#333'}),
                html.P(f"{pct:+.2f}%", style={'margin': '0', 'fontSize': '16px', 'color': color, 'fontWeight': 'bold'})
            ], style={
                'padding': '20px',
                'border': '1px solid #ddd',
                'borderRadius': '8px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        )
        
        # Alerts
        if alert_type == "minor":
            alerts.append(
                html.Div([
                    html.H4(f"⚠️ MINOR ALERT – {pair.replace('=X', '')}", style={'color': '#f57c00', 'margin': '0 0 10px 0'}),
                    html.P(f"Price: {price:.5f}"),
                    html.P(f"Move: {pct:+.2f}%")
                ], style={
                    'padding': '15px',
                    'border': '1px solid #ffb74d',
                    'borderRadius': '4px',
                    'backgroundColor': '#fff3e0',
                    'marginBottom': '10px'
                })
            )
        elif alert_type == "major":
            alerts.append(
                html.Div([
                    html.H4(f"🚨 MAJOR ALERT – {pair.replace('=X', '')}", style={'color': '#d32f2f', 'margin': '0 0 10px 0'}),
                    html.P(f"Price: {price:.5f}"),
                    html.P(f"Move: {pct:+.2f}%")
                ], style={
                    'padding': '15px',
                    'border': '1px solid #ef5350',
                    'borderRadius': '4px',
                    'backgroundColor': '#ffebee',
                    'marginBottom': '10px'
                })
            )
    
    if not alerts:
        alerts = [html.Div([
            html.P("✓ No alerts triggered", style={'color': '#4caf50', 'fontWeight': 'bold'})
        ], style={'padding': '15px', 'border': '1px solid #81c784', 'borderRadius': '4px', 'backgroundColor': '#f1f8e9'})]
    
    return metrics, alerts

@callback(
    Output('charts-container', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('pair-selector', 'value')],
    prevent_initial_call=False
)
def update_charts(n_intervals, selected_pairs):
    if not selected_pairs:
        selected_pairs = DEFAULT_PAIRS
    
    charts = []
    
    for pair in selected_pairs:
        df = get_live_fx(pair)
        
        if df.empty:
            continue
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Close'],
            mode='lines',
            name=pair.replace('=X', ''),
            line=dict(color='#2196F3', width=2)
        ))
        
        fig.update_layout(
            title=pair.replace('=X', ''),
            xaxis_title='Time',
            yaxis_title='Price',
            hovermode='x unified',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        charts.append(
            html.Div([
                dcc.Graph(figure=fig)
            ], style={'marginBottom': '30px'})
        )
    
    return charts

if __name__ == '__main__':
    app.run(debug=True)