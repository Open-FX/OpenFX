## REMEMBER: Limited to 100 requests per day from Yahoo Finance
## This engine monitors top 5 currency pairs and updates every 60 seconds

import yfinance as yf       # Library to fetch live FX data from Yahoo Finance
import pandas as pd         # Library for handling data tables
import time                 # Library to create delays between updates
from datetime import datetime  # Library to display current date/time

# -------------------------------
# Function: Fetch live FX data
# -------------------------------
def get_live_fx(pair="EURUSD=X"):
    """
    Fetches the latest FX price data from Yahoo Finance.
    
    Args:
        pair (str): Currency pair ticker (e.g., "EURUSD=X")
    
    Returns:
        pd.DataFrame: Latest price data, or empty if failed
    """
    try:
        ticker = yf.Ticker(pair)  # Create ticker object for the currency pair
        df = ticker.history(period="1d", interval="1m")  # Get last day of 1-minute data
        
        if df.empty:  # Check if we got data back
            return pd.DataFrame()  # Return empty if no data
        
        return df  # Return the price data
    except Exception as e:
        print(f"Error fetching {pair}: {e}")  # Print error message
        return pd.DataFrame()  # Return empty on error

# -------------------------------
# Function: Calculate percentage change
# -------------------------------
def calculate_percent_change(df, lookback=5):
    """
    Calculates the percentage change over the last few minutes.
    
    Args:
        df: DataFrame with price data
        lookback: How many minutes back to compare (default: 5)
    
    Returns:
        float: Percentage change (e.g., 0.85 means +0.85%)
    """
    if len(df) < lookback:  # Make sure we have enough data points
        return 0.0
    
    # Get current price (most recent)
    current_price = df['Close'].iloc[-1]
    
    # Get price from 'lookback' minutes ago
    old_price = df['Close'].iloc[-lookback]
    
    # Calculate percentage change: ((new - old) / old) * 100
    pct_change = ((current_price - old_price) / old_price) * 100
    
    return pct_change

# -------------------------------
# Function: Check if alert should trigger
# -------------------------------
def should_alert(pct_change, threshold=0.5):
    """
    Determines if the price change is large enough to trigger an alert.
    
    Args:
        pct_change: Percentage change in price
        threshold: Minimum change to trigger alert (default: 0.5%)
    
    Returns:
        bool: True if alert should be triggered
    """
    # Check if absolute value of change exceeds threshold
    return abs(pct_change) >= threshold

# -------------------------------
# Function: Print alert message
# -------------------------------
def print_alert(pair, pct_change, current_price):
    """
    Prints a formatted ALERT message to the terminal.
    
    Args:
        pair: Currency pair symbol (e.g., "EUR/USD")
        pct_change: Percentage change value
        current_price: Current price of the pair
    """
    # Choose symbol based on direction of change
    direction = "📈" if pct_change > 0 else "📉"
    
    # Print the alert message
    print(f"\n{'='*60}")
    print(f"🚨 ALERT - {pair}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Current Price: ${current_price:.5f}")
    print(f"   Change: {direction} {pct_change:+.2f}%")
    print(f"{'='*60}\n")

# -------------------------------
# Function: Monitor single currency pair
# -------------------------------
def monitor_pair(pair, threshold=0.5):
    """
    Checks one currency pair and prints alert if needed.
    
    Args:
        pair: Currency pair ticker (e.g., "EURUSD=X")
        threshold: Alert threshold percentage
    
    Returns:
        dict: Status information about this pair
    """
    # Fetch live data
    data = get_live_fx(pair)
    
    if data.empty:  # If no data, skip this pair
        return None
    
    # Calculate percentage change
    pct_change = calculate_percent_change(data, lookback=5)
    
    # Get current price
    current_price = data['Close'].iloc[-1]
    
    # Check if we should alert
    if should_alert(pct_change, threshold):
        # Print alert to terminal
        print_alert(pair.replace("=X", ""), pct_change, current_price)
    
    # Return status info
    return {
        'pair': pair,
        'price': current_price,
        'change': pct_change,
        'alerted': should_alert(pct_change, threshold)
    }

# -------------------------------
# Main Monitoring Loop
# -------------------------------
def main():
    """
    Main function that runs continuously every 60 seconds.
    Monitors top 5 currency pairs and prints alerts when needed.
    """
    # Top 5 most traded currency pairs (Yahoo Finance format)
    top_5_pairs = [
        "EURUSD=X",  # Euro / US Dollar (most traded)
        "USDJPY=X",  # US Dollar / Japanese Yen
        "GBPUSD=X",  # British Pound / US Dollar
        "AUDUSD=X",  # Australian Dollar / US Dollar
        "USDCAD=X"   # US Dollar / Canadian Dollar
    ]
    
    # Alert threshold (0.5% change triggers alert)
    alert_threshold = 0.5
    
    print("\n" + "="*60)
    print("🚀 OpenFX Volatility Monitoring Engine Started")
    print("="*60)
    print(f"Monitoring: {len(top_5_pairs)} currency pairs")
    print(f"Update interval: 60 seconds")
    print(f"Alert threshold: ±{alert_threshold}%")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    # Continuous monitoring loop
    cycle = 0  # Counter for how many times we've checked
    
    try:
        while True:  # Run forever until user stops with Ctrl+C
            cycle += 1  # Increment cycle counter
            
            # Print status header
            print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            # Check each currency pair
            results = []
            for pair in top_5_pairs:
                status = monitor_pair(pair, threshold=alert_threshold)
                if status:  # If we got data
                    results.append(status)
                    # Print quick status (non-alert)
                    if not status['alerted']:
                        pair_name = pair.replace("=X", "")
                        print(f"✓ {pair_name}: ${status['price']:.5f} ({status['change']:+.2f}%)")
            
            # Print summary
            alerts_count = sum(1 for r in results if r['alerted'])
            print(f"\nStatus: {len(results)}/{len(top_5_pairs)} pairs checked | {alerts_count} alerts")
            
            # Wait 60 seconds before next check
            print(f"Next update in 60 seconds...\n")
            time.sleep(60)  # Pause for 60 seconds
            
    except KeyboardInterrupt:
        # User pressed Ctrl+C to stop
        print("\n\n" + "="*60)
        print("🛑 Monitoring stopped by user")
        print(f"Total cycles completed: {cycle}")
        print("="*60 + "\n")

# -------------------------------
# Run the engine
# -------------------------------
if __name__ == "__main__":
    main()  # Start the monitoring engine
