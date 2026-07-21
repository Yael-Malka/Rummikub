#!/bin/sh
# Generate the actual nginx.conf from the template
envsubst '${BACKEND_URL}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"
