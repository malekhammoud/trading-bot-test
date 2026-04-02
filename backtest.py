import pandas as pd
import numpy as np

def run_backtest():
    try:
        df = pd.read_csv("train_data.csv", index_col=0, parse_dates=True)
    except FileNotFoundError:
        print("Error: train_data.csv not found.")
        return

    # Hyperparameters optimized for maximizing fitness (focus on DD reduction & signal quality)
    LOOKBACK = 48
    ENTRY_TH = 3.0
    EXIT_TH = 0.5
    POS_SCALE = 0.18  # Conservative sizing heavily protects against DD penalty

    # Feature Engineering
    df['ma'] = df['spread'].rolling(LOOKBACK, min_periods=LOOKBACK).mean()
    df['std'] = df['spread'].rolling(LOOKBACK, min_periods=LOOKBACK).std().clip(lower=1e-6)
    df['z'] = (df['spread'] - df['ma']) / df['std']
    
    # Validity mask ensures we only trade after warmup when Z-score is stable
    valid_mask = df['z'].notna()

    # Signal Generation
    entry_long = (df['z'] < -ENTRY_TH) & valid_mask
    entry_short = (df['z'] > ENTRY_TH) & valid_mask
    exit_any = (df['z'].abs() < EXIT_TH) | ~valid_mask

    # Fully Vectorized State Machine
    events = pd.Series(0.0, index=df.index, dtype=float)
    events[entry_long] = 1.0
    events[entry_short] = -1.0
    events[exit_any] = 0.0
    
    blocks = exit_any.cumsum()
    df['pos'] = events.replace(0.0, np.nan).groupby(blocks).ffill().fillna(0.0) * POS_SCALE
    
    # Returns & Transaction Costs
    df['ret_spread'] = df['spread'].pct_change().fillna(0.0)
    
    # Lag position by 1 period to avoid look-ahead bias
    df['strat_ret'] = df['pos'].shift(1) * df['ret_spread']
    
    df['turnover'] = df['pos'].diff().abs().fillna(0.0)
    df['fees'] = df['turnover'] * 0.001 
    df['net_ret'] = df['strat_ret'] - df['fees']
    
    # Performance Metrics
    total_return = (1 + df['net_ret']).prod() - 1.0
    
    hourly_std = df['net_ret'].std()
    sharpe_ratio = (df['net_ret'].mean() / hourly_std) * np.sqrt(8760) if hourly_std > 1e-9 else 0.0
    
    cum_ret = (1 + df['net_ret']).cumprod()
    drawdowns = (cum_ret / cum_ret.cummax()) - 1.0
    max_drawdown = abs(drawdowns.min())
    
    # Fitness Score Calculation
    fitness_score = total_return + (sharpe_ratio / 10.0) - (max_drawdown * 2.0)
    if total_return > 0 and sharpe_ratio > 0:
        fitness_score += (total_return * sharpe_ratio)
        
    print(f"Total Return: {total_return:.4f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"Max Drawdown: {max_drawdown:.4f}")
    print(f"Fitness Score: {fitness_score:.6f}")

if __name__ == "__main__":
    run_backtest()