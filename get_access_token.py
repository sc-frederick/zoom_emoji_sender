#!/usr/bin/env python3
"""
Zoom OAuth Helper - Get Access Token

This script helps you obtain a Zoom OAuth access token by:
1. Starting a local web server
2. Opening your browser to authorize the app
3. Catching the authorization code
4. Exchanging it for an access token
5. Saving it to a .env file
"""

import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import sys
import os
import base64


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback from Zoom"""
    
    authorization_code = None
    
    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        # Parse the authorization code from the URL
        query_components = parse_qs(urlparse(self.path).query)
        
        if 'code' in query_components:
            OAuthCallbackHandler.authorization_code = query_components['code'][0]
            
            # Send success response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <html>
            <head><title>Authorization Successful</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #2D8CFF;">✓ Authorization Successful!</h1>
                <p>You can close this window and return to your terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
        else:
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = """
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #FF0000;">✗ Authorization Failed</h1>
                <p>No authorization code received. Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


def exchange_code_for_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """
    Exchange authorization code for access token
    
    Args:
        client_id: Your Zoom OAuth Client ID
        client_secret: Your Zoom OAuth Client Secret
        code: Authorization code from OAuth callback
        redirect_uri: The redirect URI (must match what's configured in Zoom app)
    
    Returns:
        Dictionary containing access_token, refresh_token, etc.
    """
    token_url = "https://zoom.us/oauth/token"
    
    # Create Basic Auth header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    
    return response.json()


def save_to_env_file(access_token: str, refresh_token: str = ""):
    """Save tokens to .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env') or '.'
    
    with open(env_path, 'w') as f:
        f.write(f"# Zoom OAuth Access Token\n")
        f.write(f"# Get this from your Zoom OAuth app at https://marketplace.zoom.us/\n")
        f.write(f"ZOOM_ACCESS_TOKEN={access_token}\n")
        if refresh_token:
            f.write(f"\n# Refresh token to get new access tokens when they expire\n")
            f.write(f"ZOOM_REFRESH_TOKEN={refresh_token}\n")
    
    print(f"\n✓ Tokens saved to {env_path}")


def main():
    """Main function to run the OAuth flow"""
    print("="*80)
    print("ZOOM OAUTH HELPER - GET ACCESS TOKEN")
    print("="*80)
    
    # Get Client ID and Client Secret
    print("\nBefore starting, make sure you have:")
    print("1. Created a Zoom OAuth app at https://marketplace.zoom.us/")
    print("2. Added the required scopes:")
    print("   - team_chat:read:list_user_messages")
    print("   - team_chat:update:message_emoji")
    print("   - team_chat:read:list_user_channels")
    print("   - user:read:user")
    print("3. Set the redirect URI to: http://localhost:3000")
    print()
    
    client_id = input("Enter your Zoom OAuth Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required!")
        return
    
    client_secret = input("Enter your Zoom OAuth Client Secret: ").strip()
    if not client_secret:
        print("Error: Client Secret is required!")
        return
    
    # Configuration
    redirect_uri = "http://localhost:3000"
    port = 3000
    
    # Build authorization URL
    scopes = [
        "team_chat:read:list_user_messages",
        "team_chat:update:message_emoji",
        "team_chat:read:list_user_channels",
        "user:read:user"
    ]
    scope_string = " ".join(scopes)
    
    auth_url = (
        f"https://zoom.us/oauth/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}"
    )
    
    print("\n" + "="*80)
    print("STEP 1: Starting local server...")
    print("="*80)
    
    # Start local server in a thread
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"✓ Local server started on {redirect_uri}")
    
    print("\n" + "="*80)
    print("STEP 2: Opening browser for authorization...")
    print("="*80)
    print(f"\nIf the browser doesn't open automatically, visit this URL:")
    print(f"\n{auth_url}\n")
    
    # Open browser
    try:
        webbrowser.open(auth_url)
        print("✓ Browser opened. Please authorize the app in your browser.")
    except:
        print("⚠ Could not open browser automatically. Please copy the URL above.")
    
    print("\n" + "="*80)
    print("STEP 3: Waiting for authorization...")
    print("="*80)
    print("(Waiting for you to authorize the app in your browser...)")
    
    # Wait for the authorization code
    server_thread.join(timeout=300)  # Wait up to 5 minutes
    
    if not OAuthCallbackHandler.authorization_code:
        print("\n✗ Error: No authorization code received. Please try again.")
        server.server_close()
        return
    
    print("✓ Authorization code received!")
    
    print("\n" + "="*80)
    print("STEP 4: Exchanging code for access token...")
    print("="*80)
    
    try:
        token_data = exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=OAuthCallbackHandler.authorization_code,
            redirect_uri=redirect_uri
        )
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 0)
        
        if not access_token:
            print("\n✗ Error: No access token received in response")
            return
        
        print("✓ Access token obtained!")
        print(f"\nAccess Token: {access_token[:20]}...{access_token[-20:]}")
        print(f"Expires in: {expires_in // 3600} hours")
        
        if refresh_token:
            print(f"Refresh Token: {refresh_token[:20]}...{refresh_token[-20:]}")
        
        # Save to .env file
        save_to_env_file(access_token, refresh_token or "")
        
        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print("\nYou can now run the emoji sender:")
        print("  python zoom_emoji_sender.py")
        print("\nNote: Access tokens typically expire after 1 hour.")
        print("      You'll need to run this script again to get a new token.")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Error exchanging code for token:")
        print(f"   {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
    finally:
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
