# 🤖 Autonomous Crypto StatArb Researcher

An automated research loop for cryptocurrency statistical arbitrage, inspired by Andrej Karpathy's `autoresearch` architecture. This system iteratively writes, backtests, and optimizes Python trading strategies using Large Language Models (LLMs) via OpenRouter.

## 🏗 Architecture

The system consists of four core components:

1.  **`prepare.py`**: Handles data acquisition. Downloads 2 years of 1-hour OHLCV data for BTC-USD and ETH-USD using `yfinance`, calculates the ETH/BTC spread, and splits data into In-Sample (70%) and Out-of-Sample (30%) sets.
2.  **`backtest.py`**: The "Target File." This contains the vectorized trading logic. It is the **only** file the agent modifies. It calculates Total Return, Sharpe Ratio, Max Drawdown, and a custom **Fitness Score**.
3.  **`agent_loop.py`**: The "Researcher." This script manages the Auto-Research cycle. It reads the current strategy, sends results to an LLM, receives improvements, executes the new code, and either accepts the change or reverts based on the Fitness Score.
4.  **`program.md`**: The "Core Directive." Contains high-level instructions, constraints (vectorization only!), and experimentation ideas for the AI agent.

## 🚀 Features

- **Autonomous Optimization**: Runs for 100+ iterations to find alpha in the ETH/BTC spread.
- **Vectorized Backtesting**: Uses `pandas` and `numpy` for high-speed performance evaluation.
- **LLM Integration**: Utilizes OpenRouter (defaulting to `qwen-3.6-plus-preview`) for state-of-the-art coding logic.
- **Resilience**: Features exponential backoff for API quota limits and continuous logging of research progress.
- **Auto-Revert**: If a proposed strategy crashes or performs worse, the system automatically reverts to the previous "Best" version.

## 🛠 Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd trading-bot-test
    ```

2.  **Create Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Prepare Data**:
    ```bash
    python prepare.py
    ```

4.  **Run Research Loop**:
    ```bash
    export OPENROUTER_API_KEY='your_api_key'
    python agent_loop.py
    ```

## 📊 Performance Metric
The agent optimizes for a **Continuous Fitness Score**:
`Fitness = Total Return + (Sharpe / 10) - (MaxDD * 2)`
This allows the agent to recognize incremental improvements even while the strategy is still in negative territory.

## ⚠️ Disclaimer
This project is for educational and research purposes only. Trading cryptocurrencies involves significant risk. Never trade with money you cannot afford to lose.
