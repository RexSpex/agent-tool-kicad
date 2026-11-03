# syntax=docker/dockerfile:1.7

ARG KONNECT_VERSION=0.13.0
ARG KONNECT_SHA256=9c9d28e7d905d8e8519339a78890193f252bc8134993349b40d80e3a67b93512

FROM ubuntu:24.04 AS konnect-amd64
ARG KONNECT_VERSION
ARG KONNECT_SHA256
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && \
    curl -fsSL "https://github.com/mixelpixx/Konnect/releases/download/v${KONNECT_VERSION}/konnect-v${KONNECT_VERSION}-x86_64-unknown-linux-gnu.tar.gz" -o /tmp/konnect.tar.gz && \
    echo "${KONNECT_SHA256}  /tmp/konnect.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/konnect.tar.gz -C /tmp konnect && \
    install -m 0755 /tmp/konnect /konnect

FROM rust:1.96.0-bookworm AS konnect-arm64
RUN apt-get update && apt-get install -y --no-install-recommends clang cmake libprotobuf-dev pkg-config protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /src/Konnect
COPY vendor/Konnect/ ./
ENV KONNECT_BUILD_COMMIT=6bbe3e4f890ba1d37c0e5d5f38ccd03d90958c9e
RUN cargo build --locked --release -p konnect && \
    install -m 0755 target/release/konnect /konnect

ARG TARGETARCH
FROM konnect-${TARGETARCH} AS konnect-dist

FROM eclipse-temurin:25-jre AS java-runtime

FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
ARG FREEROUTING_VERSION=2.3.0
ARG FREEROUTING_SHA256=3cf18d608437740bc497db6b8ef5888e2e60a08de0def20691d1bad0c0e0ee24
RUN apt-get -o Acquire::Retries=5 update && \
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends ca-certificates curl gnupg
COPY docker/kicad-ppa.asc /tmp/kicad-ppa.asc
RUN gpg --show-keys --with-colons /tmp/kicad-ppa.asc | grep -q 'FDA854F61C4D0D9572BB95E5245D5502FAD7A805' && \
    gpg --dearmor -o /usr/share/keyrings/kicad.gpg /tmp/kicad-ppa.asc && \
    echo 'deb [signed-by=/usr/share/keyrings/kicad.gpg] http://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu noble main' > /etc/apt/sources.list.d/kicad.list && \
    apt-get -o Acquire::Retries=5 update && \
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends kicad kicad-symbols kicad-footprints python3 xvfb x11vnc novnc websockify fluxbox supervisor nginx x11-utils xdotool fonts-dejavu && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/freerouting && \
    curl -fsSL "https://github.com/freerouting/freerouting/releases/download/v${FREEROUTING_VERSION}/freerouting-${FREEROUTING_VERSION}.jar" -o /opt/freerouting/freerouting.jar && \
    echo "${FREEROUTING_SHA256}  /opt/freerouting/freerouting.jar" | sha256sum -c -
COPY --from=konnect-dist /konnect /usr/local/bin/konnect
COPY --from=java-runtime /opt/java/openjdk /opt/java/openjdk
RUN usermod -l cad -d /home/cad -m ubuntu && groupmod -n cad ubuntu && mkdir -p /workspace /home/cad/.config /tmp/nginx && chown -R cad:cad /workspace /home/cad /tmp/nginx
COPY docker/ /opt/
ENV DISPLAY=:0 HOME=/home/cad XDG_RUNTIME_DIR=/tmp/runtime-cad LIBGL_ALWAYS_SOFTWARE=1 QT_X11_NO_MITSHM=1 \
    JAVA_HOME=/opt/java/openjdk PATH="/opt/java/openjdk/bin:${PATH}"
USER cad
WORKDIR /workspace
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s CMD ["python3", "/opt/healthcheck.py"]
CMD ["/bin/sh", "/opt/entrypoint.sh"]
LABEL org.opencontainers.image.title="agent-tool-kicad" org.opencontainers.image.licenses="AGPL-3.0" org.opencontainers.image.version="0.1.0"
COPY LICENSE UPSTREAM.md /usr/share/doc/agent-tool-kicad/

LABEL org.opencontainers.image.source="https://github.com/RexSpex/agent-tool-kicad"
