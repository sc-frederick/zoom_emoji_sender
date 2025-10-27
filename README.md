# Zoom Emoji Sender

A Python script that allows you to send multiple emoji reactions to Zoom Team Chat messages using the Zoom API.

## Features

- List recent chat messages from all your chats
- Browse messages from specific channels
- Send mass emoji reactions to any message
- Choose from 2400+ Zoom-supported emojis loaded from external file
- Random emoji selection with customizable count
- Custom emoji input support
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
   - Use all supported emojis (2400+ from `zoom_supported_emojis.txt`)
   - Random selection (specify how many random emojis)
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

Loaded 2448 unique emojis from zoom_supported_emojis.txt

Emoji options:
1. Use all supported emojis (2448 emojis)
2. Random selection (specify count)
3. Enter custom emojis

Enter choice (1/2/3): 2

How many random emojis? (1-2448): 50

Randomly selected 50 emojis!
Sample: 🌀 🎨 🐻 💡 🚀 🎉 ⭐ 🔥 💯 🎯 ❤️ 🌈 🎵 🍕 🏆 🌺 🦋 ⚡ 🎭 🌟

About to send 50 emoji reactions to message ID: msg_abc123
Sample emojis: 🌀 🎨 🐻 💡 🚀 🎉 ⭐ 🔥 💯 🎯

Proceed? (yes/no): yes

Sending 50 emoji reactions...
--------------------------------------------------------------------------------
✓ Added 🌀
✓ Added 🎨
✓ Added 🐻
...
--------------------------------------------------------------------------------

✓ Successfully sent 50/50 emoji reactions!
```

## API Endpoints Used

The script uses the following Zoom API endpoints:

- `GET /v2/users/me` - Get current user information
- `GET /v2/team_chat/users/{userId}/channels` - List chat channels
- `GET /v2/team_chat/users/{userId}/messages` - List chat messages
- `PATCH /v2/team_chat/users/{userId}/messages/{messageId}/emoji_reactions` - Add/remove emoji reactions

## Rate Limiting

The script includes a configurable delay (default 1.0 seconds) between emoji reactions to avoid hitting Zoom's API rate limits. Zoom API rate limits vary by account type and endpoint tier:

| Rate Limit Type | Free | Pro | Business+ |
|----------------|------|-----|-----------|
| Light APIs | 4/second, 6000/day | 30/second | 80/second |
| Medium APIs | 2/second, 2000/day | 20/second | 60/second |
| Heavy APIs | 1/second, 1000/day | 10/second* | 40/second* |
| Resource-intensive APIs | 10/minute, 30,000/day | 10/minute* | 20/minute* |

The emoji reaction endpoint is classified as **Medium** tier. The default 1.0s delay (1 req/sec) is safe for Free accounts and conservative for Pro/Business+ accounts. 

**For Free accounts:**
- Maximum 2000 reactions per day
- Recommended delay: 1.0s (stays under 2/second limit)

**For Pro/Business+ accounts:**
- You can reduce the delay for faster sending
- Pro: Up to 20 reactions/second (0.05s delay)
- Business+: Up to 60 reactions/second (0.017s delay)

You can adjust the delay in the `spam_emojis()` method, but be aware of rate limiting consequences for your account tier.

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
