# Use the official nginx image as the base
FROM nginx:latest

# Install OpenSSL to create self-signed certificates
# RUN apt-get update && \
#     apt-get install -y openssl

# Create a directory for the SSL certificates
# RUN mkdir /etc/nginx/cert

# Generate self-signed SSL certificates
# RUN openssl req -newkey rsa:4096 -x509 -days 365 -nodes \
#     -out /etc/nginx/cert/ft_transcendence.42.crt \
#     -keyout /etc/nginx/cert/ft_transcendence.42.key \
#     -subj "/C=TH/ST=BKK/L=BKK/O=42 Bangkok/CN=ft_transcendence.42.fr/"
COPY ./ft_transcendence.42.crt /etc/nginx/cert/ft_transcendence.42.crt
COPY ./ft_transcendence.42.key /etc/nginx/cert/ft_transcendence.42.key


CMD ["nginx", "-g", "daemon off;"]
# Copy the nginx configuration file
# COPY ../nginx/default.conf /etc/nginx/conf.d

# Copy the frontend application files
# COPY ./frontend /frontend
