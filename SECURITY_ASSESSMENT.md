# Security Assessment for Ship Tracker Web Application

**Date:** 2025-11-16  
**Status:** NOT READY FOR PUBLIC INTERNET DEPLOYMENT  
**Severity:** CRITICAL ISSUES IDENTIFIED

## Executive Summary

This Flask-based ship tracking application has **multiple critical security vulnerabilities** that make it unsafe for deployment on the public internet in its current state. The application requires significant security hardening before it can be safely exposed to external users.

---

## Critical Security Issues (MUST FIX)

### 1. Debug Mode Enabled in Production ⚠️ CRITICAL
**File:** `app.py` line 167  
**Issue:** `debug=True` is enabled in production

```python
app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
```

**Risk:**
- Exposes detailed stack traces to attackers
- Allows arbitrary code execution via Werkzeug debugger
- Reveals application structure, file paths, and source code
- Provides interactive Python shell to attackers

**Recommendation:**
```python
# Use environment variable to control debug mode
import os
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.run(host='0.0.0.0', port=3000, debug=DEBUG, use_reloader=False)
```

**Priority:** CRITICAL - Fix immediately

---

### 2. No Authentication or Authorization ⚠️ CRITICAL
**Files:** All API endpoints in `app.py`  
**Issue:** All endpoints are publicly accessible without any authentication

**Vulnerable Endpoints:**
- `POST /api/update` - Anyone can trigger expensive scraping operations
- `GET /api/location` - Public access (may be acceptable depending on use case)
- `GET /api/history` - Public access (may be acceptable depending on use case)

**Risk:**
- Resource exhaustion attacks via `/api/update`
- Denial of service by repeatedly triggering scraping
- Abuse of external services (shipnext.com, Nominatim geocoding)
- Screenshot generation abuse

**Recommendation:**
```python
from functools import wraps
from flask import request, jsonify

# Simple API key authentication
API_KEY = os.getenv('API_KEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not key or key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/update', methods=['POST'])
@require_api_key
def manual_update():
    # ... existing code
```

**Alternative:** Implement session-based authentication, OAuth, or JWT tokens for more robust security.

**Priority:** CRITICAL

---

### 3. No Rate Limiting ⚠️ HIGH
**Files:** All endpoints  
**Issue:** No rate limiting on any endpoint

**Risk:**
- Denial of Service (DoS) attacks
- Resource exhaustion (CPU, memory, disk I/O)
- Abuse of `/api/update` endpoint to overload scraper
- Database flooding with update requests

**Recommendation:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Apply stricter limits to expensive endpoints
@app.route('/api/update', methods=['POST'])
@limiter.limit("5 per hour")
def manual_update():
    # ... existing code
```

Add to `requirements.txt`:
```
Flask-Limiter==3.5.0
```

**Priority:** HIGH

---

### 4. Unrestricted CORS Policy ⚠️ HIGH
**File:** `app.py` line 10  
**Issue:** CORS is enabled for all origins

```python
CORS(app)  # Allows any origin to access the API
```

**Risk:**
- Cross-Site Request Forgery (CSRF) attacks
- Data leakage to malicious websites
- API abuse from unauthorized domains

**Recommendation:**
```python
# Restrict CORS to specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com", "https://www.yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
```

**Priority:** HIGH

---

### 5. Missing Security Headers ⚠️ HIGH
**Issue:** No security headers are set on responses

**Risk:**
- Clickjacking attacks (missing X-Frame-Options)
- XSS attacks (missing Content-Security-Policy)
- MIME-type sniffing (missing X-Content-Type-Options)
- Missing HTTPS enforcement (missing Strict-Transport-Security)

**Recommendation:**
```python
from flask_talisman import Talisman

# For development (HTTP)
Talisman(app, 
    force_https=False,  # Set to True in production with HTTPS
    content_security_policy={
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",  # Required for inline scripts
            "https://unpkg.com"  # Leaflet.js CDN
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",  # Required for inline styles
            "https://unpkg.com"  # Leaflet.css CDN
        ],
        'img-src': [
            "'self'",
            "data:",
            "https://*.basemaps.cartocdn.com",  # Map tiles
            "https://*.openstreetmap.org"
        ],
        'connect-src': "'self'"
    },
    content_security_policy_nonce_in=['script-src']
)

# Manual header setting alternative
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

Add to `requirements.txt`:
```
flask-talisman==1.1.0
```

**Priority:** HIGH

---

### 6. No HTTPS/TLS Encryption ⚠️ HIGH
**Issue:** Application runs on HTTP only (port 3000)

**Risk:**
- Man-in-the-middle attacks
- Data interception
- Session hijacking
- Credential theft (if authentication is added)

**Recommendation:**
1. **Use a reverse proxy (RECOMMENDED):**
   ```nginx
   # nginx configuration
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       
       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **Alternative: Use Let's Encrypt with Certbot**
3. **Alternative: Deploy behind a cloud provider (AWS, GCP, Cloudflare) with TLS termination**

**Priority:** HIGH for production

---

### 7. Information Disclosure in Error Messages ⚠️ MEDIUM
**File:** `app.py` line 159, `scheduler.py` lines 46, 58  
**Issue:** Detailed error messages exposed to users

```python
except Exception as e:
    return jsonify({'success': False, 'message': str(e)}), 500
