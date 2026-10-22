# syntax=docker/dockerfile:1

# Étape 1 : build Angular (même version de Node que la CI)
FROM node:20.20.2-alpine3.23 AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# Étape 2 : fichiers statiques servis par Caddy en HTTPS
FROM caddy:2.11-alpine
# Création user non root avec accès à /data (certificats de l'autorité interne) et /config (configuration sauvegardée)
RUN addgroup -S web && adduser -S -D -H -G web web \
    && chown -R web:web /data /config
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist/microcrm/browser /srv
USER web
# Sonde en HTTPS, mais certificat de l'autorité interne non vérifiable
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null --no-check-certificate https://localhost/ || exit 1
# Ports hérités de l'image officielle : 80 443 443/udp
# CMD hérité de l'image officielle : caddy run --config /etc/caddy/Caddyfile
