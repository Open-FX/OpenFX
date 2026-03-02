## REMEMBER: Limited to 100 requests per day.
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
        ticker = yf.Ticker(pair)                          # Create ticker object
        df = ticker.history(period="1d", interval="1m")   # Request 1-minute data
        return df if not df.empty else pd.DataFrame()     # Return data or empty DataFrame
    except Exception as e:
        print(f"Error fetching {pair}: {e}")              # Print error message
        return pd.DataFrame()                             # Return safe empty DataFrame


# ==========================================================
# FUNCTION: Calculate percentage change
# ==========================================================
def calculate_percent_change(df, lookback=5):
    """
    Calculates percentage price change over 'lookback' minutes.
    """

    if len(df) < lookback:         # Prevent indexing error if insufficient rows
        return 0.0

    current_price = df["Close"].iloc[-1]      # Most recent closing price
    old_price = df["Close"].iloc[-lookback]   # Price X minutes ago

    # Standard percentage change formula
    return ((current_price - old_price) / old_price) * 100


# ==========================================================
# FUNCTION: Alert threshold check
# ==========================================================
def should_alert(pct_change, threshold=0.1):
    """
    Returns True if absolute percentage change exceeds threshold.
    """
    return abs(pct_change) >= threshold


# ==========================================================
# FUNCTION: Print alert message
# ==========================================================
def print_alert(pair, pct_change, price):
    """
    Prints formatted alert message to terminal.
    """

    direction = "\U0001f4c8" if pct_change > 0 else "\U0001f4c9"  # Determine arrow direction

    print("\n" + "=" * 60)

    # Determine whether movement qualifies as major or minor
    if abs(pct_change) < 0.5:
        print(f"\U0001f6a8 MINOR ALERT - {pair}")
    else:
        print(f"\U0001f6a8 MAJOR ALERT - {pair}")

    # Print current timestamp
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Print formatted price
    print(f"Price: ${price:.5f}")

    # Print formatted percentage movement
    print(f"Move: {direction} {pct_change:+.2f}%")

    print("=" * 60 + "\n")


# ========================================================== 
def rebuild_cursor(fig, plots, pairs, current_index):
    """
    Removes any existing shared cursor, then creates a new one
    bound ONLY to the currently visible pair's spike lines.
    This prevents cross-pair cursor conflicts that cause duplicate tooltips.
    """

    # Remove old shared cursor if it exists
    if hasattr(fig, "_shared_cursor") and fig._shared_cursor is not None:
        fig._shared_cursor.remove()
        fig._shared_cursor = None

    # Get the currently visible pair's spike lines
    visible_pair = pairs[current_index["value"]]
    visible_spikes = plots[visible_pair]["spike_lines"]

    if not visible_spikes:
        return  # Nothing to attach a cursor to

    # Create a single cursor tracking only the visible pair's spikes
    fig._shared_cursor = mplcursors.cursor(visible_spikes, hover=True)

    @fig._shared_cursor.connect("add")
    def on_add(sel):
        # Safety guard: ignore non-spike artists
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


