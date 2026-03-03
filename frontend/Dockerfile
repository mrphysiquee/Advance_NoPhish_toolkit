# Simple nginx server for static frontend
FROM nginx:alpine

# Copy static files
COPY build/ /usr/share/nginx/html/
COPY nginx-simple.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]