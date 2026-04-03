import yfinance as yf
import pandas as pd
import numpy as np

def prepare_4y_daily_data():
    print("Downloading 4 years of daily BTC-USD and ETH-USD data...")
    # Daily data allows us to go back many years easily
    period = "4y"
    interval = "1d"
    
    btc = yf.download("BTC-USD", period=period, interval=interval)
    eth = yf.download("ETH-USD", period=period, interval=interval)
    
    # Extract Close prices
    if isinstance(btc.columns, pd.MultiIndex):
        btc_close = btc['Close']['BTC-USD']
        eth_close = eth['Close']['ETH-USD']
    else:
        btc_close = btc['Close']
        eth_close = eth['Close']

    df = pd.DataFrame({
        'btc': btc_close,
        'eth': eth_close
    }).dropna()
    
    df['spread'] = df['eth'] / df['btc']
    
    output_file = "test_data_4y_daily.csv"
    df.to_csv(output_file)
    print(f"4-year test data saved to {output_file} ({len(df)} rows).")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

if __name__ == "__main__":
    prepare_4y_daily_data()
