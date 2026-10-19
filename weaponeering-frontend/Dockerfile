FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=/api
ARG VITE_BASE_PATH=/
ARG VITE_CESIUM_ION_TOKEN=
ARG APP_VERSION=dev-local
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_BASE_PATH=${VITE_BASE_PATH} \
    VITE_CESIUM_ION_TOKEN=${VITE_CESIUM_ION_TOKEN} \
    APP_VERSION=${APP_VERSION} \
    GIT_COMMIT=${GIT_COMMIT} \
    BUILD_DATE=${BUILD_DATE}

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

ENV API_UPSTREAM=http://api:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1

COPY devops/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
