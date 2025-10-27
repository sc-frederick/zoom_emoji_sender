#!/usr/bin/env python3
"""
Zoom Emoji Sender - Send multiple emoji reactions to a Zoom Team Chat message

This script allows you to spam a Zoom message with emoji reactions using the Zoom API.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time
from pathlib import Path
import random


def emoji_to_unicode(emoji: str) -> str:
    """
    Convert emoji to Unicode format (e.g., "😀" -> "U+1F600")
    
    Args:
        emoji: Emoji character
        
    Returns:
        Unicode string in format "U+XXXX" or "U+XXXX-U+YYYY" for multi-codepoint emojis
    """
    # Get Unicode codepoints for the emoji
    codepoints = [f"{ord(char):X}" for char in emoji]
    
    # Join multiple codepoints with hyphen (for complex emojis like flags)
    if len(codepoints) == 1:
        return f"U+{codepoints[0]}"
    else:
        return "-".join([f"U+{cp}" for cp in codepoints])


class ZoomEmojiSender:
    """Handle Zoom API interactions for sending emoji reactions"""
    
    BASE_URL = "https://api.zoom.us/v2"
    
    def __init__(self, access_token: str):
        """
        Initialize the Zoom Emoji Sender
        
        Args:
            access_token: Your Zoom OAuth access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def _handle_response(self, response: requests.Response) -> None:
        """
        Handle API response and check for errors
        
        Args:
            response: The requests Response object
            
        Raises:
            HTTPError: If the response status is not successful
        """
        if response.status_code == 204:
            # No content response is valid
            return
        
        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get('message', 'Unknown error')
                error_code = error_data.get('code', response.status_code)
                raise requests.exceptions.HTTPError(
                    f"Zoom API Error {error_code}: {error_message}",
                    response=response
                )
            except (ValueError, KeyError):
                # If we can't parse the error, use default
                response.raise_for_status()
    
    def _handle_api_error(self, error: requests.exceptions.HTTPError) -> None:
        """
        Log detailed API error information
        
        Args:
            error: The HTTPError exception
        """
        if hasattr(error, 'response') and error.response is not None:
            try:
                error_data = error.response.json()
                print(f"API Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"API Error: {error}")
    
    def get_user_id(self) -> str:
        """
        Get the current user's ID
        
        Returns:
            User ID string
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/users/me",
                headers=self.headers
            )
            self._handle_response(response)
            return response.json()["id"]
        except requests.exceptions.HTTPError as e:
            self._handle_api_error(e)
            raise
    
    def list_chat_channels(self, user_id: str, page_size: int = 50) -> List[Dict]:
        """
        List all chat channels for the user with pagination support
        
        Args:
            user_id: The user's ID
            page_size: Number of channels to retrieve per page
            
        Returns:
            List of channel dictionaries
        """
        all_channels = []
        next_page_token = None
        
        while True:
            params = {"page_size": page_size}
            if next_page_token:
                params["next_page_token"] = next_page_token
            
            try:
                response = requests.get(
                    f"{self.BASE_URL}/chat/users/{user_id}/channels",
                    headers=self.headers,
                    params=params
                )
                self._handle_response(response)
                data = response.json()
                
                all_channels.extend(data.get("channels", []))
                next_page_token = data.get("next_page_token")
                
                if not next_page_token:
                    break
            except requests.exceptions.HTTPError as e:
                self._handle_api_error(e)
                raise
        
        return all_channels
    
    def list_recent_messages(
        self, 
        user_id: str, 
        to_contact: Optional[str] = None,
        to_channel: Optional[str] = None,
        page_size: int = 50,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """
        List recent chat messages with pagination support
        
        Args:
            user_id: The user's ID
            to_contact: Email or user ID of contact (for 1-on-1 chats)
            to_channel: Channel ID (for channel messages)
            page_size: Number of messages to retrieve per page
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            List of message dictionaries
        """
        all_messages = []
        next_page_token = None
        
        while True:
            params: Dict[str, Any] = {
                "page_size": page_size
            }
            
            if to_contact:
                params["to_contact"] = to_contact
            if to_channel:
                params["to_channel"] = to_channel
            if date_from:
                params["from"] = date_from
            if date_to:
                params["to"] = date_to
            if next_page_token:
                params["next_page_token"] = next_page_token
            
            try:
                response = requests.get(
                    f"{self.BASE_URL}/chat/users/{user_id}/messages",
                    headers=self.headers,
                    params=params
                )
                self._handle_response(response)
                data = response.json()
                
                all_messages.extend(data.get("messages", []))
                next_page_token = data.get("next_page_token")
                
                if not next_page_token:
                    break
            except requests.exceptions.HTTPError as e:
                self._handle_api_error(e)
                raise
        
        return all_messages
    
    def add_emoji_reaction(
        self,
        user_id: str,
        message_id: str, 
        emoji: str,
        action: str = "add",
        to_contact: Optional[str] = None,
        to_channel: Optional[str] = None
    ) -> Dict:
        """
        Add an emoji reaction to a message
        
        Args:
            user_id: The user's ID (use "me" for current user)
            message_id: The message ID to react to
            emoji: The emoji to add (e.g., "😀", "👍", "❤️")
            action: "add" or "remove"
            to_contact: Email or user ID of contact (for 1-on-1 chats)
            to_channel: Channel ID (for channel messages)
            
        Returns:
            Response dictionary
        """
        # Prepare request body
        # Convert emoji to Unicode format (e.g., "😀" -> "U+1F600")
        emoji_unicode = emoji_to_unicode(emoji)
        data = {
            "action": action,
            "emoji": emoji_unicode
        }
        
        # Add to_contact or to_channel to the request body (required by API)
        if to_contact:
            data["to_contact"] = to_contact
        if to_channel:
            data["to_channel"] = to_channel
        
        try:
            response = requests.patch(
                f"{self.BASE_URL}/chat/users/{user_id}/messages/{message_id}/emoji_reactions",
                headers=self.headers,
                json=data
            )
            self._handle_response(response)
            
            # Handle 204 No Content response
            if response.status_code == 204:
                return {"success": True, "emoji": emoji, "emoji_unicode": emoji_unicode}
            
            result = response.json()
            result["emoji"] = emoji  # Keep original emoji for display
            return result
        except requests.exceptions.HTTPError as e:
            self._handle_api_error(e)
            raise
    
    def spam_emojis(
        self,
        user_id: str,
        message_id: str, 
        emojis: List[str],
        delay: float = 1.0,
        to_contact: Optional[str] = None,
        to_channel: Optional[str] = None,
        max_retries: int = 3
    ) -> List[Dict]:
        """
        Send multiple emoji reactions to a message
        
        Rate limits: 2 requests/second, 2000 requests/day
        
        Args:
            user_id: The user's ID (use "me" for current user)
            message_id: The message ID to react to
            emojis: List of emojis to send
            delay: Delay in seconds between each emoji (default 1.0s = 1 req/sec to stay under 2/sec limit)
            to_contact: Email or user ID of contact (for 1-on-1 chats)
            to_channel: Channel ID (for channel messages)
            max_retries: Maximum number of retries for failed requests
            
        Returns:
            List of response dictionaries
        """
        results = []
        
        for emoji in emojis:
            success = False
            retry_count = 0
            
            while not success and retry_count <= max_retries:
                try:
                    result = self.add_emoji_reaction(
                        user_id, 
                        message_id, 
                        emoji,
                        to_contact=to_contact,
                        to_channel=to_channel
                    )
                    results.append({"emoji": emoji, "success": True, "response": result})
                    retry_msg = f" (retry {retry_count})" if retry_count > 0 else ""
                    print(f"✓ Added {emoji}{retry_msg}")
                    success = True
                    time.sleep(delay)
                    
                except requests.exceptions.HTTPError as e:
                    error_code = str(e)
                    
                    # Handle rate limiting (429)
                    if "429" in error_code:
                        retry_count += 1
                        if retry_count <= max_retries:
                            wait_time = delay * (2 ** retry_count)  # Exponential backoff
                            print(f"⚠ Rate limited, waiting {wait_time:.1f}s before retry {retry_count}/{max_retries}...")
                            time.sleep(wait_time)
                        else:
                            results.append({
                                "emoji": emoji, 
                                "success": False, 
                                "error": str(e)
                            })
                            print(f"✗ Failed to add {emoji} after {max_retries} retries: {e}")
                    
                    # Handle internal errors (5301)
                    elif "5301" in error_code:
                        retry_count += 1
                        if retry_count <= max_retries:
                            wait_time = delay * 2
                            print(f"⚠ Internal error, waiting {wait_time:.1f}s before retry {retry_count}/{max_retries}...")
                            time.sleep(wait_time)
                        else:
                            results.append({
                                "emoji": emoji, 
                                "success": False, 
                                "error": str(e)
                            })
                            print(f"✗ Failed to add {emoji} after {max_retries} retries: {e}")
                    
                    # Handle other errors (no retry)
                    else:
                        results.append({
                            "emoji": emoji, 
                            "success": False, 
                            "error": str(e)
                        })
                        print(f"✗ Failed to add {emoji}: {e}")
                        success = True  # Don't retry
                        time.sleep(delay)
        
        return results


def display_messages(messages: List[Dict]) -> None:
    """Display messages in a readable format"""
    print("\n" + "="*80)
    print("RECENT MESSAGES")
    print("="*80)
    
    for idx, msg in enumerate(messages, 1):
        timestamp = msg.get("date_time", "")
        sender = msg.get("sender", "Unknown")
        message_text = msg.get("message", "")[:100]  # Truncate long messages
        message_id = msg.get("id", "")
        
        print(f"\n[{idx}] ID: {message_id}")
        print(f"    From: {sender}")
        print(f"    Time: {timestamp}")
        print(f"    Message: {message_text}")
        if len(msg.get("message", "")) > 100:
            print("    ...")
    
    print("\n" + "="*80)


def load_zoom_emojis(file_path: str = "zoom_supported_emojis.txt") -> List[str]:
    """
    Load and parse emojis from the zoom_supported_emojis.txt file
    
    Args:
        file_path: Path to the emoji file (relative to script location)
        
    Returns:
        List of emoji strings
    """
    script_dir = Path(__file__).parent
    emoji_file = script_dir / file_path
    
    if not emoji_file.exists():
        print(f"Warning: {file_path} not found, using fallback emoji list")
        return get_popular_emojis()
    
    try:
        with open(emoji_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract all emojis from the file
        # Split by spaces and filter out empty strings
        emojis = []
        for char in content:
            # Check if character is an emoji (basic check for non-ASCII printable)
            if ord(char) > 127 and char not in ['\n', '\r', '\t', ' ']:
                emojis.append(char)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_emojis = []
        for emoji in emojis:
            if emoji not in seen:
                seen.add(emoji)
                unique_emojis.append(emoji)
        
        print(f"Loaded {len(unique_emojis)} unique emojis from {file_path}")
        return unique_emojis
    
    except Exception as e:
        print(f"Error loading emoji file: {e}")
        print("Using fallback emoji list")
        return get_popular_emojis()


def get_popular_emojis() -> List[str]:
    """Return a comprehensive list of popular emojis (fallback)"""
    return [
        # Smileys & Emotion
        "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂",
        "🙂", "🙃", "😉", "😊", "😇", "🥰", "😍", "🤩",
        "😘", "😗", "😚", "😙", "🥲", "😋", "😛", "😜",
        "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐",
        "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬",
        "🤥", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒",
        "🤕", "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵",
        "🤯", "🤠", "🥳", "🥸", "😎", "🤓", "🧐", "😕",
        "😟", "🙁", "☹️", "😮", "😯", "😲", "😳", "🥺",
        "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱",
        "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤",
        "😡", "😠", "🤬", "😈", "👿", "💀", "☠️", "💩",
        
        # Hand gestures
        "👍", "👎", "👊", "✊", "🤛", "🤜", "🤞", "✌️",
        "🤟", "🤘", "👌", "🤌", "🤏", "👈", "👉", "👆",
        "👇", "☝️", "👋", "🤚", "🖐️", "✋", "🖖", "👏",
        "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💅", "🤳",
        
        # Hearts & Symbols
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍",
        "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖",
        "💘", "💝", "💟", "☮️", "✝️", "☪️", "🕉️", "☸️",
        "✡️", "🔯", "🕎", "☯️", "☦️", "🛐", "⛎", "♈",
        
        # Symbols & Expressions
        "💯", "💥", "💫", "⭐", "🌟", "✨", "🔥", "💧",
        "💦", "💨", "🌈", "☀️", "🌤️", "⛅", "🌥️", "☁️",
        "🌦️", "🌧️", "⛈️", "🌩️", "🌨️", "❄️", "☃️", "⛄",
        "💨", "💫", "☄️", "💥", "🌪️", "🌊", "💧", "💦",
        
        # Celebrations & Activities
        "🎉", "🎊", "🎈", "🎁", "🎀", "🎂", "🍰", "🧁",
        "🏆", "🥇", "🥈", "🥉", "🏅", "🎖️", "🎗️", "🎟️",
        "🎫", "🎭", "🎨", "🎬", "🎤", "🎧", "🎼", "🎹",
        "🥁", "🎷", "🎺", "🎸", "🪕", "🎻", "🎲", "♟️",
        "🎯", "🎳", "🎮", "🎰", "🧩", "🪀", "🪁", "🎪",
        
        # Food & Drink
        "🍕", "🍔", "🍟", "🌭", "🍿", "🧈", "🧂", "🥚",
        "🍳", "🥞", "🧇", "🥓", "🥩", "🍗", "🍖", "🦴",
        "🌮", "🌯", "🫔", "🥙", "🧆", "🥚", "🍳", "🥘",
        "🍲", "🫕", "🥣", "🥗", "🍱", "🍘", "🍙", "🍚",
        "🍛", "🍜", "🍝", "🍠", "🍢", "🍣", "🍤", "🍥",
        
        # Animals & Nature
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼",
        "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🙈",
        "🙉", "🙊", "🐔", "🐧", "🐦", "🐤", "🐣", "🐥",
        "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄",
        "🐝", "🪱", "🐛", "🦋", "🐌", "🐞", "🐜", "🪰",
        
        # Sports & Games
        "⚽", "🏀", "🏈", "⚾", "🥎", "🎾", "🏐", "🏉",
        "🥏", "🎱", "🪀", "🏓", "🏸", "🏒", "🏑", "🥍",
        "🏏", "🪃", "🥅", "⛳", "🪁", "🏹", "🎣", "🤿",
        "🥊", "🥋", "🎽", "🛹", "🛼", "🛷", "⛸️", "🥌",
        
        # Travel & Places
        "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑",
        "🚒", "🚐", "🛻", "🚚", "🚛", "🚜", "🦯", "🦽",
        "🦼", "🛴", "🚲", "🛵", "🏍️", "🛺", "🚨", "🚔",
        "🚍", "🚘", "🚖", "🚡", "🚠", "🚟", "🚃", "🚋",
        
        # Objects
        "⌚", "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️",
        "🖲️", "🕹️", "🗜️", "💾", "💿", "📀", "📼", "📷",
        "📸", "📹", "🎥", "📽️", "🎞️", "📞", "☎️", "📟",
        "📠", "📺", "📻", "🎙️", "🎚️", "🎛️", "🧭", "⏱️",
        
        # Flags & Common Symbols
        "🏁", "🚩", "🎌", "🏴", "🏳️", "🏳️‍🌈", "🏳️‍⚧️", "🏴‍☠️",
        "✅", "❌", "❎", "➕", "➖", "➗", "✖️", "♾️",
        "💲", "💱", "™️", "©️", "®️", "〰️", "➰", "➿",
        "🔚", "🔙", "🔛", "🔝", "🔜", "✔️", "☑️", "🔘",
    ]


def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def main():
    """Main function to run the emoji sender"""
    print("="*80)
    print("ZOOM EMOJI SENDER")
    print("="*80)
    
    # Load .env file
    load_env_file()
    
    # Get access token from environment or user input
    access_token = os.environ.get("ZOOM_ACCESS_TOKEN")
    
    if not access_token:
        print("\nNo ZOOM_ACCESS_TOKEN found in environment variables.")
        print("Please enter your Zoom OAuth access token:")
        access_token = input("> ").strip()
    
    if not access_token:
        print("Error: Access token is required!")
        return
    
    # Initialize the sender
    sender = ZoomEmojiSender(access_token)
    
    try:
        # Get user ID
        print("\nFetching user information...")
        user_id = sender.get_user_id()
        print(f"User ID: {user_id}")
        
        # Option to view channels
        print("\nWould you like to:")
        print("1. View recent messages from all chats")
        print("2. View messages from a specific channel")
        print("3. Enter a message ID directly")
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        messages = []
        message_id = None
        to_channel = None
        to_contact = None
        
        if choice == "1":
            # Get recent messages from all channels
            print("\nFetching channels...")
            channels = sender.list_chat_channels(user_id)
            
            if not channels:
                print("No channels found!")
                return
            
            print(f"Found {len(channels)} channels. Fetching recent messages...")
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            # Fetch messages from all channels
            messages = []
            for channel in channels:
                try:
                    channel_messages = sender.list_recent_messages(
                        user_id=user_id,
                        to_channel=channel["id"],
                        page_size=10,
                        date_from=date_from
                    )
                    # Tag each message with its channel ID
                    for msg in channel_messages:
                        msg["_channel_id"] = channel["id"]
                    messages.extend(channel_messages)
                except Exception as e:
                    # Skip channels that error out
                    print(f"Warning: Could not fetch messages from {channel.get('name', 'Unknown')}: {e}")
                    continue
            
            if not messages:
                print("No recent messages found!")
                return
            
            # Sort by date (most recent first)
            messages.sort(key=lambda x: x.get("date_time", ""), reverse=True)
            
            # Limit to most recent 20 messages
            messages = messages[:20]
            
            # Display messages
            display_messages(messages)
            
            # Select message
            msg_num = input("\nEnter the message number to spam with emojis: ").strip()
            try:
                msg_idx = int(msg_num) - 1
                message_id = messages[msg_idx]["id"]
                to_channel = messages[msg_idx].get("_channel_id")
            except (ValueError, IndexError):
                print("Invalid message number!")
                return
        
        elif choice == "2":
            # List channels
            print("\nFetching channels...")
            channels = sender.list_chat_channels(user_id)
            
            if not channels:
                print("No channels found!")
                return
            
            print("\nAvailable channels:")
            for idx, channel in enumerate(channels, 1):
                print(f"[{idx}] {channel.get('name', 'Unnamed')} (ID: {channel.get('id', '')})")
            
            # Select channel
            channel_num = input("\nEnter channel number: ").strip()
            try:
                channel_idx = int(channel_num) - 1
                to_channel = channels[channel_idx]["id"]
            except (ValueError, IndexError):
                print("Invalid channel number!")
                return
            
            # Get messages from channel
            print(f"\nFetching messages from channel...")
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            messages = sender.list_recent_messages(
                user_id=user_id,
                to_channel=to_channel,
                page_size=20,
                date_from=date_from
            )
            
            if not messages:
                print("No messages found in this channel!")
                return
            
            # Display messages
            display_messages(messages)
            
            # Select message
            msg_num = input("\nEnter the message number to spam with emojis: ").strip()
            try:
                msg_idx = int(msg_num) - 1
                message_id = messages[msg_idx]["id"]
            except (ValueError, IndexError):
                print("Invalid message number!")
                return
        
        elif choice == "3":
            message_id = input("\nEnter the message ID: ").strip()
        
        else:
            print("Invalid choice!")
            return
        
        if not message_id:
            print("Error: No message ID provided!")
            return
        
        # Load emojis from file
        all_emojis = load_zoom_emojis()
        
        # Select emojis
        print("\nEmoji options:")
        print(f"1. Use all supported emojis ({len(all_emojis)} emojis)")
        print("2. Random selection (specify count)")
        print("3. Enter custom emojis")
        emoji_choice = input("\nEnter choice (1/2/3): ").strip()
        
        emojis = []
        
        if emoji_choice == "1":
            emojis = all_emojis
            print(f"\nUsing all {len(emojis)} supported emojis!")
        elif emoji_choice == "2":
            # Ask user for number of random emojis
            while True:
                count_input = input(f"\nHow many random emojis? (1-{len(all_emojis)}): ").strip()
                try:
                    count = int(count_input)
                    if 1 <= count <= len(all_emojis):
                        emojis = random.sample(all_emojis, count)
                        print(f"\nRandomly selected {count} emojis!")
                        print(f"Sample: {' '.join(emojis[:20])}" + (" ..." if len(emojis) > 20 else ""))
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(all_emojis)}")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        elif emoji_choice == "3":
            print("\nEnter emojis separated by spaces (e.g., 😀 😃 😄 👍 ❤️):")
            emoji_input = input("> ").strip()
            emojis = emoji_input.split()
            if not emojis:
                print("No emojis provided!")
                return
        else:
            print("Invalid choice!")
            return
        
        # Confirm
        print(f"\nAbout to send {len(emojis)} emoji reactions to message ID: {message_id}")
        print("Sample emojis:", " ".join(emojis[:10]))
        
        # Rate limit warning
        if len(emojis) > 2000:
            print(f"\n⚠️  WARNING: You're trying to send {len(emojis)} reactions.")
            print("    Daily rate limit is 2000 requests/day. This will exceed the limit!")
            print("    Consider reducing the number of emojis.")
        
        estimated_time = len(emojis) * 1.0 / 60  # minutes
        print(f"\nEstimated time: {estimated_time:.1f} minutes (rate limit: 1 req/sec)")
        
        confirm = input("\nProceed? (yes/no): ").strip().lower()
        
        if confirm not in ["yes", "y"]:
            print("Cancelled.")
            return
        
        # Send emojis
        print(f"\nSending {len(emojis)} emoji reactions...")
        print("-"*80)
        results = sender.spam_emojis(
            user_id, 
            message_id, 
            emojis,
            to_contact=to_contact,
            to_channel=to_channel
        )
        print("-"*80)
        
        # Summary
        success_count = sum(1 for r in results if r["success"])
        print(f"\n✓ Successfully sent {success_count}/{len(emojis)} emoji reactions!")
        
        if success_count < len(emojis):
            print(f"✗ Failed to send {len(emojis) - success_count} reactions")
    
    except requests.exceptions.HTTPError as e:
        print(f"\nAPI Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
