# API Key Authentication Implementation

## Summary

This document describes the API key authentication feature implemented for POST endpoints in the Ship Tracker application.

## Changes Made

### Backend Changes (`app.py`)

1. **Added Required Imports**:
   - `request` from Flask (for accessing headers and query parameters)
   - `secrets` module (for generating secure random API keys)
   - `wraps` from functools (for preserving function metadata in decorators)

2. **Database Schema Updates**:
   - Added `api_keys` table with the following columns:
     - `id`: Primary key
     - `key`: Unique API key string
     - `name`: Descriptive name for the key
     - `created_at`: Timestamp when key was created
     - `last_used`: Timestamp when key was last used (updated on each authentication)
     - `is_active`: Boolean flag (1=active, 0=disabled)
   
3. **Default API Key Generation**:
   - On first run, automatically generates a secure random API key
   - Displays the key prominently in the console
   - Supports custom keys via `API_KEY` environment variable
   - Only generates a key if no active keys exist in the database

4. **Authentication Decorator**:
   - Created `@require_api_key` decorator
   - Checks for API key in two locations:
     - `X-API-Key` header (primary method)
     - `api_key` query parameter (fallback)
   - Returns 401 Unauthorized if no key provided
   - Returns 403 Forbidden if key is invalid or inactive
   - Updates `last_used` timestamp on successful authentication

5. **Protected Endpoint**:
   - Applied `@require_api_key` decorator to `/api/update` POST endpoint
   - Updated docstring to indicate authentication requirement

### Frontend Changes

#### `static/index.html`
- Added API key input field with label
- Added password input type for security (can be toggled to text)
- Added eye icon button to toggle password visibility
- Positioned in controls section for easy access

#### `static/app.js`
- Modified `manualUpdate()` function to:
  - Read API key from input field
  - Validate that key is provided before making request
  - Include API key in `X-API-Key` header
  - Store API key in localStorage for convenience
  - Show appropriate error messages
- Added `toggleApiKeyVisibility()` function for show/hide functionality
- Added event listener for toggle button
- Added code to restore saved API key from localStorage on page load

#### `static/styles.css`
- Added `.api-key-input` styles for container layout
- Added label styling for clear visibility
- Added input field styling with focus states
- Added `.btn-toggle` styles for the visibility toggle button
- Ensured responsive design with flexbox layout

### Documentation Updates (`README.md`)

1. **New Section: API Key Authentication**
   - Overview of authentication system
   - How to get your API key
   - How to set a custom API key
   - Usage instructions for web interface and API
   - API key management (adding, disabling keys)
   - Security best practices

2. **Updated API Endpoints Section**
   - Added note about POST endpoint authentication
   - Updated `/api/update` documentation with:
     - Authentication requirement
     - Header format
     - Example curl requests
     - New response codes (401, 403)

3. **Updated Component Descriptions**
   - Mentioned API key authentication in `app.py` description
   - Added `api_keys` table schema to database documentation
   - Marked POST endpoints as requiring authentication

## Security Features

1. **Secure Key Generation**: Uses `secrets.token_urlsafe()` for cryptographically secure random keys
2. **Flexible Authentication**: Supports both header and query parameter methods
3. **Key Management**: Can disable keys without deletion, preserving audit trail
4. **Usage Tracking**: Records when each key was last used
5. **Environment Variable Support**: Production keys can be set via environment variables
6. **Browser Security**: Input field uses password type by default

## Usage Examples

### Web Interface
```
1. Copy the API key from the console when you first start the app
2. Paste it into the "API Key" input field in the web interface
3. Click "Get Current Location" to trigger an update
4. The key is automatically saved in your browser for future visits
```

### API Request (cURL)
```bash
# Using header (recommended)
curl -X POST http://localhost:3000/api/update \
  -H "X-API-Key: your-api-key-here"

# Using query parameter
curl -X POST "http://localhost:3000/api/update?api_key=your-api-key-here"
```

### Custom API Key via Environment Variable
```bash
export API_KEY="my-secure-custom-key"
python3 app.py
```

## Testing

All components have been tested:
- ✅ Database schema creation
- ✅ API key table structure
- ✅ Decorator implementation
- ✅ Frontend integration
- ✅ localStorage persistence
- ✅ Syntax validation

## Backward Compatibility

- GET endpoints remain unprotected and publicly accessible
- Existing functionality for viewing locations is unchanged
- Only POST operations (data modifications) require authentication
- Rate limiting continues to work as before

## Future Enhancements

Potential improvements for consideration:
- Multiple API keys per user
- Role-based access control (read-only vs. write access)
- Key expiration dates
- API key rotation workflow
- Admin UI for key management
- Request logging per API key
- Rate limits per API key
