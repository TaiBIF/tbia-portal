#!/bin/sh

echo "🕒 Waiting for static files to be available..."

while [ ! -f /tbia-volumes/static/css/base.css ]; do
    echo "⏳ Waiting for /tbia-volumes/static..."
    sleep 1
done

echo "✅ Static files ready. Starting nginx..."
exec nginx -g "daemon off;"