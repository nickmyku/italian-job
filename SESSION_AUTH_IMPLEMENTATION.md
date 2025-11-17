# Session-Based Authentication Implementation

## Overview

Session-based authentication has been implemented for all POST endpoints in the Ship Tracker application. This protects sensitive operations like manual location updates from unauthorized access.

## What's New

### Backend Changes (`app.py`)

1. **Session Configuration**
   - Added Flask session support with secure configuration
   - Secret key management (via environment variable or auto-generated)
   - Secure cookie settings (HttpOnly, SameSite)
   - CORS configured to support credentials

2. **Authentication Endpoints**
   - `POST /api/login` - Authenticate and create session
   - `POST /api/logout` - Clear session and logout
   - `GET /api/check-auth` - Check current authentication status

3. **Protected Endpoints**
   - `POST /api/update` - Now requires authentication
   - Uses `@require_auth` decorator to enforce authentication

4. **Rate Limiting**
   - Login endpoint limited to 10 requests per minute to prevent brute force attacks

### Frontend Changes

1. **Login UI (`index.html`)**
   - Added login modal with username and password fields
   - Authentication status display showing current user
   - Login/Logout buttons in the controls panel

2. **Authentication Logic (`app.js`)**
   - Authentication state management
   - Login/logout handlers
   - Automatic session validation on page load
   - Handles 401 responses by prompting login
   - All authenticated requests include credentials

3. **Styling (`styles.css`)**
   - Modern modal design with animations
   - Form styling with focus states
   - Authentication status UI elements
   - Error message display

## Default Credentials

**Username:** `admin`  
**Password:** `shiptracker2024`

> ⚠️ **IMPORTANT**: Change these credentials in production! 
> The credentials are stored in the `USERS` dictionary in `app.py` (line 30).

## How It Works

### User Flow

1. **Unauthenticated User**
   - User visits the application
   - Can view location data and history (GET endpoints)
   - Clicking "Get Current Location" button shows login modal

2. **Login Process**
   - User clicks "Login" button
   - Modal appears with username/password fields
   - Upon successful login, session is created
   - UI updates to show username and "Logout" button

3. **Authenticated User**
   - Can trigger manual location updates
   - Session persists across page reloads
   - Can logout at any time

4. **Session Expiration**
   - If session expires, user receives 401 error
   - Login modal automatically appears
   - User can re-authenticate without losing page state

### Security Features

1. **Session Management**
   - Flask's built-in session handling with secure cookies
   - HttpOnly cookies prevent XSS attacks
   - SameSite protection against CSRF

2. **Rate Limiting**
   - Login endpoint: 10 requests/minute (prevents brute force)
   - Update endpoint: 60 requests/minute (already protected)

3. **Credential Storage**
   - Currently uses simple dictionary (for development)
   - **Production Recommendation**: Use database with hashed passwords

## API Endpoints

### POST /api/login
Authenticate user and create session.

**Request:**
```json
{
  "username": "admin",
  "password": "shiptracker2024"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Login successful"
}
```

**Response (Failure):**
```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

**Rate Limit:** 10 requests per minute

---

### POST /api/logout
Clear session and logout user.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### GET /api/check-auth
Check current authentication status.

**Response:**
```json
{
  "authenticated": true,
  "username": "admin"
}
```

---

### POST /api/update (Protected)
Manually trigger location update. **Requires authentication.**

**Headers:**
- Must include session cookie (sent automatically by browser)

**Response (Not Authenticated):**
```json
{
  "success": false,
  "message": "Authentication required"
}
```
HTTP Status: 401 Unauthorized

## Configuration

### Change Credentials

Edit `app.py` around line 30:

```python
USERS = {
    'admin': 'shiptracker2024',  # username: password
    'user2': 'another_password'  # Add more users
}
```

### Set Secret Key (Production)

Set the `SECRET_KEY` environment variable:

```bash
export SECRET_KEY="your-secure-random-key-here"
```

Or let the application generate one automatically (will reset on restart).

### Adjust Session Settings

Edit `app.py` around line 15:

```python
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only (for production)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session duration
```

## Production Recommendations

### 1. Use Database with Hashed Passwords

Replace the `USERS` dictionary with a database:

```python
from werkzeug.security import check_password_hash, generate_password_hash

# Store hashed passwords in database
def verify_credentials(username, password):
    user = db.get_user(username)
    if user:
        return check_password_hash(user.password_hash, password)
    return False
```

### 2. Enable HTTPS

Update session configuration:

```python
app.config['SESSION_COOKIE_SECURE'] = True  # Requires HTTPS
```

### 3. Add CSRF Protection

Install Flask-WTF:

```bash
pip install flask-wtf
```

Enable CSRF:

```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### 4. Implement Password Reset

Add endpoints for:
- Password reset request
- Email verification
- Password update

### 5. Add Multi-Factor Authentication (MFA)

Consider implementing TOTP-based 2FA for additional security.

### 6. Session Storage

For production with multiple instances, use Redis or database-backed sessions:

```python
from flask_session import Session
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)
```

## Testing

### Test Login
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "shiptracker2024"}' \
  -c cookies.txt
```

### Test Protected Endpoint
```bash
curl -X POST http://localhost:3000/api/update \
  -b cookies.txt
```

### Test Without Authentication
```bash
curl -X POST http://localhost:3000/api/update
# Should return 401 Unauthorized
```

## Troubleshooting

### Login Button Not Working
- Check browser console for JavaScript errors
- Verify modal is loading correctly
- Ensure credentials are correct

### Session Not Persisting
- Check if cookies are enabled in browser
- Verify SECRET_KEY is set
- Check browser's cookie storage

### 401 Errors After Login
- Check if session cookie is being sent with requests
- Verify CORS credentials are configured
- Check if session has expired

### CORS Issues
- Ensure `supports_credentials=True` in CORS config
- Frontend must send `credentials: 'include'` in fetch requests
- Check if origin is allowed in CORS settings

## Migration Notes

### Existing Deployments

If you have an existing deployment:

1. **No Database Changes Required** - Authentication is session-based
2. **Update Frontend Files** - Replace index.html, app.js, and styles.css
3. **Update Backend** - Deploy updated app.py
4. **Set SECRET_KEY** - Add environment variable for production
5. **Test Authentication** - Verify login/logout works correctly

### Breaking Changes

- **POST /api/update** now requires authentication
- Users will need to login to trigger manual updates
- Read-only operations (GET endpoints) remain public

## Summary

Session-based authentication has been successfully implemented with:
- ✅ Secure session management with Flask sessions
- ✅ Login/logout functionality with modal UI
- ✅ Protected POST endpoints with authentication requirement
- ✅ Rate limiting on authentication endpoints
- ✅ User-friendly error handling and login prompts
- ✅ Clean, modern UI with animations
- ✅ Production-ready security recommendations

The implementation is ready for development use and can be enhanced for production with the recommendations provided above.
