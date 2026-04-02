import os
import subprocess
import time
from openai import OpenAI

# API Key configuration
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY environment variable.")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API_KEY,
)

MODEL_ID = "qwen/qwen-3.6-plus:free"

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

def main():
    best_score = -999.0
    best_code = read_code()
    
    # Context Management: Keep only the last 5 failed attempts to prevent bloat
    failure_log = [] 
    
    print(f"Starting 100-Iteration Deep Research Loop ({MODEL_ID})...")
    
    # Initial run
    output, best_score = run_backtest()
    print(f"Baseline Score: {best_score}")
    
    iteration = 1
    while iteration <= 100:
        print(f"\n--- Iteration {iteration} ---")
        
        # Build the condensed history string
        history_context = "\n".join(failure_log[-5:]) if failure_log else "No recent failures."
        
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
                # Fallback if the LLM ignores formatting
                summary = "Code mutation attempted."
                new_code = raw_text.replace("```python", "").replace("```", "").strip()
            
            save_code(new_code)
            new_output, new_score = run_backtest()
            
            print(f"Change: {summary}")
            print(f"New Score: {new_score}")
            
            if new_score > best_score:
                print(f"SUCCESS: New Best Score: {new_score}")
                best_score = new_score
                best_code = new_code
                # On success, we can clear the failure log as the baseline has shifted
                failure_log = [] 
            else:
                print("REJECTED: Reverting.")
                failure_log.append(f"- Tried: {summary} (Score: {new_score})")
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