# ==========================================================
# FUNCTION: Initialize dashboard
# ==========================================================
def init_dashboard(pairs):
    """
    Creates matplotlib dashboard with ONE visible graph at a time.
    LEFT / RIGHT arrow keys switch between pairs.
    """

    plt.ion()  # Turn on interactive mode for real-time updates

    fig = plt.figure(figsize=(14, 8))  # Create figure window
    fig.suptitle("OpenFX Live Volatility Dashboard", fontsize=16)

    # Initialize the shared cursor attribute on the figure
    fig._shared_cursor = None

    plots = {}                         # Store subplot data per currency pair
    current_index = {"value": 0}       # Track which pair is currently visible

    for pair in pairs:
        #  Use fig.add_axes with a unique label per pair so each pair
        # gets its own independent axes object
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], label=pair)

        ax.set_title(pair.replace("=X", ""))  # Remove '=X' for display
        ax.set_xlabel("Time")
        ax.set_ylabel("Price")
        ax.grid(True)

        line, = ax.plot([], [], linewidth=2)  # Create empty price line

        ax.set_visible(False)  # Hide all charts initially

        # Store references needed later
        plots[pair] = {
            "ax": ax,
            "line": line,
            "spike_lines": [],   # Stores vertical spike markers
        }

    # Make first pair visible
    plots[pairs[0]]["ax"].set_visible(True)

    # Keyboard navigation handler
    def on_key(event):

        if event.key not in ["left", "right"]:
            return

        # Hide current axis
        current_pair = pairs[current_index["value"]]
        plots[current_pair]["ax"].set_visible(False)

        # Update index depending on arrow direction
        if event.key == "right":
            current_index["value"] = (current_index["value"] + 1) % len(pairs)
        else:
            current_index["value"] = (current_index["value"] - 1) % len(pairs)

        # Show new axis
        new_pair = pairs[current_index["value"]]
        plots[new_pair]["ax"].set_visible(True)

        #Rebuild cursor for the newly visible pair so tooltips
        # only respond to the active pair's spike lines
        rebuild_cursor(fig, plots, pairs, current_index)

        fig.canvas.draw_idle()  # Refresh display

    fig.canvas.mpl_connect("key_press_event", on_key)

    return fig, plots, current_index


# ==========================================================
# FUNCTION: Update subplot data
# ==========================================================
def update_plot(plot_obj, df):
    """
    Updates an existing subplot with new price data.
    """

    if df.empty:
        return  # Skip update if no data

    times = df.index
    prices = df["Close"]

    line = plot_obj["line"]
    ax = plot_obj["ax"]

    line.set_data(times, prices)  # Update line values

    ax.relim()                    # Recalculate axis bounds
    ax.autoscale_view()           # Auto-scale to fit new data


# ==========================================================
# FUNCTION: Draw vertical spike marker
# ==========================================================
def draw_spike_line(fig, plots, pairs, current_index, plot_obj, timestamp, price, pct_change, is_major):

    ax = plot_obj["ax"]

    color = "red" if is_major else "blue"

    ymin, ymax = ax.get_ylim()
    height = (ymax - ymin) * 0.15  # Spike visual height scaling

    # Create vertical line
    spike_line = ax.plot(
        [timestamp, timestamp],
        [price - height / 2, price + height / 2],
        color=color,
        linewidth=1.5,
        alpha=0.85
    )[0]

    # Attach spike metadata to the line object
    spike_line.spike_data = {
        "timestamp": timestamp,
        "price": price,
        "pct_change": pct_change,
        "is_major": is_major
    }

    plot_obj["spike_lines"].append(spike_line)

    # Limit to last 8 spikes
    if len(plot_obj["spike_lines"]) > 8:
        old_line = plot_obj["spike_lines"].pop(0)
        old_line.remove()

    # single shared cursor so it tracks the updated spike lines for the currently visible pair.
    rebuild_cursor(fig, plots, pairs, current_index)


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

    alert_threshold = 0.01   # % move to trigger alert
    spike_threshold = 0.03   # % move to classify as major spike

    fig, plots, current_index = init_dashboard(pairs)

    print("\n" + "=" * 60)
    print("\U0001f680 OpenFX Monitoring Engine Started")
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
                    print(f"\u26a0 {pair.replace('=X','')}: No data")
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
                        fig,
                        plots,
                        pairs,
                        current_index,
                        plots[pair],
                        timestamp,
                        price,
                        pct_change,
                        is_major
                    )

                else:
                    print(f"\u2713 {pair.replace('=X','')}: ${price:.5f} ({pct_change:+.2f}%)")

            fig.canvas.draw()
            fig.canvas.flush_events()

            print(f"\nStatus: {alerts} alerts | Next update in 60s\n")

            plt.pause(60)

    except KeyboardInterrupt:

        print("\n" + "=" * 60)
        print("\U0001f6d1 Monitoring stopped by user")
        print(f"Total cycles completed: {cycle}")
        print("=" * 60 + "\n")

        plt.ioff()
        plt.show(block=False)


# ==========================================================
# RUN ENGINE
# ==========================================================
if __name__ == "__main__":
    main()





