# BAC-Hunter Session Handling Fixes

## Overview

This document outlines the comprehensive fixes applied to BAC-Hunter's session handling system to address the issues you identified:

1. **Domain-specific session files**: Ensured consistent file naming and usage
2. **Cookie filtering**: Prevented capture of unrelated cookies (Google, YouTube, etc.)
3. **Session isolation**: Proper separation between different domains
4. **Consistent file usage**: Fixed inconsistent file naming and loading
5. **Proper session validation**: Improved session checking and cleanup

## Issues Fixed

### 1. Unrelated Cookies Being Captured

**Problem**: The script was capturing cookies from Google, YouTube, and other unrelated websites instead of only the target domain.

**Solution**: 
- Added `_is_cookie_for_domain()` method to validate cookie domain ownership
- Added `_filter_cookies_by_domain()` method to filter cookies by target domain
- Updated all cookie extraction points to filter by domain
- Modified browser automation to only capture domain-relevant cookies

**Files Modified**:
- `bac_hunter/session_manager.py`: Added domain filtering methods
- `bac_hunter/integrations/browser_automation.py`: Updated cookie extraction
- `bac_hunter/http_client.py`: Added domain filtering in session hydration

### 2. Inconsistent Session File Naming

**Problem**: The script was generating different file names on different runs instead of using consistent naming.

**Solution**:
- Improved `_session_path()` method with proper domain sanitization
- Used regex-based sanitization: `re.sub(r'[^\w\-\.]', '_', domain.lower())`
- Ensured consistent file naming across all operations

**Example**:
```python
# Before: Inconsistent naming
domain = "example.com:8080" -> "example.com:8080.json" (invalid filename)

# After: Consistent sanitized naming  
domain = "example.com:8080" -> "example.com_8080.json" (valid filename)
```

### 3. Session Files Not Being Used Consistently

**Problem**: Some parts of the code were not loading the correct session files or switching between different files.

**Solution**:
- Updated `load_domain_session()` to use consistent file paths
- Modified `save_domain_session()` to use the same naming convention
- Ensured all session operations use `_session_path()` method
- Fixed session file loading to prioritize domain-specific files over global auth store

### 4. Missing Domain Validation

**Problem**: No proper validation to ensure cookies belonged to the target domain.

**Solution**:
- Added comprehensive domain validation logic
- Supports exact domain matches and parent domain relationships
- Handles cookies with no domain specification (assumes current domain)
- Validates both direct domain matches and subdomain relationships

**Domain Validation Logic**:
```python
def _is_cookie_for_domain(self, cookie: dict, target_domain: str) -> bool:
    cookie_domain = cookie.get("domain", "").lower()
    if not cookie_domain:
        return True  # No domain specified, assume current domain
    
    # Remove leading dot if present
    if cookie_domain.startswith('.'):
        cookie_domain = cookie_domain[1:]
    
    # Exact match
    if cookie_domain == target_domain.lower():
        return True
    
    # Parent domain match (e.g., .example.com for sub.example.com)
    if target_domain.lower().endswith('.' + cookie_domain):
        return True
    
    return False
```

## Implementation Details

### Session File Structure

Each domain now gets its own session file with consistent naming:

```
sessions/
├── example.com.json
├── sub.example.com.json
├── test-site.com.json
└── session.json (aggregate index)
```

### Cookie Filtering Process

1. **Browser Automation**: When extracting cookies from browser, filter by target domain
2. **Response Processing**: When processing HTTP responses, validate Set-Cookie headers
3. **Session Loading**: When loading from global auth store, filter cookies by domain
4. **Session Saving**: When saving sessions, ensure only domain-relevant cookies are stored

### Cross-Domain Isolation

- Each domain maintains its own session file
- Cookies are strictly filtered by domain
- No cross-contamination between different target sites
- Separate bearer tokens and CSRF tokens per domain

## Testing

A comprehensive test suite (`test_session_fixes.py`) was created to verify all fixes:

### Test Coverage

