# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:3000"
backlog = 2048

# SSL/TLS Configuration (HTTPS)
# Set these environment variables to enable HTTPS:
# SSL_CERTFILE: Path to SSL certificate file (e.g., /path/to/cert.pem)
# SSL_KEYFILE: Path to SSL private key file (e.g., /path/to/key.pem)
# SSL_PORT: Port to bind HTTPS server (default: 3000)
# If SSL_CERTFILE and SSL_KEYFILE are set, HTTPS will be enabled
ssl_certfile = os.environ.get('SSL_CERTFILE')
ssl_keyfile = os.environ.get('SSL_KEYFILE')
ssl_port = int(os.environ.get('SSL_PORT', '3000'))

# If SSL certificates are provided, configure HTTPS
if ssl_certfile and ssl_keyfile:
    bind = f"0.0.0.0:{ssl_port}"
    keyfile = ssl_keyfile
    certfile = ssl_certfile

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ship_tracker"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app to ensure scheduler starts only once in master process
# This prevents multiple scheduler instances when using multiple workers
preload_app = True

# Graceful timeout for worker restarts
graceful_timeout = 30
