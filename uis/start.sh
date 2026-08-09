#!/bin/sh
# Launch both Next.js apps in one container (hot reload via next dev).
set -e

echo "[interfaces] Starting website on :3000 and backoffice on :3001"

cd /app/website
npx next dev -H 0.0.0.0 -p 3000 &
WEBSITE_PID=$!

cd /app/backoffice
npx next dev -H 0.0.0.0 -p 3001 &
BACKOFFICE_PID=$!

trap 'kill $WEBSITE_PID $BACKOFFICE_PID 2>/dev/null; wait' INT TERM

wait $WEBSITE_PID $BACKOFFICE_PID
