# Zoom Emoji Sender

A Python script that allows you to send multiple emoji reactions to Zoom Team Chat messages using the Zoom API.

## Features

- List recent chat messages from all your chats
- Browse messages from specific channels
- Send mass emoji reactions to any message
- Choose from 70+ popular emojis or provide custom ones
- Rate limiting protection with configurable delays

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Zoom OAuth Access Token

You need to create a Zoom OAuth app and get an access token. Here's how:

#### Step 1: Create a Zoom OAuth App

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us/)
2. Click "Develop" → "Build App"
3. Choose "OAuth" app type
4. Fill in basic information:
   - App Name: "Emoji Sender"
   - Short Description: "Send emoji reactions to chat messages"
   - Company Name: Your name
5. Set OAuth redirect URL (for testing, you can use `http://localhost:3000`)

#### Step 2: Configure Scopes

In the Scopes tab, add the following scopes:
- `team_chat:read:list_user_messages` - To read chat messages
- `team_chat:update:message_emoji` - To send emoji reactions
- `team_chat:read:list_user_channels` - To list channels
- `user:read:user` - To get user information

**Note**: These are the Team Chat scopes. The older `chat_message:*` scopes have been replaced with `team_chat:*` scopes in newer Zoom apps.

#### Step 3: Note Your Client ID and Client Secret

1. In your app's dashboard, find the "App Credentials" section
2. Copy your **Client ID** and **Client Secret**
3. You'll need these when running the `get_access_token.py` script (see Setup step 3 below)

### 3. Get Your Access Token

**Important:** Before running the helper script, you must set your redirect URI in your Zoom app:
1. Go to https://marketplace.zoom.us/
2. Open your OAuth app
3. Find the "Redirect URL for OAuth" or "OAuth Redirect URLs" setting
4. Add: `http://localhost:3000`
5. Save your changes

Now run the OAuth helper script:

```bash
python get_access_token.py
```

This interactive script will:
1. Ask for your Client ID and Client Secret
2. Open your browser to authorize the app
3. Automatically catch the authorization code
4. Exchange it for an access token
5. Save the token to a `.env` file

The access token will be automatically loaded by `zoom_emoji_sender.py` from the `.env` file.

**Note:** Access tokens typically expire after 1 hour. When it expires, simply run `get_access_token.py` again to get a new one.

## Usage

Run the script:

```bash
python zoom_emoji_sender.py
```

The script will guide you through:

1. **Authentication**: Enter your access token if not set as environment variable
2. **Message Selection**: Choose how to find the message:
   - View recent messages from all chats
   - Browse a specific channel
   - Enter a message ID directly
3. **Emoji Selection**: Choose emojis to send:
   - Use all 70+ popular emojis
   - Enter custom emojis (space-separated)
4. **Confirmation**: Review and confirm before sending

### Example Session

```
================================================================================
ZOOM EMOJI SENDER
================================================================================

Fetching user information...
User ID: abc123xyz

Would you like to:
1. View recent messages from all chats
2. View messages from a specific channel
3. Enter a message ID directly

Enter choice (1/2/3): 1

Fetching recent messages...

================================================================================
RECENT MESSAGES
================================================================================

[1] ID: msg_abc123
    From: john@example.com
    Time: 2025-10-27T10:30:00Z
    Message: Hey everyone, great meeting today!

[2] ID: msg_def456
    From: jane@example.com
    Time: 2025-10-27T09:15:00Z
    Message: Don't forget about the deadline tomorrow!

================================================================================

Enter the message number to spam with emojis: 1

Emoji options:
1. Use all popular emojis (70+ emojis)
2. Select custom emojis

Enter choice (1/2): 1

Using 70 popular emojis!

About to send 70 emoji reactions to message ID: msg_abc123
Sample emojis: 😀 😃 😄 😁 😆 😅 🤣 😂 🙂 🙃

Proceed? (yes/no): yes

Sending 70 emoji reactions...
--------------------------------------------------------------------------------
✓ Added 😀
✓ Added 😃
✓ Added 😄
...
--------------------------------------------------------------------------------

✓ Successfully sent 70/70 emoji reactions!
```

## API Endpoints Used

The script uses the following Zoom API endpoints:

- `GET /v2/users/me` - Get current user information
- `GET /v2/team_chat/users/{userId}/channels` - List chat channels
- `GET /v2/team_chat/users/{userId}/messages` - List chat messages
- `PATCH /v2/team_chat/users/{userId}/messages/{messageId}/emoji_reactions` - Add/remove emoji reactions

## Rate Limiting

The script includes a configurable delay (default 0.5 seconds) between emoji reactions to avoid hitting Zoom's API rate limits. Zoom API rate limits vary by endpoint:
- Heavy endpoints: 1 request/second
- Medium endpoints: 10 requests/second
- Light endpoints: 100 requests/second

The emoji reaction endpoint is typically classified as "Medium" tier, so the default 0.5s delay is conservative and safe. You can adjust this in the `spam_emojis()` method if needed, but be aware of rate limiting consequences.

## Features & Enhancements

### Pagination Support
The script automatically handles pagination for both channels and messages, retrieving all available results across multiple pages.

### Enhanced Error Handling
Detailed error messages from the Zoom API are captured and displayed, making debugging easier when issues occur.

### Response Validation
The script properly handles various response types including empty responses (204 No Content) and JSON responses.

## Troubleshooting

### "Access token is required!"
Make sure you've either set the `ZOOM_ACCESS_TOKEN` environment variable or enter it when prompted.

### "401 Unauthorized"
Your access token may have expired. Zoom OAuth tokens typically expire after 1 hour. Generate a new token.

### "403 Forbidden"
Your app may not have the required scopes. Double-check that you've added all necessary scopes in your Zoom app settings.

### "404 Not Found"
The message ID may be invalid or you may not have access to that message.

### Rate Limit Errors
If you encounter rate limit errors, increase the delay parameter in the `spam_emojis()` call.

## Notes

- Emoji reactions are added individually, so sending 70 emojis will make 70 API calls
- The script respects rate limits with built-in delays
- Access tokens expire - you'll need to refresh them periodically
- You can only react to messages you have access to (in your channels/conversations)

## Disclaimer

Use this script responsibly! Spamming emojis may annoy your colleagues. This tool is intended for fun and testing purposes.

## License

MIT License - feel free to modify and use as needed!