```

**Risk:**
- Exposes internal application structure
- Reveals file paths and stack traces
- Provides reconnaissance information to attackers

**Recommendation:**
```python
import logging

logger = logging.getLogger(__name__)

@app.route('/api/update', methods=['POST'])
def manual_update():
    try:
        # ... existing code
    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)  # Log detailed error
        return jsonify({
            'success': False, 
            'message': 'Internal server error'  # Generic message to user
        }), 500
```

**Priority:** MEDIUM

---

### 8. Potential Directory Traversal Vulnerability ⚠️ MEDIUM
**Files:** `app.py` lines 52-58, 62-69  
**Issue:** File serving endpoints may be vulnerable to path traversal

```python
@app.route('/static/<path:filename>')
def static_files(filename):
    response = send_from_directory('static', filename)
    return response
```

**Risk:**
- Access to files outside the static directory
- Exposure of sensitive files (database, configuration, source code)

**Recommendation:**
```python
from werkzeug.security import safe_join
import os

@app.route('/static/<path:filename>')
def static_files(filename):
    # Prevent directory traversal
    safe_path = safe_join(app.static_folder, filename)
    if not safe_path or not os.path.exists(safe_path):
        abort(404)
    response = send_from_directory('static', filename)
    # ... rest of code
```

**Note:** Flask's `send_from_directory` already has some built-in protection, but explicit validation is recommended.

**Priority:** MEDIUM

---

### 9. No Input Validation ⚠️ MEDIUM
**Issue:** No validation on user inputs or API requests

**Risk:**
- Injection attacks (though limited due to no user input currently)
- Malformed requests causing crashes
- Resource exhaustion

**Recommendation:**
```python
from flask import request
from werkzeug.exceptions import BadRequest

@app.route('/api/update', methods=['POST'])
def manual_update():
    # Validate request
    if request.content_length and request.content_length > 1024:
        return jsonify({'error': 'Request too large'}), 413
    
    # Validate content type if accepting JSON
    if request.data and request.content_type != 'application/json':
        return jsonify({'error': 'Invalid content type'}), 415
    
    # ... existing code
```

**Priority:** MEDIUM

---

### 10. Database Security Issues ⚠️ MEDIUM
**File:** `app.py` line 12, multiple database connections  
**Issues:**
- SQLite database file permissions not set
- No database file encryption
- SQL injection risk (mitigated by parameterized queries - GOOD!)
- Concurrent access issues

**Risk:**
- Unauthorized database file access
- Data theft if server is compromised
- Database corruption from concurrent writes

**Recommendation:**
```python
import os
import sqlite3

DB_PATH = 'ship_locations.db'

def init_db():
    """Initialize the database with proper security settings"""
    # Create database with restricted permissions
    if not os.path.exists(DB_PATH):
        # Create database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # ... existing table creation
        conn.close()
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(DB_PATH, 0o600)
```

**Additional recommendations:**
- Use connection pooling to prevent connection exhaustion
- Consider PostgreSQL for production (better concurrency, security features)
- Enable WAL mode for SQLite: `PRAGMA journal_mode=WAL;`

**Priority:** MEDIUM

---

### 11. Production Server Configuration ⚠️ CRITICAL
**File:** `app.py` line 167  
**Issue:** Using Flask's development server in production

```python
app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
```

**Risk:**
- Development server is not designed for production workloads
- Poor performance under load
- Security vulnerabilities in development server
- No process management or auto-restart capabilities

**Recommendation:**
Use a production WSGI server:

```python
# Install gunicorn
# pip install gunicorn

# Run with:
# gunicorn -w 4 -b 0.0.0.0:3000 --access-logfile - --error-logfile - app:app
```

Or use uWSGI:
```bash
uwsgi --http 0.0.0.0:3000 --wsgi-file app.py --callable app --processes 4 --threads 2
```

**Priority:** CRITICAL for production

---

### 12. Missing Logging and Monitoring ⚠️ MEDIUM
**Issue:** Minimal logging, no security monitoring

**Risk:**
- Cannot detect security incidents
- Cannot track abuse or attacks
- Difficult to debug production issues

**Recommendation:**
```python
import logging
from logging.handlers import RotatingFileHandler
import time

# Configure comprehensive logging
if not app.debug:
    # File handler
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Ship Tracker startup')

# Log all requests
@app.before_request
def log_request_info():
    app.logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')

# Log suspicious activity
@app.route('/api/update', methods=['POST'])
def manual_update():
    app.logger.warning(f'Manual update triggered by {request.remote_addr}')
    # ... existing code
```

**Priority:** MEDIUM

---

## Medium Priority Issues

### 13. No CSRF Protection ⚠️ MEDIUM
**Issue:** POST endpoints lack CSRF token validation

**Recommendation:**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))

# Exempt API endpoints if using API key auth
@csrf.exempt
@app.route('/api/update', methods=['POST'])
def manual_update():
    # ... existing code
```

