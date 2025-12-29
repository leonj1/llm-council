#!/bin/bash
set -e

# Check if we can run Tailscale (need /dev/net/tun)
if [ -e /dev/net/tun ] && [ -n "$TS_AUTHKEY" ]; then
    echo "Starting Tailscale daemon..."
    tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &

    # Wait for tailscaled to be ready
    sleep 2

    echo "Authenticating with Tailscale..."
    
    # Build tailscale up command with optional parameters
    TS_UP_ARGS="--authkey=$TS_AUTHKEY"
    
    # Set hostname if provided
    if [ -n "$TS_HOSTNAME" ]; then
        TS_UP_ARGS="$TS_UP_ARGS --hostname=$TS_HOSTNAME"
    fi
    
    tailscale up $TS_UP_ARGS
    
    # Show Tailscale status
    echo "Tailscale connected!"
    tailscale status
    
    # If TS_SERVE is enabled, set up Tailscale Serve for port 8001
    if [ "$TS_SERVE" = "true" ]; then
        echo "Setting up Tailscale Serve on port 8001..."
        tailscale serve --bg 8001
    fi
elif [ -n "$TS_AUTHKEY" ]; then
    echo "WARNING: /dev/net/tun not available. Skipping Tailscale."
    echo "This is normal for cloud platforms like Railway."
else
    echo "Tailscale not configured (TS_AUTHKEY not set)."
fi

echo ""
echo "Starting LLM Council backend..."

# Use PORT env var if set (Railway sets this), otherwise default to 8001
APP_PORT=${PORT:-8001}
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port $APP_PORT
