#!/bin/sh

# Copy the template to the default conf location
cp /etc/nginx/conf.d/default.conf.template /etc/nginx/conf.d/default.conf

# Replace API URL placeholder in nginx configuration with actual environment variable
sed -i "s|FUNDUS_API_URL_PLACEHOLDER|$VITE_FUNDUS_API_URL|g" /etc/nginx/conf.d/default.conf

echo "Nginx configured with API URL: $VITE_FUNDUS_API_URL"

# Start nginx in the foreground
exec nginx -g 'daemon off;'