1. **Domain Filtering Test**: Verifies cookies are filtered correctly
2. **Session File Naming Test**: Ensures consistent file naming
3. **Session Persistence Test**: Validates save/load operations
4. **Cross-Domain Isolation Test**: Confirms domain separation
5. **Session Cleanup Test**: Tests expired session removal

### Running Tests

```bash
python3 test_session_fixes.py
```

Expected output:
```
🔧 BAC-Hunter Session Handling Fixes Test Suite
============================================================
🧪 Testing domain filtering...
✅ Domain filtering works correctly

🧪 Testing session file naming...
✅ example.com -> example.com.json
✅ sub.example.com -> sub.example.com.json

🧪 Testing session persistence...
✅ Session file created
✅ Session data loaded correctly

🧪 Testing cross-domain isolation...
✅ Cross-domain isolation works

🧪 Testing session cleanup...
✅ Expired session file removed

============================================================
📊 Test Results: 5/5 tests passed
🎉 All tests passed! Session handling fixes are working correctly.
```

## Files Modified

### Core Session Management
- `bac_hunter/session_manager.py`: Main session handling logic
- `bac_hunter/auth_store.py`: Global auth store integration
- `bac_hunter/http_client.py`: HTTP client session integration

### Browser Automation
- `bac_hunter/integrations/browser_automation.py`: Cookie extraction filtering

### Configuration
- `bac_hunter/config.py`: Session directory configuration

## Key Methods Added/Modified

### SessionManager Class

**New Methods**:
- `_is_cookie_for_domain()`: Validates cookie domain ownership
- `_filter_cookies_by_domain()`: Filters cookies by target domain

**Modified Methods**:
- `_session_path()`: Improved file naming with sanitization
- `load_domain_session()`: Consistent file loading
- `save_domain_session()`: Domain-filtered session saving
- `process_response()`: Domain-aware cookie capture
- `open_browser_login()`: Filtered cookie extraction
- `clear_expired_sessions()`: Consistent file cleanup

### Browser Automation

**Modified Methods**:
- `PlaywrightDriver.extract_cookies_and_tokens()`: Added domain filtering
- `SeleniumDriver.extract_cookies_and_tokens()`: Added domain filtering
- `InteractiveLogin.open_and_wait()`: Domain-aware cookie extraction

## Benefits

1. **Clean Session Data**: Only relevant cookies are captured and stored
2. **Consistent Behavior**: Same session files are used across runs
3. **Domain Isolation**: No cross-contamination between different sites
4. **Improved Reliability**: Better session validation and cleanup
5. **Debugging**: Clear session file structure for troubleshooting

## Migration Notes

- Existing session files will continue to work
- New sessions will be created with proper domain filtering
- Expired sessions will be automatically cleaned up
- Global auth store is still supported as fallback

## Configuration

Session handling can be configured via environment variables:

```bash
# Session directory (default: "sessions")
export BH_SESSIONS_DIR="/path/to/sessions"

# Browser driver (default: "playwright")
export BH_BROWSER="playwright"

# Login timeout (default: 180 seconds)
export BH_LOGIN_TIMEOUT="300"

# Disable interactive login (default: enabled)
export BH_SKIP_LOGIN="1"
```

## Troubleshooting

### Common Issues

1. **Session not persisting**: Check file permissions on sessions directory
2. **Wrong cookies captured**: Verify domain filtering is working
3. **File naming issues**: Ensure domain sanitization is working correctly

### Debug Information

Session information can be retrieved using:

```python
session_mgr = SessionManager()
info = session_mgr.get_session_info("example.com")
print(info)
```

This provides detailed information about session status, cookie count, and validity.

## Conclusion

These fixes ensure that BAC-Hunter's session handling is:
- **Domain-specific**: Only captures relevant cookies
- **Consistent**: Uses same files across runs
- **Isolated**: No cross-domain contamination
- **Reliable**: Proper validation and cleanup
- **Maintainable**: Clear structure and debugging capabilities

The session handling system now properly manages authentication data while maintaining clean separation between different target domains.