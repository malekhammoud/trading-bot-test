import pandas as pd
import numpy as np

def run_backtest():
    try:
        df = pd.read_csv("train_data.csv", index_col=0, parse_dates=True)
    except FileNotFoundError:
        print("Error: train_data.csv not found.")
        return

    s = df['spread'].astype(float)
    
    # 1. Adaptive Mean & Volatility
    lookback = 96
    roll_mu = s.rolling(lookback, min_periods=12).mean()
    roll_std = s.rolling(lookback, min_periods=12).std().clip(1e-8)
    z = (s - roll_mu) / roll_std
    
    # 2. Regime & Quality Filters
    # Structural support: price above long-term rolling median (filters bear regimes)
    regime_ok = s > s.rolling(240, min_periods=40).median()
    # Volatility regime filter: avoid trading during extreme panic/spike expansions
    vol_stable = roll_std < roll_std.rolling(48).mean() * 1.4
    
    # 3. Signal Logic (Asymmetric & Momentum-Confirmed)
    # Entry: Deep oversold + immediate z-score recovery (bounce confirmation) + filters
    dip = z < -1.8
    momentum_turn = z > z.shift(1)  # Derivative of z is positive = falling has stalled/reversing
    entry_sig = dip & momentum_turn & regime_ok & vol_stable
    
    # Exit: Capture full mean reversion OR enforce strict drawdown control
    take_profit = z > 0.2          # Overshoot target to maximize TR once risk is cleared
    hard_stop = z < -2.6           # Structural breakdown prevention (attacks -2*DD penalty)
    exit_sig = take_profit | hard_stop
    
    # 4. Vectorized Position Construction
    sig = pd.Series(np.nan, index=df.index)
    sig[entry_sig & ~exit_sig] = 1.0  # Enter long
    sig[exit_sig] = 0.0               # Force flat (overrides entry if concurrent)
    df['pos'] = sig.ffill().fillna(0.0).clip(0.0, 1.0)
    
    # 5. PnL & Risk Accounting
    ret_spread = s.pct_change().fillna(0.0)
    pos_lag = df['pos'].shift(1).fillna(0.0)
    
    turnover = df['pos'].diff().abs().fillna(0.0)
    fees = turnover * 0.001  # 10bps slippage/commission
    net_ret = (pos_lag * ret_spread) - fees
    
    # 6. Performance Metrics
    equity = (1 + net_ret).cumprod()
    total_return = equity.iloc[-1] - 1.0
    
    ret_std = net_ret.std()
    sharpe = (net_ret.mean() / ret_std) * np.sqrt(8760) if ret_std > 1e-9 else 0.0
    
    peak = equity.cummax()
    drawdowns = (equity / peak) - 1.0
    max_drawdown = abs(drawdowns.min())
    
    # Fitness Optimization Target
    fitness = total_return + (sharpe / 10.0) - (max_drawdown * 2.0)
    if total_return > 0 and sharpe > 0:
        fitness += (total_return * sharpe)
        
    print(f"Total Return: {total_return:.4f}")
    print(f"Sharpe Ratio: {sharpe:.4f}")
    print(f"Max Drawdown: {max_drawdown:.4f}")
    print(f"Fitness Score: {fitness:.6f}")

if __name__ == "__main__":
    run_backtest()