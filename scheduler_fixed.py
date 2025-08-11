#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Onsen Scraper Scheduler for Railway
Clean version to minimize red lines in logs
"""

import sys
import os
import time
import subprocess
import json
from datetime import datetime

# Try to import schedule, install if missing
try:
    import schedule
except ImportError:
    print("Installing schedule module...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
    import schedule

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Simple print function to avoid red lines
def log(message):
    """Simple logging that avoids stderr"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)

def save_run_history(status, records_count=0, slots_count=0, error=None):
    """Save scraping history for monitoring"""
    history = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "records_scraped": records_count,
        "slots_found": slots_count,
        "environment": "railway",
        "error": str(error) if error else None
    }
    
    try:
        # Read existing history
        history_file = './scrape_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                all_history = json.load(f)
        else:
            all_history = []
        
        # Add new entry
        all_history.append(history)
        
        # Keep only last 100 entries
        all_history = all_history[-100:]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(all_history, f, indent=2)
        
        # Also save last scrape info
        with open('./last_scrape.json', 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        log(f"Note: Could not save history: {e}")

def run_scraper():
    """Run the scraper and log results"""
    log("="*60)
    log("Starting scheduled scrape")
    log("="*60)
    
    try:
        # Run the scraper with cleaned output
        process = subprocess.Popen(
            [sys.executable, "onsen_scraper_v4.py", "--production"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Track summary info
        slots_found = 0
        records_count = 0
        
        # Process output line by line
        for line in process.stdout:
            if not line:
                continue
                
            line = line.strip()
            
            # Skip empty lines and warnings
            if not line or any(skip in line.lower() for skip in [
                'deprecationwarning',
                'warning:',
                '/usr/local/lib',
                'site-packages',
                'selenium',
                'urllib3'
            ]):
                continue
            
            # Extract useful info
            if "slots" in line and ":" in line:
                try:
                    import re
                    match = re.search(r'(\d+) slots', line)
                    if match:
                        slots_found += int(match.group(1))
                except:
                    pass
            
            if "records appended" in line:
                try:
                    import re
                    match = re.search(r'(\d+) total records appended', line)
                    if match:
                        records_count = int(match.group(1))
                except:
                    pass
            
            # Clean and print the line
            # Remove emojis and special characters that might cause issues
            clean_line = line.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARN]')
            clean_line = clean_line.replace('🔍', '>').replace('📅', '>').replace('🎯', '>')
            clean_line = clean_line.replace('📊', '[SUMMARY]').replace('📈', '[DATA]')
            clean_line = clean_line.replace('🚀', '[START]').replace('🔚', '[END]')
            clean_line = clean_line.replace('💾', '[SAVE]').replace('📤', '[UPLOAD]')
            clean_line = clean_line.replace('🌸', '[SPRING]').replace('❄️', '[WINTER]')
            
            log(clean_line)
        
        # Wait for process to complete
        process.wait(timeout=600)
        
        # Log summary
        log("="*60)
        log("Scrape Summary:")
        log(f"  Status: {'Success' if process.returncode == 0 else 'Completed with issues'}")
        log(f"  Total slots found: {slots_found}")
        log(f"  Historical records added: {records_count}")
        log("="*60)
        
        # Save history
        if process.returncode == 0:
            save_run_history("success", records_count, slots_found)
        else:
            save_run_history("completed_with_warnings", records_count, slots_found)
            
    except subprocess.TimeoutExpired:
        log("Scraper timed out after 10 minutes")
        save_run_history("timeout", 0, 0, "Process timed out")
        if 'process' in locals():
            process.kill()
    except Exception as e:
        log(f"Scraper exception: {str(e)}")
        save_run_history("error", 0, 0, str(e))

def health_check():
    """Simple health check"""
    try:
        if os.path.exists('./last_scrape.json'):
            with open('./last_scrape.json', 'r') as f:
                last_scrape = json.load(f)
                last_time = datetime.fromisoformat(last_scrape['timestamp'])
                hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                
                if hours_ago > 5:
                    log(f"Health Check: No successful scrape in {hours_ago:.1f} hours")
    except:
        pass  # Silent fail for health check

def initialize():
    """Initialize the scheduler"""
    log("Onsen Scraper Scheduler Starting...")
    log(f"Environment: Railway")
    log(f"Current time: {datetime.now()}")
    log(f"Python version: {sys.version}")
    
    # Check for required files
    required_files = [
        'onsen_scraper_v4.py',
        'sheets_writer.py',
        'onsen-scraping-fefa44f03c43.json'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            log(f"Found: {file}")
        else:
            log(f"Missing: {file}")
    
    # Schedule jobs
    schedule.every(2).hours.do(run_scraper)
    
    # Specific times
    # schedule.every().day.at("08:00").do(run_scraper)
    # schedule.every().day.at("12:00").do(run_scraper)
    # schedule.every().day.at("16:00").do(run_scraper)
    # schedule.every().day.at("20:00").do(run_scraper)
    
    # New cronjob timings
    schedule.every().day.at("07:35").do(run_scraper)
    schedule.every().day.at("09:35").do(run_scraper)
    schedule.every().day.at("11:35").do(run_scraper)
    schedule.every().day.at("13:35").do(run_scraper)
    schedule.every().day.at("15:35").do(run_scraper)
    schedule.every().day.at("17:35").do(run_scraper)
    schedule.every().day.at("19:35").do(run_scraper)
    schedule.every().day.at("21:35").do(run_scraper)
    
    # Health check every 30 minutes
    schedule.every(30).minutes.do(health_check)
    
    log("Scheduled runs:")
    log("- Every 2 hours")
    # log("- Daily at: 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM")
    log("- Daily at: 7:35 AM, 9:35 AM, 11:35 AM, 1:35 PM, 3:35 PM, 5:35 PM, 7:35 PM, 9:35 PM")
    log("- Health check every 30 minutes")
    
    # Run immediately on start
    log("Running initial scrape on startup...")
    run_scraper()

def main():
    """Main scheduler loop"""
    try:
        initialize()
        
        log("Scheduler running...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except KeyboardInterrupt:
        log("Scheduler stopped by user")
    except Exception as e:
        log(f"Scheduler error: {str(e)}")
        save_run_history("scheduler_error", 0, 0, str(e))
        # Re-raise to see full error in logs
        raise

if __name__ == "__main__":
    main()
