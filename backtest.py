import pandas as pd
import numpy as np

def run_backtest():
    try:
        df = pd.read_csv("train_data.csv", index_col=0, parse_dates=True)
    except FileNotFoundError:
        print("Error: train_data.csv not found.")
        return

    # 1. Feature Engineering & Signal Generation
    df['ret_spread'] = df['spread'].pct_change().fillna(0.0)
    
    # EWMA for faster adaptation to regime shifts
    span = 48
    df['ma'] = df['spread'].ewm(span=span).mean()
    df['std'] = df['spread'].ewm(span=span).std().clip(lower=1e-6)
    df['z'] = (df['spread'] - df['ma']) / df['std']
    
    # 2. Regime Filtering: Avoid mean reversion during strong trends
    # Filter out periods where short-term momentum significantly deviates from long-term baseline
    df['ma_short'] = df['spread'].rolling(20).mean()
    df['ma_long'] = df['spread'].rolling(80).mean()
    trend_dev = ((df['ma_short'] - df['ma_long']) / df['ma_long']).abs()
    valid_mask = df['z'].notna() & (trend_dev < 0.012)
    
    # 3. Signal Thresholds (Tuned for higher signal-to-noise ratio)
    ENTRY_TH = 2.2
    EXIT_TH = 0.5
    entry_long = (df['z'] < -ENTRY_TH) & valid_mask
    entry_short = (df['z'] > ENTRY_TH) & valid_mask
    exit_any = (df['z'].abs() < EXIT_TH) | ~valid_mask
    
    # 4. Fully Vectorized State Machine
    signals = pd.Series(np.nan, index=df.index, dtype=float)
    signals[entry_long] = 1.0
    signals[entry_short] = -1.0
    signals[exit_any] = 0.0
    
    # Forward fill preserves state between signals. Exits set state to 0.
    df['pos_raw'] = signals.ffill().fillna(0.0)
    
    # 5. Volatility Targeting for Drawdown Control & Sharpe Optimization
    # Scale positions inversely to realized volatility. Higher vol -> smaller size.
    df['roll_vol'] = df['ret_spread'].rolling(24).std().clip(lower=1e-6)
    # Target ~0.08% hourly volatility per unit, clipped to prevent leverage extremes
    df['vol_scale'] = (0.0008 / df['roll_vol']).shift(1).clip(0.4, 1.8)
    df['pos'] = df['pos_raw'].shift(1) * df['vol_scale']
    
    # 6. Returns & Transaction Costs
    df['gross_ret'] = df['pos'] * df['ret_spread']
    
    # Turnover is the absolute change in position size
    df['turnover'] = df['pos'].diff().abs().fillna(0.0)
    df['fees'] = df['turnover'] * 0.001 
    df['net_ret'] = df['gross_ret'] - df['fees']
    
    # 7. Performance Metrics
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