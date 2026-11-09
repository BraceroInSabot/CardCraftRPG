# syntax=docker/dockerfile:1

# ---- Build the static app -------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Same-origin API by default: Nginx below forwards /api to the backend.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---- Serve it with Nginx --------------------------------------------------
FROM nginx:1.27-alpine

# Rendered to /etc/nginx/conf.d/default.conf at start-up (envsubst on defined env vars only).
ENV BACKEND_URL=http://backend:8000
COPY docker/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
