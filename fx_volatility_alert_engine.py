import yfinance as yf              # Fetch FX data from Yahoo Finance
import pandas as pd               # Data handling
import time                       # Sleep / timing
import matplotlib.pyplot as plt   # Plotting
from datetime import datetime     # Timestamps
import mplcursors                 # Hover tooltips


# ==========================================================
# FUNCTION: Fetch live FX data
# ==========================================================
def get_live_fx(pair="EURUSD=X"):
    """
    Fetch latest 1-minute FX price data for the last day.
    Returns empty DataFrame if fetch fails.
    """
    try:
        ticker = yf.Ticker(pair)                          # Create ticker object for currency pair
        df = ticker.history(period="1d", interval="1m")   # Get 1-minute interval data for today
        return df if not df.empty else pd.DataFrame()     # Return data or empty DataFrame
    except Exception as e:
        print(f"Error fetching {pair}: {e}")              # Print error if fetch fails
        return pd.DataFrame()                             # Return empty DataFrame


# ==========================================================
# FUNCTION: Calculate percentage change
# ==========================================================
def calculate_percent_change(df, lookback=5):
    """
    Calculates percentage price change over 'lookback' minutes.
    """
    if len(df) < lookback:                    # If not enough data points
        return 0.0                            # Return 0%

    current_price = df["Close"].iloc[-1]      # Latest price
    old_price = df["Close"].iloc[-lookback]   # Price X minutes ago

    return ((current_price - old_price) / old_price) * 100  # % change formula


# ==========================================================
# FUNCTION: Alert threshold check
# ==========================================================
def should_alert(pct_change, threshold=0.1):
    """
    Returns True if absolute percentage change exceeds threshold.
    """
    return abs(pct_change) >= threshold        # True if movement exceeds threshold


# ==========================================================
# FUNCTION: Print alert message
# ==========================================================
def print_alert(pair, pct_change, price):
    """
    Prints formatted alert message to terminal.
    """
    direction = "📈" if pct_change > 0 else "📉"  # Determine up/down direction

    print("\n" + "=" * 60)

    if abs(pct_change) < 0.5:                  # Minor alert condition
        print(f"🚨 MINOR ALERT - {pair}")
    else:                                      # Major alert condition
        print(f"🚨 MAJOR ALERT - {pair}")

    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Price: ${price:.5f}")
    print(f"Move: {direction} {pct_change:+.2f}%")
    print("=" * 60 + "\n")


# ==========================================================
# FUNCTION: Initialize dashboard
# ==========================================================
def init_dashboard(pairs):
    """
    Creates matplotlib dashboard with ONE visible graph at a time.
    LEFT / RIGHT arrow keys switch between pairs.
    """

    plt.ion()                                  # Turn on interactive mode

    fig = plt.figure(figsize=(14, 8))           # Create figure window
    fig.suptitle("OpenFX Live Volatility Dashboard", fontsize=16)

    plots = {}                                 # Dictionary to store plot data
    current_index = {"value": 0}                # Track which pair is visible

    for pair in pairs:

        ax = fig.add_subplot(111)               # Create subplot
        ax.set_title(pair.replace("=X", ""))    # Remove '=X' from title
        ax.set_xlabel("Time")                   # X-axis label
        ax.set_ylabel("Price")                  # Y-axis label
        ax.grid(True)                           # Show grid

        line, = ax.plot([], [], linewidth=2)    # Main price line

        ax.set_visible(False)                   # Hide initially

        plots[pair] = {
            "ax": ax,
            "line": line,
            "spike_lines": [],
            "cursor": None
        }

    plots[pairs[0]]["ax"].set_visible(True)     # Show first pair

    def on_key(event):
        if event.key not in ["left", "right"]:
            return

        current_pair = pairs[current_index["value"]]
        plots[current_pair]["ax"].set_visible(False)

        if event.key == "right":
            current_index["value"] = (current_index["value"] + 1) % len(pairs)
        else:
            current_index["value"] = (current_index["value"] - 1) % len(pairs)

        new_pair = pairs[current_index["value"]]
        plots[new_pair]["ax"].set_visible(True)

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("key_press_event", on_key)

    return fig, plots


