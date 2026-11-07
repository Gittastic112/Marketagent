FROM node:24-slim@sha256:0e0ff40c39bc087845bfb27465a0df4ea419520094bc35842ff83dd8cbe6f9b6 AS base

# Disable HTTP download retries until APT is patched for CVE-2026-109518.
# Debian signatures remain required while bootstrapping the CA certificate store.
RUN sed -i 's|http://deb.debian.org/debian-security|http://snapshot.debian.org/archive/debian-security/20261107T180000Z|;s|http://deb.debian.org/debian|http://snapshot.debian.org/archive/debian/20261107T180000Z|' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o APT::Update::Error-Mode=any -o Acquire::Check-Valid-Until=false -o Acquire::Retries=0 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 update \
    && DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Retries=0 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 upgrade -y --no-install-recommends \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' apt)" ge 2.6.2 \
    && apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 install -y --no-install-recommends ca-certificates \
    && sed -i 's|http://snapshot.debian.org|https://snapshot.debian.org|' /etc/apt/sources.list.d/debian.sources \
    && rm -rf /var/lib/apt/lists/*

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app

FROM base AS deps

COPY package*.json ./
RUN npm ci --no-audit --no-fund && npm cache clean --force

FROM base AS builder

ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner

ENV HOSTNAME=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV PORT=3000
WORKDIR /app

RUN groupadd --system --gid 1001 nodejs \
    && useradd --system --uid 1001 --gid nodejs nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
