# Bot and Web Crawler Blocking Guide

## Overview

This Flask application now includes comprehensive bot and web crawler protection with multiple layers of security:

## Protection Layers Implemented

### 1. **robots.txt File**
- Located at `/static/robots.txt`
- Blocks all well-behaved crawlers and bots
- Includes specific blocks for major search engines and crawlers
- Sets crawl delay to 99999 to discourage any crawling

### 2. **User-Agent Filtering**
The application now detects and blocks 41+ bot patterns including:
- Search engine bots (Googlebot, Bingbot, Baiduspider, YandexBot, etc.)
- Social media crawlers (facebookexternalhit, etc.)
- SEO tools (SemrushBot, AhrefsBot, etc.)
- Generic crawlers and scrapers
- Command-line tools (curl, wget, python-requests, etc.)
- Security scanners (nmap, shodan, masscan, etc.)

### 3. **Request Header Validation**
The middleware blocks requests that:
- Have no User-Agent header
- Have suspiciously short User-Agent strings (< 10 characters)
- Are missing the Accept header (legitimate browsers always send this)

### 4. **Rate Limiting**
Implemented using Flask-Limiter with the following limits:
- **Global limits**: 200 requests/day, 50 requests/hour per IP
- **Homepage**: 30 requests/minute
- **API endpoints**: 20 requests/minute
- **Manual updates**: 5 requests/minute

When limits are exceeded, the server returns HTTP 429 (Too Many Requests).

## How It Works

### Request Flow
1. Every request passes through the `block_bots()` middleware
2. The middleware checks:
   - If the path is `/robots.txt` → Allow (everyone can read robots.txt)
   - User-Agent header → Block if missing or matches bot patterns
   - Accept header → Block if missing
3. If all checks pass, rate limiting is applied per endpoint
4. If rate limits are exceeded, return 403 Forbidden

### Protected Endpoints
All endpoints are protected:
- `/` - Main page
- `/api/location` - Location data
- `/api/history` - History data
- `/api/update` - Manual update trigger
- `/static/*` - Static files
- `/screenshots/*` - Screenshot files

## Testing

### Manual Testing

Run the included test script:
```bash
# Start the Flask app first
python3 app.py

# In another terminal, run the test
python3 test_bot_blocking.py
```

### Test Scenarios

The test script verifies:
1. ✓ Normal browsers can access the site
2. ✓ Bot user agents are blocked (403 Forbidden)
3. ✓ Requests without User-Agent are blocked
4. ✓ Requests without Accept header are blocked
5. ✓ robots.txt is accessible
6. ✓ Rate limiting works correctly

### Manual cURL Testing

Test bot blocking:
```bash
# This should be blocked (bot user agent)
curl -A "Googlebot/2.1" http://localhost:3000/

# This should be blocked (no Accept header)
curl -A "Mozilla/5.0" http://localhost:3000/

# This should work (proper headers)
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
     -H "Accept: text/html" \
     http://localhost:3000/
```

## Configuration

### Adjusting Rate Limits

Edit the limits in `app.py`:

```python
# Global limits
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],  # Modify these
    storage_uri="memory://"
)

# Per-endpoint limits
@app.route('/api/location')
@limiter.limit("20 per minute")  # Modify this
def get_location():
    ...
```

### Adding More Bot Patterns

Add patterns to the `BOT_USER_AGENTS` list in `app.py`:

```python
BOT_USER_AGENTS = [
    r'bot', r'crawl', r'spider',
    r'your-new-pattern',  # Add here
    # ...
]
```

### Whitelisting Specific Bots

To allow specific bots while blocking others, modify the `block_bots()` function:

```python
@app.before_request
def block_bots():
    if request.path == '/robots.txt':
        return None
    
    user_agent = request.headers.get('User-Agent', '')
    
    # Whitelist example
    if 'specific-allowed-bot' in user_agent.lower():
        return None
    
    # Continue with normal blocking logic
    if is_bot(user_agent):
        abort(403)
    ...
```

## Important Notes

### robots.txt
- The `/robots.txt` endpoint is **always accessible** (not blocked)
- This is intentional - bots need to be able to read it to know they're not welcome
- Well-behaved bots will respect robots.txt and not crawl the site

### Rate Limiting Storage
- Currently uses in-memory storage: `storage_uri="memory://"`
- For production with multiple workers, consider using Redis:
  ```python
  storage_uri="redis://localhost:6379"
  ```

### False Positives
If legitimate users are being blocked:
1. Check their User-Agent string
2. Adjust the `BOT_USER_AGENTS` patterns if needed
3. Add whitelisting logic as shown above

### Reverse Proxies
If behind a reverse proxy (nginx, Apache, etc.), update the rate limiter to use the correct IP:
```python
from flask_limiter.util import get_remote_address

# For proxies that set X-Forwarded-For
limiter = Limiter(
    app=app,
    key_func=lambda: request.headers.get('X-Forwarded-For', get_remote_address())
)
```

## Security Considerations

### What This Protects Against
✓ Automated scrapers and crawlers
✓ Search engine indexing
✓ Basic DDoS attempts (via rate limiting)
✓ Reconnaissance by security scanners
✓ Simple bot attacks

### What This Doesn't Protect Against
✗ Sophisticated bots that mimic real browsers
✗ Distributed attacks from many IPs
✗ Attacks that rotate user agents to match real browsers
✗ Human-operated scraping

### Additional Security Measures to Consider
1. **CAPTCHA** - For critical endpoints
2. **JavaScript Challenges** - Require client-side execution
3. **Cloudflare/WAF** - Professional bot protection
4. **Authentication** - Require login for sensitive data
5. **Honeypot Fields** - Hidden form fields to catch bots

## Files Modified

1. **requirements.txt** - Added `flask-limiter==3.5.0`
2. **app.py** - Added bot detection, rate limiting, and middleware
3. **static/robots.txt** - Created to discourage crawlers

## Files Created

1. **static/robots.txt** - Bot discouragement file
2. **test_bot_blocking.py** - Test script for verification
3. **BOT_BLOCKING_GUIDE.md** - This documentation file

## Maintenance

### Monitoring
Monitor your logs for:
- 403 Forbidden responses (blocked bots)
- 429 Too Many Requests (rate limit hits)
- Unusual patterns in User-Agent strings

### Updating Bot Patterns
Regularly update the `BOT_USER_AGENTS` list as new bots emerge. Check logs for suspicious user agents and add patterns as needed.

---

**Need Help?** Check the test script output or Flask application logs for debugging information.
