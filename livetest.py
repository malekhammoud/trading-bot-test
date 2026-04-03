import yfinance as yf
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime, timedelta

# --- Configuration ---
LOG_FILE = "live_log.csv"
INITIAL_EQUITY = 1.0
SLIPPAGE_RATE = 0.0005  # 0.05% slippage
TICKERS = ["BTC-USD", "ETH-USD"]
INTERVAL = "1h"
CHECK_INTERVAL = 60  # Check every 60 seconds if a new candle is available
WARM_UP_PERIOD = "30d" # Period to backfill on first run

def run_strategy(df):
    """Calculate indicators and signals for the entire dataframe."""
    s = df['spread'].astype(float)
    
    # --- Tactical Indicators ---
    ema_24 = s.ewm(span=24, adjust=False).mean()
    ema_120 = s.ewm(span=120, adjust=False).mean()
    ema_macro = s.ewm(span=480, adjust=False).mean()
    
    # Slopes
    slope_med = (ema_120 - ema_120.shift(24)) / (ema_120.shift(24) + 1e-9)
    slope_macro = (ema_macro - ema_macro.shift(48)) / (ema_macro.shift(48) + 1e-9)
    
    # Breakout Intensity
    sma_30, std_30 = s.rolling(30).mean(), s.rolling(30).std()
    z_30 = (s - sma_30) / (std_30 + 1e-9)
    
    # --- The "Bullet Proof" Regime ---
    regime_ok = (s > ema_macro) & (slope_macro > 0) & (s > ema_120) & (slope_med > 0)
    
    # --- Signal Logic ---
    entry_long = regime_ok & (z_30 > 1.25)
    exit_long = (~regime_ok) | (z_30 < 0.25)
    
    sig = pd.Series(np.nan, index=df.index)
    sig.loc[entry_long] = 1.0
    sig.loc[exit_long] = 0.0
    pos_base = sig.ffill().fillna(0.0)
    
    # --- Position Sizing ---
    slope_factor = (1.0 + slope_med.clip(0, 0.02) * 150.0)
    z_factor = (1.0 + (z_30.clip(1.25, 2.5) - 1.25) * 2.0)
    
    pos = pos_base * slope_factor * z_factor
    
    result = df.copy()
    result['pos'] = pos
    result['pos_base'] = pos_base
    result['regime_ok'] = regime_ok
    result['z_30'] = z_30
    return result

def backfill_log(df):
    """Run strategy on historical data and save to log."""
    print(f"Backfilling log with {WARM_UP_PERIOD} of historical data...")
    
    # We need a longer period for EMAs to stabilize, but we only log the last WARM_UP_PERIOD
    processed = run_strategy(df)
    
    # Filter for the last 30 days of data for the log
    start_ts = df.index[-1] - timedelta(days=30)
    to_log = processed[processed.index >= start_ts].copy()
    
    # Calculate performance for the logged period
    # Note: To be fully accurate we'd calculate from the very beginning of the df
    # but for warm-up, starting equity at 1.0 at start_ts is fine.
    
    to_log['net_ret'] = 0.0
    to_log['equity'] = INITIAL_EQUITY
    
    current_equity = INITIAL_EQUITY
    last_pos = 0.0
    last_spread = None
    
    log_rows = []
    for ts, row in to_log.iterrows():
        net_ret = 0.0
        if last_spread is not None:
            ret_spread = (row['spread'] / last_spread) - 1.0
            turnover = abs(row['pos'] - last_pos)
            slippage_costs = turnover * SLIPPAGE_RATE
            net_ret = (last_pos * ret_spread) - slippage_costs
            current_equity *= (1 + net_ret)
        
        log_rows.append({
            'timestamp': ts,
            'btc': row['btc'],
            'eth': row['eth'],
            'spread': row['spread'],
            'pos': row['pos'],
            'pos_base': row['pos_base'],
            'regime_ok': row['regime_ok'],
            'z_30': row['z_30'],
            'net_ret': net_ret,
            'equity': current_equity
        })
        
        last_pos = row['pos']
        last_spread = row['spread']
    
    log_df = pd.DataFrame(log_rows)
    log_df.to_csv(LOG_FILE, index=False)
    print(f"Backfilled {len(log_df)} entries to {LOG_FILE}")
    return current_equity, last_pos, last_spread, to_log.index[-1]

