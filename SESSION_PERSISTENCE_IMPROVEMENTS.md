# Session Persistence Improvements

This document describes the improvements made to BAC-Hunter's session management to fix the repeated login issue.

## Problem Solved

Previously, the script would:
- Open the browser repeatedly for each login attempt
- Not properly capture or persist session data
- Fail to detect valid sessions, causing unnecessary re-authentication
- Provide unclear feedback about session status

## Improvements Made

### 1. Enhanced Session Validation (`session_manager.py`)

**Before**: Only checked for specific auth cookie names
**After**: More lenient validation that accepts any valid cookies

```python
# Old logic - too restrictive
auth_names = ["sessionid", "session_id", "session", "_session", "sid", "connect.sid", ...]
if name in auth_names or any(n in name for n in auth_names):
    return True

# New logic - more lenient
cookies = sess.get("cookies") or []
if cookies:
    for c in cookies:
        if self._cookie_is_valid(c):
            return True  # Any valid cookie is sufficient
```

### 2. Improved Session Loading (`session_manager.py`)

**Before**: Only loaded from per-domain files
**After**: Hierarchical loading with global auth store fallback

```python
def load_domain_session(self, domain: str) -> Dict[str, object]:
    # 1. Try sessions directory first
    if self._sessions_dir:
        session_file = f"{self._sessions_dir}/{domain}.json"
        if os.path.exists(session_file):
            return json.load(f)
    
    # 2. Fallback to global auth store
    data = read_auth(self._auth_store_path)
    if data:
        return {
            "cookies": data.get("cookies") or [],
            "bearer": data.get("bearer") or data.get("token"),
            "csrf": data.get("csrf"),
            "storage": data.get("storage")
        }
    
    return {}
```

### 3. Better Login Detection (`browser_automation.py`)

**Before**: Single criteria for login success
**After**: Multiple criteria with stability requirement

```python
# Multiple success indicators
success_indicators = [
    url_ok,        # URL changed away from login paths
    cookies_ok,    # Any cookies present
    token_ok,      # Bearer token found
    logout_ok,     # Logout button visible
    profile_ok,    # Profile/account link visible
    selector_ok    # Custom success selector
]

# Require at least 2 indicators for stability
strong_ok = sum(success_indicators) >= 2
```

### 4. Enhanced Session Persistence (`session_manager.py`)

**Before**: Basic file saving
**After**: Comprehensive persistence with metadata

```python
data = {
    "cookies": cookies or [],
    "bearer": bearer,
    "csrf": csrf,
    "headers": hdrs,
    "storage": storage or None,
    "captured_at": self._now(),  # Timestamp for debugging
}
write_auth(data, self._auth_store_path)
```

### 5. New Session Management Methods

#### `validate_and_refresh_session(domain_or_url)`
- Validates existing sessions
- Loads from global auth store if needed
- Triggers login only when necessary

#### `clear_expired_sessions()`
- Removes expired sessions from memory and disk
- Automatic cleanup of stale session files

#### `get_session_info(domain_or_url)`
- Provides detailed session debugging information
- Shows cookie counts, validity status, etc.

## Usage Examples

### Basic Session Management

```python
from bac_hunter.session_manager import SessionManager

# Initialize and configure
session_mgr = SessionManager()
session_mgr.configure(
    sessions_dir="sessions",
    browser_driver="playwright",
    login_timeout_seconds=120
)

# Validate/refresh session (will reuse if valid)
success = session_mgr.validate_and_refresh_session("example.com")

# Get session headers for API calls
headers = session_mgr.attach_session("https://example.com/api/test")
```

### Session Information and Debugging

```python
# Get detailed session info
info = session_mgr.get_session_info("example.com")
print(f"Session valid: {info['is_valid']}")
print(f"Cookie count: {info['cookie_count']}")
print(f"Valid cookies: {info['valid_cookies']}")

# Clear expired sessions
session_mgr.clear_expired_sessions()
```

## Configuration Options

### Environment Variables

- `BH_AUTH_DATA`: Path to global auth store (default: `auth_data.json`)
- `BH_LOGIN_SUCCESS_SELECTOR`: Custom CSS selector for login success
- `BH_AUTH_COOKIE_NAMES`: Comma-separated list of auth cookie names
- `BH_LOGIN_STABLE_SECONDS`: Seconds to wait for stable login state (default: 3)

### Session Manager Configuration

```python
session_mgr.configure(
    sessions_dir="sessions",                    # Per-domain session storage
    browser_driver="playwright",               # Browser automation driver
    login_timeout_seconds=120,                 # Individual login timeout
    enable_semi_auto_login=True,               # Enable browser automation
    max_login_retries=3,                       # Max login attempts
    overall_login_timeout_seconds=300          # Total timeout across retries
)
```

## File Structure

```
sessions/
├── example.com.json          # Per-domain session data
├── another-site.com.json     # Another domain's session
└── session.json              # Aggregate session index

auth_data.json                # Global auth store (shared across domains)
```

## Testing

Run the test script to verify the improvements:

```bash
python test_session_persistence.py
```

This will:
1. Test first-time login (opens browser)
2. Test session reuse (no browser)
3. Test session headers generation
4. Test session cleanup

## Benefits

1. **No More Repeated Logins**: Sessions are properly captured and reused
2. **Better User Experience**: Clear feedback about session status
3. **Robust Validation**: More lenient session detection
4. **Automatic Cleanup**: Expired sessions are removed automatically
5. **Debugging Support**: Detailed session information for troubleshooting
6. **Flexible Configuration**: Environment variables for customization

## Migration Notes

- Existing session files are compatible
- Global auth store (`auth_data.json`) is automatically used as fallback
- No breaking changes to existing API
- New methods are additive and optional