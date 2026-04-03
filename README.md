# Crypto StatArb Autonomous Researcher

A fully autonomous research agent for crypto statistical arbitrage, modeled after the `autoresearch` architecture. This system iteratively writes, backtests, and optimizes Shariah-compliant (Long-Only) trading strategies.

## 🚀 Quick Start for Server Deployment

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your server.

### 2. Setup Environment
```bash
# Clone the repository
git clone <your-repo-url>
cd trading-bot-test

# Create virtual environment and install dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 3. Prepare Data
Download 2 years of 1-hour OHLCV data for BTC/ETH:
```bash
./venv/bin/python3 prepare.py
```

### 4. Run the Research Loop
Set your OpenRouter API key and start the 100-iteration optimization:
```bash
export OPENROUTER_API_KEY='your_api_key'
nohup ./venv/bin/python3 agent_loop.py &
```
The `nohup` command ensures the loop continues running even if you disconnect from the server.

## 📊 Live Test Simulation

The `livetest.py` script converts the optimized `backtest2.py` strategy into a real-time monitor that fetches live data from Yahoo Finance and simulates trading in current market conditions.

### 1. Features
- **Real-Time Data**: Uses `yfinance` to monitor BTC and ETH hourly.
- **Simulated Execution**: No actual trading is performed; it's a "paper trade" simulation.
- **Realistic Constraints**: Includes 0.05% slippage on every trade to model market impact.
- **Persistence**: Logs all signals, actions, and equity to `live_log.csv`. Resumes automatically if restarted.

### 2. How to Run
Once you have an optimized strategy in `backtest2.py`:
```bash
./venv/bin/python3 livetest.py
```
To run it in the background on a server:
```bash
nohup ./venv/bin/python3 livetest.py > live_output.log 2>&1 &
```

### 3. Monitoring Results
You can monitor the live feed by watching the log file:
```bash
tail -f live_log.csv
```
The CSV tracks timestamp, BTC/ETH prices, spread, current position size, Z-score, and cumulative equity.

## 📁 File Structure
- `agent_loop.py`: The "Researcher" (Orchestrates the LLM and optimization).
- `backtest.py` / `backtest2.py`: The "Strategy" (Backtesting logic and latest optimized results).
- `livetest.py`: Real-time simulation and market monitoring.
- `prepare.py`: Data utility for downloading/aligning BTC-ETH spreads.
- `program.md`: The "Directive" (Rules and constraints for the AI).
- `train_data.csv` / `val_data.csv`: Historical data (70/30 split).

## ⚖️ Shariah Compliance
This system is strictly configured for **Long-Only** spot strategies. Short selling and borrowing are forbidden via the `program.md` directive and baseline code structure.

## 📈 Monitoring
You can monitor the progress by tailing the logs if you use redirection:
```bash
tail -f nohup.out
```
Once the loop is finished, the best-performing code will be stored in `backtest.py`.
