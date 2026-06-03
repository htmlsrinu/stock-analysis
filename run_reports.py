import subprocess
import os
import sys
import json
from datetime import datetime

# Script Directory
CWD = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(CWD, "scheduler_history.log")
CREDENTIALS_FILE = os.path.join(CWD, "credentials.json")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + "\n")

def run_command(command, description):
    log(f"Starting: {description}...")
    try:
        # Run python script using same interpreter
        result = subprocess.run(
            [sys.executable] + command,
            cwd=CWD,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log(f"SUCCESS: {description}")
            return True
        else:
            log(f"ERROR: {description} (Exit Code: {result.returncode})")
            log(f"Error details:\n{result.stderr}")
            return False
    except Exception as e:
        log(f"FATAL ERROR executing {description}: {e}")
        return False

def git_push_updates():
    log("Starting: Pushing updated data to GitHub repository...")
    try:
        if not os.path.exists(os.path.join(CWD, ".git")):
            log("INFO: Git repository not initialized. Skipping Git push.")
            return False

        # Pull first to resolve any remote conflicts automatically
        subprocess.run(["git", "pull", "origin", "main", "--rebase"], cwd=CWD, check=True)

        # Add data files to staging
        subprocess.run(["git", "add", "data.js", "data_quantum.js", "performance.js"], cwd=CWD, check=True)
        
        # Check if there are changes to commit
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=CWD, capture_output=True, text=True)
        if not status_res.stdout.strip():
            log("INFO: No new data changes to commit.")
            return True

        # Commit changes
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"Auto-update stock analysis data - {timestamp}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=CWD, check=True)
        
        # Push to remote repository
        push_res = subprocess.run(["git", "push"], cwd=CWD, capture_output=True, text=True)
        if push_res.returncode == 0:
            log("SUCCESS: Pushed data updates to GitHub Pages remote.")
            return True
        else:
            log(f"WARNING: Git push failed. remote might not be set up yet or needs authentication. Details:\n{push_res.stderr}")
            return False
    except Exception as e:
        log(f"WARNING: Failed to push updates to Git: {e}")
        return False

def main():
    log("==================================================")
    log("      CONSENUS ENGINE REPORT SCHEDULER ACTIVE     ")
    log("==================================================")
    
    # Load SMTP credentials from credentials.json
    sender = "DadiShekar@gmail.com"
    password = "tfhuczdxuuumcdec" # Fallbacks
    
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                sender = creds.get("email_sender", sender)
                password = creds.get("email_password", password)
            log("SUCCESS: Loaded SMTP credentials from credentials.json")
        except Exception as e:
            log(f"WARNING: Failed to parse credentials.json ({e}). Using hardcoded fallbacks.")
    else:
        log("INFO: credentials.json not found. Using local fallbacks.")

    # 1. Recalculate Space Stocks
    run_command(["analyze.py"], "Space Stock Scraper (analyze.py)")
    
    # 2. Recalculate Quantum Stocks
    run_command(["analyze_quantum.py"], "Quantum Stock Scraper (analyze_quantum.py)")
    
    # 3. Recalculate Performance Metrics & Backtests
    run_command(["backtest.py"], "Performance Audit Simulator (backtest.py)")
    
    # 4. Dispatch Space Technical Report Email
    run_command(["send_email.py", "--sender", sender, "--password", password], "Space Email Dispatcher (send_email.py)")
    
    # 5. Dispatch Quantum Technical Report Email
    run_command(["send_email_quantum.py", "--sender", sender, "--password", password], "Quantum Email Dispatcher (send_email_quantum.py)")
    
    # 6. Dispatch Apex Shorts Report Email
    run_command(["send_email_shorts.py", "--sender", sender, "--password", password], "Apex Shorts Email Dispatcher (send_email_shorts.py)")
    
    # 7. Push newly updated data files to GitHub Pages
    git_push_updates()
    
    log("==================================================")
    log("      ALL SCHEDULED REPORTS COMPLETED & SENT       ")
    log("==================================================")

if __name__ == '__main__':
    main()