# ==========================================================
# FUNCTION: Update subplot data
# ==========================================================
def update_plot(plot_obj, df):
    """
    Updates an existing subplot with new price data.
    """

    if df.empty:
        return

    times = df.index                    # Time index
    prices = df["Close"]                # Closing prices

    line = plot_obj["line"]
    ax = plot_obj["ax"]

    line.set_data(times, prices)        # Update line data

    ax.relim()                          # Recalculate axis limits
    ax.autoscale_view()                 # Autoscale


# ==========================================================
# FUNCTION: Draw vertical spike marker
# FIXED: No NoneType DPI error
# All spikes show tooltips
# Clicking annotation hides it safely
# ==========================================================
def draw_spike_line(plot_obj, timestamp, price, pct_change, is_major):

    ax = plot_obj["ax"]

    color = "red" if is_major else "blue"

    ymin, ymax = ax.get_ylim()
    height = (ymax - ymin) * 0.15

    spike_line = ax.plot(
        [timestamp, timestamp],
        [price - height / 2, price + height / 2],
        color=color,
        linewidth=1.5,
        alpha=0.85
    )[0]

    # Attach spike metadata directly to the line
    spike_line.spike_data = {
        "timestamp": timestamp,
        "price": price,
        "pct_change": pct_change,
        "is_major": is_major
    }

    plot_obj["spike_lines"].append(spike_line)

    # Keep only last 8 spikes
    if len(plot_obj["spike_lines"]) > 8:
        old_line = plot_obj["spike_lines"].pop(0)
        old_line.remove()

    # Create cursor once per axis
    if plot_obj["cursor"] is None:

        cursor = mplcursors.cursor(plot_obj["spike_lines"], hover=True)
        plot_obj["cursor"] = cursor

        @cursor.connect("add")
        def on_add(sel):

            # Only respond to spike lines
            if not hasattr(sel.artist, "spike_data"):
                sel.annotation.set_visible(False)
                return

            data = sel.artist.spike_data

            spike_type = "MAJOR SPIKE" if data["is_major"] else "MINOR ALERT"

            sel.annotation.set_text(
                f"{spike_type}\n"
                f"Time: {data['timestamp'].strftime('%H:%M:%S')}\n"
                f"Price: {data['price']:.5f}\n"
                f"Move: {data['pct_change']:+.2f}%"
            )

            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

            # Make annotation clickable
            sel.annotation.set_picker(True)

        # Handle annotation click removal
        @cursor.connect("remove")
        def on_remove(sel):
            sel.annotation.set_visible(False)



# ==========================================================
# MAIN MONITORING LOOP
# ==========================================================
def main():

    pairs = [
        "EURUSD=X",
        "USDJPY=X",
        "GBPUSD=X",
        "USDCHF=X",
        "USDCAD=X",
        "AUDUSD=X"
    ]

    alert_threshold = 0.01
    spike_threshold = 0.03

    fig, plots = init_dashboard(pairs)

    print("\n" + "=" * 60)
    print("🚀 OpenFX Monitoring Engine Started")
    print(f"Tracking {len(pairs)} currency pairs")
    print("Use LEFT / RIGHT arrows to switch charts")
    print("Updates every 60 seconds")
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
                timestamp = data.index[-1]

                if should_alert(pct_change, alert_threshold):

                    print_alert(pair.replace("=X", ""), pct_change, price)
                    alerts += 1

                    is_major = abs(pct_change) >= spike_threshold

                    draw_spike_line(
                        plots[pair],
                        timestamp,
                        price,
                        pct_change,
                        is_major
                    )

                else:
                    print(f"✓ {pair.replace('=X','')}: ${price:.5f} ({pct_change:+.2f}%)")

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


# ==========================================================
# RUN ENGINE
# ==========================================================
if __name__ == "__main__":
    main()




