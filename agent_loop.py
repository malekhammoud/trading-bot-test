import os
import subprocess
import time
import json
from datetime import datetime
from openai import OpenAI

# API Key configuration
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY environment variable.")

# OpenRouter Client Setup
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API_KEY,
)

# Best Free Coding Model for 2026
MODEL_ID = "qwen/qwen3.6-plus-preview:free"
LOG_FILE = "research_log.txt"

# Strategy directive
with open("program.md", "r") as f:
    DIRECTIVE = f.read()

def log_event(message):
    """Writes a message to both stdout and the log file immediately."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    with open(LOG_FILE, "a") as f:
        f.write(formatted_msg + "\n")

def run_backtest():
    """Executes backtest.py and returns output + fitness score."""
    try:
        venv_python = os.path.join(os.getcwd(), "venv", "bin", "python3")
        result = subprocess.run([venv_python, "backtest.py"], capture_output=True, text=True, timeout=30)
        output = result.stdout
        if "Fitness Score:" in output:
            score_line = [l for l in output.split("\n") if "Fitness Score:" in l][0]
            score = float(score_line.split("Fitness Score:")[1].strip())
            return output, score
        return output, -999.0
    except Exception as e:
        return str(e), -999.0

def save_code(code):
    with open("backtest.py", "w") as f:
        f.write(code)

def read_code():
    with open("backtest.py", "r") as f:
        return f.read()

def main():
    best_score = -999.0
    best_code = read_code()
    
    log_event(f"Starting 100-run Auto-Research Loop using {MODEL_ID}...")
    
    # Run baseline first
    output, best_score = run_backtest()
    log_event(f"Baseline Score: {best_score}")
    
    iteration = 1
    error_count = 0
    
    while iteration <= 100:
        log_event(f"\n--- Iteration {iteration} ---")
        
        prompt = f"""
        {DIRECTIVE}
        
        Current backtest.py code:
        ```python
        {best_code}
        ```
        
        Previous Results:
        {output}
        
        Improve the Fitness Score while avoiding overfitting. 
        Focus on signal logic, risk management, and vectorized optimizations.
        Return ONLY the full code for backtest.py. Do not include markdown or explanations.
        """
        
        try:
            # Exponential Backoff for API Calls
            wait_time = 2 ** error_count
            if error_count > 0:
                log_event(f"Error detected. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a senior quantitative developer optimizing a crypto trading strategy."},
                    {"role": "user", "content": prompt}
                ],
                extra_headers={
                    "HTTP-Referer": "https://github.com/karpathy/autoresearch-python",
                    "X-Title": "Crypto Research Agent",
                }
            )
            
            new_code = response.choices[0].message.content
            
            # Reset error count on success
            error_count = 0
            
            # Clean up potential markdown formatting
            if "```python" in new_code:
                new_code = new_code.split("```python")[1].split("```")[0].strip()
            elif "```" in new_code:
                new_code = new_code.split("```")[1].split("```")[0].strip()
            else:
                new_code = new_code.strip()
            
            # Save and run
            save_code(new_code)
            new_output, new_score = run_backtest()
            
            log_event(f"New Score: {new_score}")
            
            if new_score > best_score:
                log_event(f"SUCCESS: Improvement found! New Best Score: {new_score}")
                best_score = new_score
                best_code = new_code
                output = new_output
                # Save a backup of the best code
                with open("backtest_best.py", "w") as f:
                    f.write(best_code)
            else:
                log_event("REJECTED: No improvement. Reverting.")
                save_code(best_code)
            
            iteration += 1
            time.sleep(2) # Normal delay
            
        except Exception as e:
            error_msg = str(e)
            log_event(f"API ERROR: {error_msg}")
            
            # If it's a quota/rate limit error, increase backoff
            if "429" in error_msg or "rate" in error_msg.lower() or "quota" in error_msg.lower():
                error_count = min(error_count + 1, 6) # Max wait ~64 seconds
            else:
                # For other errors, just log and continue
                log_event("Non-quota error. Skipping iteration.")
                iteration += 1
            
            save_code(best_code)

    log_event("Research loop complete. Best strategy saved to backtest_best.py")

if __name__ == "__main__":
    main()
