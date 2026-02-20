import yfinance as yf              # Fetch FX data from Yahoo Finance
import pandas as pd               # Data handling
import time                       # Sleep / timing
import matplotlib.pyplot as plt   # Plotting
from datetime import datetime     # Timestamps
import mplcursors                 # Hover tooltips for spike lines


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

    print("\n" + "=" * 60)

    if abs(pct_change) < 0.5:
        print(f"🚨 MINOR ALERT - {pair}")
    else:
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
    Creates a matplotlib dashboard with subplots.
    Also prepares storage for volatility spike lines.
    """
    plt.ion()

    fig = plt.figure(figsize=(14, 8))
    fig.suptitle("OpenFX Live Volatility Dashboard", fontsize=16)

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

        # Main price line
        line, = ax.plot([], [], linewidth=2)

        plots[pair] = {
            "ax": ax,
            "line": line,
            "spike_lines": []  # Stores vertical spike markers
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
# Function: Draw vertical spike marker (SHORT LINE VERSION)
# -------------------------------
def draw_spike_line(plot_obj, timestamp, price, pct_change, is_major):
    """
    Draws a SHORT vertical line at spike timestamp.
    Red = major spike
    Blue = minor spike
    """

    ax = plot_obj["ax"]

    # Choose spike color
    color = "red" if is_major else "blue"

    # Get current y-axis limits
    ymin, ymax = ax.get_ylim()

    # Calculate 15% of chart height
    height = (ymax - ymin) * 0.15

    # Draw a SHORT vertical line centered at spike price
    spike_line = ax.plot(
        [timestamp, timestamp],                   # Same X (vertical line)
        [price - height/2, price + height/2],     # Small Y-range only
        color=color,
        linewidth=1.5,
        alpha=0.85
    )[0]

    # Store line reference
    plot_obj["spike_lines"].append(spike_line)

    # Limit stored spike markers to last 8 (prevents clutter)
    if len(plot_obj["spike_lines"]) > 8:
        old_line = plot_obj["spike_lines"].pop(0)
        old_line.remove()

    # Add hover tooltip
    cursor = mplcursors.cursor(spike_line, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        spike_type = "MAJOR SPIKE" if is_major else "MINOR ALERT"

        sel.annotation.set_text(
            f"{spike_type}\n"
            f"Time: {timestamp.strftime('%H:%M:%S')}\n"
            f"Price: {price:.5f}\n"
            f"Move: {pct_change:+.2f}%"
        )
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)


# -------------------------------
# Main Monitoring Loop
# -------------------------------
def main():

    pairs = [
        "EURUSD=X",
        "USDJPY=X",
        "GBPUSD=X",
        "USDCHF=X",
        "USDCAD=X",
        "AUDUSD=X"
    ]

    alert_threshold = 0.001     # Minor alert trigger
    spike_threshold = 0.3     # Major spike trigger

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

                update_plot(plots[pair], data)

                pct_change = calculate_percent_change(data)
                price = data["Close"].iloc[-1]
                timestamp = data.index[-1]  # Capture spike time

                if should_alert(pct_change, alert_threshold):
                    print_alert(pair.replace("=X", ""), pct_change, price)
                    alerts += 1

                    # Determine if major or minor
                    is_major = abs(pct_change) >= spike_threshold

                    # Draw vertical spike marker
                    draw_spike_line(
                        plots[pair],
                        timestamp,
                        price,
                        pct_change,
                        is_major
                    )
                else:
                    print(f"✓ {pair.replace('=X','')}: ${price:.5f} ({pct_change:+.2f}%)")

            # Refresh dashboard
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
