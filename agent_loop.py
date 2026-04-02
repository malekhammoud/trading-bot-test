import os
import subprocess
import time
from datetime import datetime
from openai import OpenAI

# API Key configuration
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY environment variable.")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API_KEY,
)

MODEL_ID = "qwen/qwen3.6-plus-preview:free"
RESEARCH_LOG_FILE = "research_log.md"

# Strategy directive
with open("program.md", "r") as f:
    DIRECTIVE = f.read()

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

def append_to_research_log(iteration, summary, score, decision):
    """Appends a single research entry to the permanent log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"### Iteration {iteration} ({timestamp})\n"
    log_entry += f"- **Summary:** {summary}\n"
    log_entry += f"- **Score:** {score}\n"
    log_entry += f"- **Decision:** {decision}\n\n"
    
    with open(RESEARCH_LOG_FILE, "a") as f:
        f.write(log_entry)

def get_recent_failures_from_log(limit=5):
    """Reads the permanent log to find the most recent failed attempts for context."""
    if not os.path.exists(RESEARCH_LOG_FILE):
        return "No prior research history."
    
    failures = []
    with open(RESEARCH_LOG_FILE, "r") as f:
        lines = f.readlines()
        
    # We'll work backwards from the end of the file
    current_summary = ""
    for line in reversed(lines):
        if "- **Decision:** REJECTED" in line:
            # The summary is on the line above it (Score is between them)
            # Find the summary for this rejection
            pass # We'll need a better parser if we want to be exact
            
    # Simpler: just get the last few REJECTED lines for now
    recent_rejections = [line for line in lines if "- **Summary:**" in line or "- **Decision:** REJECTED" in line]
    # To keep context lean, we'll just extract the summaries of the last 5 rejections
    # (Actually, let's keep it simple: the in-memory failure_log is fine for the session,
    # and the file is for permanent human review.)
    return "\n".join(recent_rejections[-10:]) # Summaries + Decisions

def main():
    best_score = -999.0
    best_code = read_code()
    
    # Session memory (clears on success)
    session_failure_log = [] 
    
    print(f"Starting 100-Iteration Deep Research Loop ({MODEL_ID})...")
    if not os.path.exists(RESEARCH_LOG_FILE):
        with open(RESEARCH_LOG_FILE, "w") as f:
            f.write("# Research Log: Autonomous Crypto StatArb\n\n")
    
    # Initial run
    output, best_score = run_backtest()
    print(f"Baseline Score: {best_score}")
    
    iteration = 1
    while iteration <= 100:
        print(f"\n--- Iteration {iteration} ---")
        
        # Build the condensed history string from session failures
        history_context = "\n".join(session_failure_log[-5:]) if session_failure_log else "No recent failures in this session."
        
        prompt = f"""
        {DIRECTIVE}
        
        Current Best Score: {best_score}
        Current Best Code:
        ```python
        {best_code}
        ```
        
        Recent Failed Attempts (Avoid these):
        {history_context}
        
        Instruction: Improve the Fitness Score. 
        Format your response as:
        SUMMARY: [One sentence explaining the logical change]
        CODE:
        ```python
        [Full Code]
        ```
        """
        
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a quantitative researcher. Be concise. Focus on logic, not just parameters."},
                    {"role": "user", "content": prompt}
                ],
                extra_headers={"HTTP-Referer": "https://github.com/karpathy/autoresearch-python", "X-Title": "Crypto Researcher"}
            )
            
            raw_text = response.choices[0].message.content
            
            # Parse Summary and Code
            try:
                summary = raw_text.split("SUMMARY:")[1].split("CODE:")[0].strip()
                new_code = raw_text.split("```python")[1].split("```")[0].strip()
            except:
                summary = "Code mutation attempted."
                new_code = raw_text.replace("```python", "").replace("```", "").strip()
            
            save_code(new_code)
            new_output, new_score = run_backtest()
            
            print(f"Change: {summary}")
            print(f"New Score: {new_score}")
            
            if new_score > best_score:
                print(f"SUCCESS: New Best Score: {new_score}")
                append_to_research_log(iteration, summary, new_score, "SUCCESS")
                best_score = new_score
                best_code = new_code
                session_failure_log = [] 
            else:
                print("REJECTED: Reverting.")
                append_to_research_log(iteration, summary, new_score, "REJECTED")
                session_failure_log.append(f"- Tried: {summary} (Score: {new_score})")
                save_code(best_code)
            
            iteration += 1
            time.sleep(2) 
            
        except Exception as e:
            print(f"Error: {e}")
            save_code(best_code)
            iteration += 1
            time.sleep(5)

if __name__ == "__main__":
    main()
