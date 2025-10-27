#!/bin/bash
# Setup script for Zoom Emoji Sender

echo "=================================="
echo "Zoom Emoji Sender Setup"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed!"
    echo "Please install uv and try again."
    exit 1
fi

echo "uv found: $(uv --version)"
echo ""

# Install dependencies using uv
echo "Installing dependencies..."
uv pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Dependencies installed successfully!"
else
    echo ""
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Make the script executable
chmod +x zoom_emoji_sender.py

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Get your Zoom OAuth access token (see README.md)"
echo "2. Set it as an environment variable:"
echo "   export ZOOM_ACCESS_TOKEN='your_token_here'"
echo "3. Run the script:"
echo "   python3 zoom_emoji_sender.py"
echo ""
