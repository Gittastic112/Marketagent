FROM postgres:16.15-trixie@sha256:f9a7b9ebf6f56201f949db745e47bc423c0f0f8294bafe991cc10bf74b029657

# Keep the reviewed PostgreSQL binaries; update only signed Debian OS packages.
# Exclude the rolling PGDG repository from this dated security rebuild.
RUN dpkg --compare-versions "$(dpkg-query -W -f='${Version}' apt)" ge 3.0.4 \
    && rm -f /etc/apt/sources.list.d/pgdg.list /etc/apt/sources.list.d/pgdg.sources \
    && sed -i 's|http://deb.debian.org/debian-security|http://snapshot.debian.org/archive/debian-security/20261107T180000Z|;s|http://deb.debian.org/debian|http://snapshot.debian.org/archive/debian/20261107T180000Z|' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o APT::Update::Error-Mode=any -o Acquire::Check-Valid-Until=false -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 update \
    && DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 upgrade -y --no-install-recommends \
    && apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 install -y --no-install-recommends ca-certificates \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' apt)" ge 3.0.4 \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' zlib1g)" ge '1:1.3.dfsg+really1.3.1-1+deb13u1' \
    && sed -i 's|http://snapshot.debian.org|https://snapshot.debian.org|' /etc/apt/sources.list.d/debian.sources \
    && rm -rf /var/lib/apt/lists/*