---

### 14. Hardcoded Configuration ⚠️ LOW
**Issue:** Configuration values are hardcoded in source code

**Recommendation:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'ship_locations.db')
    API_KEY = os.getenv('API_KEY')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 3000))
    HOST = os.getenv('HOST', '0.0.0.0')

app.config.from_object(Config)
```

Create `.env` file (add to `.gitignore`):
```env
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
FLASK_DEBUG=False
PORT=3000
```

---

### 15. Third-Party Dependencies ⚠️ ONGOING
**File:** `requirements.txt`  
**Issue:** Dependencies may have vulnerabilities

**Recommendation:**
```bash
# Regularly scan for vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

**Priority:** ONGOING maintenance

---

### 16. robots.txt Not Sufficient for Security ⚠️ INFO
**File:** `robots.txt`  
**Issue:** `robots.txt` does not provide security, only guidance to well-behaved bots

**Note:** While you have a comprehensive `robots.txt`, malicious actors will ignore it. Do not rely on it for security.

---

## Additional Recommendations

### 17. Implement Request Validation
- Validate all input parameters
- Set maximum request sizes
- Implement request timeouts

### 18. Add Health Check Endpoint
```python
@app.route('/health')
def health_check():
    # Check database connectivity
    # Check disk space
    # Return 200 OK if healthy
    return jsonify({'status': 'healthy'}), 200
```

### 19. Implement Graceful Shutdown
```python
import signal
import sys

def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    if _scheduler:
        _scheduler.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### 20. Network Security
- Use firewall rules to restrict access
- Implement IP whitelisting for administrative endpoints
- Use VPN or bastion host for administrative access

### 21. Regular Security Audits
- Schedule regular penetration testing
- Review logs for suspicious activity
- Keep dependencies updated
- Monitor CVE databases for vulnerabilities

---

## Deployment Checklist

Before deploying to the public internet:

- [ ] **Disable debug mode** (`debug=False`)
- [ ] **Implement authentication** on sensitive endpoints
- [ ] **Add rate limiting** to all endpoints
- [ ] **Restrict CORS** to specific origins
- [ ] **Add security headers** (X-Frame-Options, CSP, etc.)
- [ ] **Enable HTTPS/TLS** (use reverse proxy with SSL certificate)
- [ ] **Use production WSGI server** (Gunicorn/uWSGI, not Flask dev server)
- [ ] **Sanitize error messages** (no stack traces to users)
- [ ] **Set database file permissions** (0600)
- [ ] **Implement comprehensive logging** (access logs, error logs, security logs)
- [ ] **Set up monitoring** (uptime, performance, security events)
- [ ] **Configure firewall** (restrict ports, IP whitelisting)
- [ ] **Regular backup strategy** for database
- [ ] **Update all dependencies** to latest secure versions
- [ ] **Security scan** with tools like OWASP ZAP, Nikto, or similar
- [ ] **Load testing** to identify DoS vulnerabilities
- [ ] **Create incident response plan**
- [ ] **Set up environment variables** for sensitive configuration
- [ ] **Review and harden server OS** (disable unnecessary services, apply security patches)

---

## Example: Minimal Hardened Configuration

Here's a minimal example of critical security fixes applied:

```python
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, static_folder='static')

# Configuration from environment
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
API_KEY = os.getenv('API_KEY', 'change-this-in-production')
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# CORS restricted to specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST"]
    }
})

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if not DEBUG:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Logging
if not DEBUG:
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not key or key != API_KEY:
            app.logger.warning(f'Unauthorized access attempt from {request.remote_addr}')
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Protected endpoint
@app.route('/api/update', methods=['POST'])
@require_api_key
@limiter.limit("5 per hour")
def manual_update():
    try:
        # ... existing logic
        pass
    except Exception as e:
        app.logger.error(f'Update failed: {e}', exc_info=True)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # DO NOT USE IN PRODUCTION - Use Gunicorn instead
    app.run(host='0.0.0.0', port=3000, debug=DEBUG)
```

**Production deployment:**
```bash
gunicorn -w 4 -b 127.0.0.1:3000 --access-logfile logs/access.log --error-logfile logs/error.log app:app
```

---

## Conclusion

This application requires **significant security hardening** before public deployment. The most critical issues are:

1. **Debug mode enabled** - Immediate security risk
2. **No authentication** - Allows abuse of expensive operations
3. **No rate limiting** - Vulnerable to DoS attacks
4. **Development server in production** - Not designed for public exposure
5. **No HTTPS** - All traffic is unencrypted

**Estimated effort to secure:** 1-2 days of development work

**Recommended approach:**
1. Fix critical issues first (debug mode, authentication, production server)
2. Implement rate limiting and CORS restrictions
3. Add HTTPS via reverse proxy
4. Implement logging and monitoring
5. Perform security testing before launch

**Do not deploy this application to the public internet until critical security issues are resolved.**
