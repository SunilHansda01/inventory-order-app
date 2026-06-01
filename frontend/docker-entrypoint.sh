#!/bin/sh
set -e

cat >/usr/share/nginx/html/env.js <<EOF
window.__ENV__ = {
  API_BASE_URL: "${VITE_API_BASE_URL:-http://localhost:8000}"
};
EOF

exec nginx -g 'daemon off;'
