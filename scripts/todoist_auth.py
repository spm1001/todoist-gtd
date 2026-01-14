#!/usr/bin/env python3
"""
Todoist OAuth authentication module.

Provides OAuth 2.0 authentication flow for Todoist.
Stores tokens portably: env var, macOS Keychain, or file (~/.todoist-token).
Supports both auto mode (localhost callback) and manual mode (paste redirect URL).

Usage:
    from todoist_auth import authenticate, get_auth_status

    # Interactive auth (opens browser)
    authenticate()

    # Manual mode for SSH
    authenticate(manual=True)

    # Check current status
    status = get_auth_status()
"""

import os
import secrets
import subprocess
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

# OAuth configuration
# TODO: Replace with actual credentials after registering at developer.todoist.com
CLIENT_ID = "PLACEHOLDER_CLIENT_ID"
CLIENT_SECRET = "PLACEHOLDER_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8080/callback"
OAUTH_PORT = 8080
SCOPES = ["data:read_write"]
AUTH_TIMEOUT_SECONDS = 300  # 5 minutes

# Import portable secrets management
from todoist_secrets import get_token_quiet, store_token


def _load_credentials_from_file() -> tuple[str, str]:
    """Load client credentials from JSON file if it exists."""
    creds_path = Path(__file__).parent / "client_credentials.json"
    if creds_path.exists():
        import json
        with open(creds_path) as f:
            data = json.load(f)
        return data.get("client_id", CLIENT_ID), data.get("client_secret", CLIENT_SECRET)
    return CLIENT_ID, CLIENT_SECRET


def _build_auth_url(client_id: str, scopes: list, state: str) -> str:
    """Build OAuth authorization URL."""
    params = {
        "client_id": client_id,
        "scope": ",".join(scopes),
        "state": state,
    }
    return f"https://todoist.com/oauth/authorize?{urlencode(params)}"


def _generate_state() -> str:
    """Generate CSRF state token (32 random bytes, hex encoded)."""
    return secrets.token_hex(32)


