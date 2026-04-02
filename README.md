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

## 📁 File Structure
- `agent_loop.py`: The "Researcher" (Orchestrates the LLM and optimization).
- `backtest.py`: The "Strategy" (The target file modified by the agent).
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