def main():
    print("Initializing Live Test Simulation...")
    print(f"Monitoring: {TICKERS} | Interval: {INTERVAL} | Slippage: {SLIPPAGE_RATE*100:.3f}%")
    
    # 1. Fetch initial data (60 days for stable EMAs)
    print("Fetching historical data for initialization...")
    full_df = yf.download(TICKERS, period="60d", interval=INTERVAL, progress=False)
    if isinstance(full_df.columns, pd.MultiIndex):
        btc_close = full_df['Close']['BTC-USD']
        eth_close = full_df['Close']['ETH-USD']
    else:
        btc_close = full_df['BTC-USD']
        eth_close = full_df['ETH-USD']
        
    df = pd.DataFrame({'btc': btc_close, 'eth': eth_close}).dropna()
    df['spread'] = df['eth'] / df['btc']
    
    # 2. Check for log file and resume or backfill
    if os.path.exists(LOG_FILE):
        try:
            log_df = pd.read_csv(LOG_FILE)
            if not log_df.empty:
                current_equity = log_df['equity'].iloc[-1]
                last_pos = log_df['pos'].iloc[-1]
                last_spread = log_df['spread'].iloc[-1]
                last_timestamp = pd.to_datetime(log_df['timestamp'].iloc[-1]).tz_localize('UTC') if pd.to_datetime(log_df['timestamp'].iloc[-1]).tzinfo is None else pd.to_datetime(log_df['timestamp'].iloc[-1])
                print(f"Resuming from {last_timestamp}. Current Equity: {current_equity:.4f}")
            else:
                raise ValueError("Log file empty")
        except Exception as e:
            print(f"Could not load log ({e}). Backfilling...")
            current_equity, last_pos, last_spread, last_timestamp = backfill_log(df.iloc[:-1])
    else:
        current_equity, last_pos, last_spread, last_timestamp = backfill_log(df.iloc[:-1])

    print("Entering main loop...")
    while True:
        try:
            # Refresh data
            full_df = yf.download(TICKERS, period="60d", interval=INTERVAL, progress=False)
            if isinstance(full_df.columns, pd.MultiIndex):
                btc_close = full_df['Close']['BTC-USD']
                eth_close = full_df['Close']['ETH-USD']
            else:
                btc_close = full_df['BTC-USD']
                eth_close = full_df['ETH-USD']
            
            df = pd.DataFrame({'btc': btc_close, 'eth': eth_close}).dropna()
            df['spread'] = df['eth'] / df['btc']
            
            completed_df = df.iloc[:-1]
            latest_ts = completed_df.index[-1]
            
            if latest_ts > last_timestamp:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New completed candle: {latest_ts}")
                
                # Calculate latest signal
                processed = run_strategy(completed_df)
                latest_data = processed.iloc[-1]
                
                # Calculate returns
                ret_spread = (latest_data['spread'] / last_spread) - 1.0
                turnover = abs(latest_data['pos'] - last_pos)
                slippage_costs = turnover * SLIPPAGE_RATE
                net_ret = (last_pos * ret_spread) - slippage_costs
                current_equity *= (1 + net_ret)
                
                if turnover > 0.0001:
                    print(f" ACTION: Position changed from {last_pos:.4f} to {latest_data['pos']:.4f}")
                
                # Log entry
                log_entry = f"{latest_ts},{latest_data['btc']:.2f},{latest_data['eth']:.2f},{latest_data['spread']:.6f},{latest_data['pos']:.4f},{latest_data['pos_base']:.1f},{latest_data['regime_ok']},{latest_data['z_30']:.4f},{net_ret:.6f},{current_equity:.6f}\n"
                with open(LOG_FILE, "a") as f:
                    f.write(log_entry)
                
                print(f" Spread: {latest_data['spread']:.6f} | Signal: {'LONG' if latest_data['pos_base'] > 0 else 'FLAT'} (Z: {latest_data['z_30']:.2f})")
                print(f" Net Ret: {net_ret:.6%} | Equity: {current_equity:.6f}")
                
                last_timestamp = latest_ts
                last_pos = latest_data['pos']
                last_spread = latest_data['spread']
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