def _exchange_token_directly(client_id: str, client_secret: str, code: str) -> Optional[str]:
    """
    Exchange authorization code for token directly via HTTP.

    Workaround for SDK bug where AuthResult expects 'state' field
    that Todoist doesn't return in token response.
    """
    import requests

    try:
        response = requests.post(
            "https://todoist.com/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except Exception as e:
        print(f"Direct token exchange failed: {e}", file=sys.stderr)
        return None


# HTML templates for OAuth callback
SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Todoist Authorization Successful</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
               display: flex; justify-content: center; align-items: center;
               height: 100vh; margin: 0; background: #f5f5f5; }
        .container { text-align: center; padding: 40px; background: white;
                     border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #e44332; margin-bottom: 16px; }
        p { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✓ Authorization Successful</h1>
        <p>You can close this tab and return to your terminal.</p>
    </div>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Todoist Authorization Failed</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
               display: flex; justify-content: center; align-items: center;
               height: 100vh; margin: 0; background: #f5f5f5; }
        .container { text-align: center; padding: 40px; background: white;
                     border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #e44332; margin-bottom: 16px; }
        p { color: #666; }
        .error { color: #c62828; font-family: monospace; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✗ Authorization Failed</h1>
        <p>Something went wrong during authorization.</p>
        <p class="error">{error}</p>
    </div>
</body>
</html>"""


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    auth_code: Optional[str] = None
    auth_error: Optional[str] = None
    expected_state: Optional[str] = None

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle OAuth callback."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Check for error
        if "error" in params:
            error = params["error"][0]
            OAuthCallbackHandler.auth_error = error
            self._send_error_response(f"OAuth error: {error}")
            return

        # Validate state (CSRF protection)
        state = params.get("state", [None])[0]
        if state != OAuthCallbackHandler.expected_state:
            OAuthCallbackHandler.auth_error = "State mismatch (possible CSRF attack)"
            self._send_error_response("Security error: state parameter mismatch")
            return

        # Extract code
        code = params.get("code", [None])[0]
        if not code:
            OAuthCallbackHandler.auth_error = "No authorization code received"
            self._send_error_response("No authorization code in callback")
            return

        OAuthCallbackHandler.auth_code = code
        self._send_success_response()

    def _send_success_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(SUCCESS_HTML.encode())

    def _send_error_response(self, error: str):
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(ERROR_HTML.format(error=error).encode())


def _auto_flow(auth_url: str, state: str) -> Optional[str]:
    """
    Auto mode: Open browser and wait for localhost callback.

    Returns the authorization code on success, None on failure.
    """
    # Reset handler state
    OAuthCallbackHandler.auth_code = None
    OAuthCallbackHandler.auth_error = None
    OAuthCallbackHandler.expected_state = state

    # Start server
    server = HTTPServer(("localhost", OAUTH_PORT), OAuthCallbackHandler)
    server.timeout = AUTH_TIMEOUT_SECONDS

    # Open browser
    print(f"Opening browser for authorization...")
    webbrowser.open(auth_url)

    # Wait for callback (with timeout)
    try:
        while OAuthCallbackHandler.auth_code is None and OAuthCallbackHandler.auth_error is None:
            server.handle_request()
    except Exception as e:
        print(f"Error waiting for callback: {e}", file=sys.stderr)
        return None
    finally:
        server.server_close()

    if OAuthCallbackHandler.auth_error:
        print(f"Authorization failed: {OAuthCallbackHandler.auth_error}", file=sys.stderr)
        return None

    return OAuthCallbackHandler.auth_code


def _manual_flow(auth_url: str, state: str, code_input: Optional[str] = None) -> Optional[str]:
    """
    Manual mode: Print URL, user pastes redirect URL or code.

    Args:
        auth_url: The authorization URL to display
        state: The expected state parameter
        code_input: Optional pre-provided code/URL (for non-interactive use)

    Returns the authorization code on success, None on failure.
    """
    print("\n" + "=" * 60)
    print("MANUAL AUTHORIZATION")
    print("=" * 60)
    print("\n1. Open this URL in your browser:\n")
    print(f"   {auth_url}")
    print("\n2. Sign in and click 'Authorize'")
    print("\n3. You'll be redirected to a URL that fails to load.")
    print("   Copy the ENTIRE URL from your browser's address bar.")
    print("\n4. Paste it below (or just the 'code' parameter value):\n")

    if code_input:
        user_input = code_input
        print(f"   Using provided input: {user_input[:50]}...")
    else:
        try:
            user_input = input("   > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            return None

    if not user_input:
        print("No input provided.", file=sys.stderr)
        return None

    # Parse input - could be full URL or just the code
    code = _parse_code_from_input(user_input)

    # Validate state if we can extract it from URL
    if "state=" in user_input:
        parsed = urlparse(user_input)
        params = parse_qs(parsed.query)
        url_state = params.get("state", [None])[0]
        if url_state and url_state != state:
            print("Warning: State mismatch detected. This could indicate a security issue.", file=sys.stderr)
            # Continue anyway for manual mode - user is in control

    return code


def _parse_code_from_input(input_str: str) -> str:
    """
    Parse authorization code from user input.

    Accepts either a full redirect URL or just the code value.
    """
    # Try parsing as URL first
    if input_str.startswith("http"):
        parsed = urlparse(input_str)
        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        if code:
            return code

    # Fall back to treating input as raw code
    return input_str


def authenticate(manual: bool = False, code: Optional[str] = None) -> bool:
    """
    Run OAuth authentication flow.

    Args:
        manual: If True, use manual mode (print URL, paste redirect)
        code: Optional pre-provided code/URL for non-interactive manual mode

    Returns True on success, False on failure.
    """
    client_id, client_secret = _load_credentials_from_file()

    if client_id == "PLACEHOLDER_CLIENT_ID":
        print("Error: OAuth not configured.", file=sys.stderr)
        print("\nTo set up OAuth:", file=sys.stderr)
        print("  1. Register an app at https://developer.todoist.com", file=sys.stderr)
        print("  2. Create skills/todoist-gtd/scripts/client_credentials.json with:", file=sys.stderr)
        print('     {"client_id": "your_id", "client_secret": "your_secret"}', file=sys.stderr)
        print("\nAlternatively, use a personal API token:", file=sys.stderr)
        print("  1. Get your token from: https://todoist.com/prefs/integrations", file=sys.stderr)
        print('  2. Set: export TODOIST_API_KEY="TOKEN" in ~/.bashrc or ~/.secrets', file=sys.stderr)
        return False

    state = _generate_state()

    # Generate authorization URL
    auth_url = _build_auth_url(client_id, SCOPES, state)

    # Run appropriate flow
    if manual:
        auth_code = _manual_flow(auth_url, state, code)
    else:
        auth_code = _auto_flow(auth_url, state)

    if not auth_code:
        return False

    # Exchange code for token
    # Note: Using direct HTTP instead of SDK due to AuthResult parsing bug
    # (SDK expects 'state' in response but Todoist doesn't return it)
    print("Exchanging authorization code for token...")
    token = _exchange_token_directly(client_id, client_secret, auth_code)
    if not token:
        return False

    # Store token
    if not store_token(token):
        return False

    print("\n✓ Successfully authenticated with Todoist!")
    return True


def get_auth_status() -> dict:
    """
    Check current authentication status.

    Returns dict with:
        - authenticated: bool
        - message: str describing status
    """
    token = get_token_quiet()

    if not token:
        return {
            "authenticated": False,
            "message": "Not authenticated. Run `todoist.py auth` to connect your Todoist account."
        }

    # Try to verify token works by making a simple API call
    try:
        from todoist_api_python.api import TodoistAPI
        api = TodoistAPI(token)
        # This will fail if token is revoked
        list(api.get_projects())
        return {
            "authenticated": True,
            "message": "Authenticated with Todoist."
        }
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            return {
                "authenticated": False,
                "message": "Token revoked or expired. Run `todoist.py auth` to re-authenticate."
            }
        # Network error or other issue - assume still authenticated
        return {
            "authenticated": True,
            "message": f"Token present (could not verify: {e})"
        }


def main():
    """CLI entry point for standalone testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Todoist OAuth authentication")
    parser.add_argument("--manual", action="store_true", help="Use manual mode (paste redirect URL)")
    parser.add_argument("--code", help="Authorization code or redirect URL (for non-interactive manual mode)")
    parser.add_argument("--status", action="store_true", help="Check authentication status")

    args = parser.parse_args()

    if args.status:
        status = get_auth_status()
        print(status["message"])
        sys.exit(0 if status["authenticated"] else 1)

    success = authenticate(manual=args.manual, code=args.code)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
