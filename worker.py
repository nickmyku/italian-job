#!/usr/bin/env python3
"""
Standalone scheduler worker process
Run this separately from Gunicorn to handle scheduled tasks
"""
from scheduler import start_scheduler
import time

if __name__ == '__main__':
    print("Starting standalone scheduler worker...")
    scheduler = start_scheduler()
    
    # Keep process alive
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down scheduler...")
