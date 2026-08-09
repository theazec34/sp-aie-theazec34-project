# Brasaland Digital — single container for website (3000) + backoffice (3001)
FROM node:20-alpine

WORKDIR /app

# Install dependencies for each Next.js app separately
COPY website/package.json website/package-lock.json ./website/
COPY backoffice/package.json backoffice/package-lock.json ./backoffice/

RUN cd /app/website && npm ci
RUN cd /app/backoffice && npm ci

# App sources (compose bind-mounts override these for hot reload)
COPY website ./website
COPY backoffice ./backoffice
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV NODE_ENV=development
ENV WATCHPACK_POLLING=true
ENV CHOKIDAR_USEPOLLING=true

EXPOSE 3000 3001

CMD ["/start.sh"]
