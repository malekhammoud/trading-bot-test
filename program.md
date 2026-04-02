# Core Directive: Autonomous Crypto Researcher

## Objective
Your goal is to maximize the **Fitness Score** of the crypto statistical arbitrage strategy in `backtest.py`.

## Optimization Target
**Fitness Score** = `Total Return + (Sharpe Ratio / 10.0) - (Max Drawdown * 2.0)`
(If Total Return and Sharpe are positive, a multiplier bonus is applied). 
Higher is ALWAYS better. Optimize your strategy to climb out of negative scores into positive ones.

## Constraints
1.  **LONG ONLY:** Strictly no short selling. The strategy must only enter 'Long' positions (position = 1) or stay 'Flat' (position = 0). Selling an asset you do not own is forbidden.
2.  **Vectorization:** All calculations MUST be vectorized using Pandas or NumPy. Do not use `for` loops.
2.  **Dependencies:** Use only `pandas`, `numpy`, and `scipy`.
3.  **Output:** The script must always print the four required metrics at the end:
    *   Total Return
    *   Sharpe Ratio
    *   Max Drawdown
    *   Fitness Score (formatted as `Fitness Score: <value>`)
4.  **Data:** The script loads `train_data.csv` which contains `btc`, `eth`, and `spread` (ETH/BTC ratio).

## Experimentation Ideas
*   **Signal Engineering:** 
    *   Use RSI, Bollinger Bands, or MACD on the ETH/BTC spread.
    *   Incorporate Volume-Weighted Average Price (VWAP) if available.
    *   Apply Kalman Filters or Hurst Exponent to measure mean reversion strength.
*   **Risk Management:**
    *   Dynamic stop-losses based on Volatility (ATR).
    *   Take-profit levels relative to z-score mean crossing.
    *   Position sizing based on signal conviction.
*   **Hyperparameter Tuning:**
    *   Optimize lookback windows for moving averages and standard deviations.
    *   Adjust entry/exit z-score thresholds.

Avoid overfitting by ensuring that the logic is statistically sound and not just capturing noise in the training set.
