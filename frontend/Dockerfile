# Use the official nginx image as the base
FROM nginx:latest

# Self-signed SSL certificates

COPY ./ft_transcendence.42.crt /etc/nginx/cert/ft_transcendence.42.crt
COPY ./ft_transcendence.42.key /etc/nginx/cert/ft_transcendence.42.key

CMD ["nginx", "-g", "daemon off;"]

