#!/bin/bash
set -e

# Run Flyway migrations if database is configured
# Support both Railway (DB_*) and local (MYSQL_*) env vars
FLYWAY_HOST="${DB_HOST:-$MYSQL_HOST}"
FLYWAY_PORT="${DB_PORT:-${MYSQL_PORT:-3306}}"
FLYWAY_DB="${DB_NAME:-$MYSQL_DATABASE}"
FLYWAY_USER="${DB_USER:-${MYSQL_USER:-root}}"
FLYWAY_PASS="${DB_PASSWORD:-${MYSQL_PASSWORD:-}}"

if [ -n "$FLYWAY_HOST" ] && [ -n "$FLYWAY_DB" ]; then
    echo "Running Flyway migrations..."

    # Build Flyway JDBC URL
    FLYWAY_URL="jdbc:mysql://${FLYWAY_HOST}:${FLYWAY_PORT}/${FLYWAY_DB}"

    # Run Flyway migrate
    flyway \
        -url="${FLYWAY_URL}" \
        -user="${FLYWAY_USER}" \
        -password="${FLYWAY_PASS}" \
        -locations="filesystem:/app/sql" \
        -connectRetries=5 \
        migrate

    echo "Flyway migrations completed."
else
    echo "Database not configured (DB_HOST/MYSQL_HOST or DB_NAME/MYSQL_DATABASE not set). Skipping Flyway migrations."
fi

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
    
    # If TS_SERVE is enabled, set up Tailscale Serve for port 8004
    if [ "$TS_SERVE" = "true" ]; then
        echo "Setting up Tailscale Serve on port 8004..."
        tailscale serve --bg 8004
    fi
elif [ -n "$TS_AUTHKEY" ]; then
    echo "WARNING: /dev/net/tun not available. Skipping Tailscale."
    echo "This is normal for cloud platforms like Railway."
else
    echo "Tailscale not configured (TS_AUTHKEY not set)."
fi

echo ""
echo "Starting LLM Council backend..."

# Use PORT env var if set (Railway sets this), otherwise default to 8004
APP_PORT=${PORT:-8004}
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port $APP_PORT
