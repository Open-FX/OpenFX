import yfinance as yf              # Fetch FX data from Yahoo Finance
import pandas as pd               # Data handling
import time                       # Sleep / timing
import matplotlib.pyplot as plt   # Plotting
from datetime import datetime     # Timestamps


# -------------------------------
# Function: Fetch live FX data
# -------------------------------
def get_live_fx(pair="EURUSD=X"):
    """
    Fetch latest 1-minute FX price data for the last day.
    """
    try:
        ticker = yf.Ticker(pair)
        df = ticker.history(period="1d", interval="1m")
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        print(f"Error fetching {pair}: {e}")
        return pd.DataFrame()


# -------------------------------
# Function: Calculate percentage change
# -------------------------------
def calculate_percent_change(df, lookback=5):
    """
    Calculates percentage price change over 'lookback' minutes.
    """
    if len(df) < lookback:
        return 0.0

    current_price = df["Close"].iloc[-1]
    old_price = df["Close"].iloc[-lookback]

    return ((current_price - old_price) / old_price) * 100


# -------------------------------
# Function: Alert threshold check
# -------------------------------
def should_alert(pct_change, threshold=0.1):
    """
    Returns True if price movement exceeds threshold.
    """
    return abs(pct_change) >= threshold


# -------------------------------
# Function: Print alert message
# -------------------------------
def print_alert(pair, pct_change, price):
    """
    Prints formatted alert message to terminal.
    """
    direction = "📈" if pct_change > 0 else "📉"

    if (pct_change <0.5 and pct_change > 0) or (pct_change > -0.5 and pct_change < 0):
        print("\n" + "=" * 60)
        print(f"🚨 MINOR ALERT - {pair}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Price: ${price:.5f}")
        print(f"Move: {direction} {pct_change:+.2f}%")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print(f"🚨 MAJOR ALERT - {pair}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Price: ${price:.5f}")
        print(f"Move: {direction} {pct_change:+.2f}%")
        print("=" * 60 + "\n")
        


# -------------------------------
# Function: Initialize dashboard
# -------------------------------
def init_dashboard(pairs):
    """
    Creates a single matplotlib dashboard with subplots
    and returns references to line objects for live updates.
    """
    plt.ion()  # Interactive mode ON (non-blocking updates)

    fig = plt.figure(figsize=(14, 8))
    fig.suptitle("OpenFX Live Volatility Dashboard", fontsize=16)

    # Grid layout: 2 rows, 3 columns
    grid_positions = {
        pairs[0]: (2, 3, 1),
        pairs[1]: (2, 3, 2),
        pairs[2]: (2, 3, 4),
        pairs[3]: (2, 3, 5),
        pairs[4]: (2, 3, 3),
        pairs[5]: (2, 3, 6)
    }

    plots = {}

    for pair, pos in grid_positions.items():
        ax = fig.add_subplot(*pos)
        ax.set_title(pair.replace("=X", ""))
        ax.set_xlabel("Time")
        ax.set_ylabel("Price")
        ax.grid(True)

        # Create an empty line (data filled later)
        line, = ax.plot([], [], linewidth=2)

        plots[pair] = {
            "ax": ax,
            "line": line
        }

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig, plots


# -------------------------------
# Function: Update subplot data
# -------------------------------
def update_plot(plot_obj, df):
    """
    Updates an existing subplot with new price data.
    """
    if df.empty:
        return

    times = df.index
    prices = df["Close"]

    line = plot_obj["line"]
    ax = plot_obj["ax"]

    line.set_data(times, prices)
    ax.relim()
    ax.autoscale_view()


# -------------------------------
# Main Monitoring Loop
# -------------------------------
def main():
    """
    Runs FX monitoring, alerts, and dashboard updates every 60 seconds.
    """

    pairs = [
        "EURUSD=X",
        "USDJPY=X",
        "GBPUSD=X",
        "USDCHF=X",
        "USDCAD=X",
        "AUDUSD=X"
        
    ]

    alert_threshold = 0.1

    # Initialize dashboard
    fig, plots = init_dashboard(pairs)

    print("\n" + "=" * 60)
    print("🚀 OpenFX Monitoring Engine Started")
    print(f"Tracking {len(pairs)} currency pairs")
    print("Dashboard active | Updates every 60 seconds")
    print("Press Ctrl+C to exit")
    print("=" * 60 + "\n")

    cycle = 0

    try:
        while True:
            cycle += 1
            print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)

            alerts = 0

            for pair in pairs:
                data = get_live_fx(pair)

                if data.empty:
                    print(f"⚠ {pair.replace('=X','')}: No data")
                    continue

                # Update dashboard plot
                update_plot(plots[pair], data)

                # Calculate movement
                pct_change = calculate_percent_change(data)
                price = data["Close"].iloc[-1]

                # Alert logic
                if should_alert(pct_change, alert_threshold):
                    print_alert(pair.replace("=X", ""), pct_change, price)
                    alerts += 1
                else:
                    print(f"✓ {pair.replace('=X','')}: ${price:.5f} ({pct_change:+.2f}%)")

            # Redraw entire dashboard
            fig.canvas.draw()
            fig.canvas.flush_events()

            print(f"\nStatus: {alerts} alerts | Next update in 60s\n")
            plt.pause(60)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("🛑 Monitoring stopped by user")
        print(f"Total cycles completed: {cycle}")
        print("=" * 60 + "\n")
        plt.ioff()
        plt.show(block=False)


# -------------------------------
# Run the engine
# -------------------------------
if __name__ == "__main__":
    main()

