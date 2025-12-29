#!/bin/bash
set -e

# Start Tailscale daemon
echo "Starting Tailscale daemon..."
tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &

# Wait for tailscaled to be ready
sleep 2

# Authenticate with Tailscale if auth key is provided
if [ -n "$TS_AUTHKEY" ]; then
    echo "Authenticating with Tailscale..."
    
    # Build tailscale up command with optional parameters
    TS_UP_ARGS="--authkey=$TS_AUTHKEY"
    
    # Set hostname if provided
    if [ -n "$TS_HOSTNAME" ]; then
        TS_UP_ARGS="$TS_UP_ARGS --hostname=$TS_HOSTNAME"
    fi
    
    # Enable Tailscale Serve if requested (exposes port 8001 to tailnet)
    if [ "$TS_SERVE" = "true" ]; then
        TS_UP_ARGS="$TS_UP_ARGS"
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
else
    echo "WARNING: TS_AUTHKEY not set. Tailscale will not connect."
    echo "Set TS_AUTHKEY environment variable to enable Tailscale."
fi

echo ""
echo "Starting LLM Council backend..."
exec python -m backend.main
