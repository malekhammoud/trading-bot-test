import pandas as pd
import numpy as np

def run_backtest(file_name="train_data.csv"):
    try:
        df = pd.read_csv(file_name, index_col=0, parse_dates=True)
    except FileNotFoundError:
        print(f"Error: {file_name} not found.")
        return

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
    # Stricter: Price > Macro AND Macro Slope > 0 AND Price > Med
    regime_ok = (s > ema_macro) & (slope_macro > 0) & (s > ema_120) & (slope_med > 0)
    
    # --- Signal Logic ---
    entry_long = regime_ok & (z_30 > 1.25)
    # Exit if regime decays or Z-score reverts
    exit_long = (~regime_ok) | (z_30 < 0.25)
    
    sig = pd.Series(np.nan, index=df.index)
    sig.loc[entry_long] = 1.0
    sig.loc[exit_long] = 0.0
    sig.iloc[0] = 0.0
    pos_base = sig.ffill().fillna(0.0)
    
    # --- "Rich but Safe" Position Sizing ---
    # Multiplier up to 4x based on slope
    slope_factor = (1.0 + slope_med.clip(0, 0.02) * 150.0)
    # Z-Score Confidence
    z_factor = (1.0 + (z_30.clip(1.25, 2.5) - 1.25) * 2.0)
    
    pos = pos_base * slope_factor * z_factor
    
    # --- Returns & Costs ---
    ret_spread = s.pct_change().fillna(0.0)
    pos_lag = pos.shift(1).fillna(0.0)
    turnover_lag = pos.diff().abs().shift(1).fillna(0.0)
    slippage_costs = turnover_lag * 0.0005 
    net_ret = (pos_lag * ret_spread) - slippage_costs
    equity = (1 + net_ret).cumprod()
    
    # --- Metrics ---
    total_return = equity.iloc[-1] - 1.0
    std_ret = net_ret.std()
    sharpe_ratio = (net_ret.mean() / std_ret * np.sqrt(8760)) if std_ret > 0 else 0.0
    max_drawdown = abs(((equity / equity.cummax()) - 1.0).min())
    
    fitness_score = total_return + (sharpe_ratio / 10.0) - (max_drawdown * 2.0)
    if total_return > 0 and sharpe_ratio > 0:
        fitness_score *= 2.0
        
    num_trades = (turnover_lag > 1e-6).sum()
    if num_trades == 0: fitness_score = 0.0

    print(f"--- {file_name} Results ---")
    print(f"Num Trades: {num_trades}")
    print(f"Total Return: {total_return:.4f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"Max Drawdown: {max_drawdown:.4f}")
    print(f"Fitness Score: {fitness_score:.4f}")
    print("")

if __name__ == "__main__":
    run_backtest("train_data.csv")
    run_backtest("val_data.csv")
