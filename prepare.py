import yfinance as yf
import pandas as pd
import numpy as np
import os

def download_data():
    print("Downloading BTC-USD and ETH-USD data...")
    # Fetch data
    btc = yf.download("BTC-USD", period="2y", interval="1h")
    eth = yf.download("ETH-USD", period="2y", interval="1h")
    
    # Handle MultiIndex if present (yfinance >= 0.2.40)
    if isinstance(btc.columns, pd.MultiIndex):
        btc_close = btc['Close']['BTC-USD']
        eth_close = eth['Close']['ETH-USD']
    else:
        btc_close = btc['Close']
        eth_close = eth['Close']

    # Align and calculate spread
    df = pd.DataFrame({
        'btc': btc_close,
        'eth': eth_close
    }).dropna()
    
    df['spread'] = df['eth'] / df['btc']
    
    # Chronological split: 70% train, 30% validation
    split_idx = int(len(df) * 0.7)
    train_data = df.iloc[:split_idx]
    val_data = df.iloc[split_idx:]
    
    train_data.to_csv("train_data.csv")
    val_data.to_csv("val_data.csv")
    print(f"Data prepared: {len(train_data)} train rows, {len(val_data)} val rows.")

def load_data(filename="train_data.csv"):
    return pd.read_csv(filename, index_col=0, parse_dates=True)

if __name__ == "__main__":
    download_data()
