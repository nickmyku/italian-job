# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:3000"
backlog = 2048

# Worker processes
# Option 1: Use 1 worker (scheduler runs in the web worker)
workers = 1  # Set to 1 if running scheduler in app.py
# Option 2: Use multiple workers (requires running worker.py separately)
# workers = multiprocessing.cpu_count() * 2 + 1  # Uncomment for multi-worker setup
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "ship-tracker"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if needed)
# keyfile = None
# certfile = None
