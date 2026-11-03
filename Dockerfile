FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg
COPY docker/kicad-ppa.asc /tmp/kicad-ppa.asc
RUN gpg --show-keys --with-colons /tmp/kicad-ppa.asc | grep -q 'FDA854F61C4D0D9572BB95E5245D5502FAD7A805' && \
    gpg --dearmor -o /usr/share/keyrings/kicad.gpg /tmp/kicad-ppa.asc && \
    echo 'deb [signed-by=/usr/share/keyrings/kicad.gpg] https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu noble main' > /etc/apt/sources.list.d/kicad.list && \
    apt-get update && apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints python3 xvfb x11vnc novnc websockify fluxbox supervisor nginx x11-utils xdotool fonts-dejavu && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ARG KONNECT_VERSION=0.13.0
ARG KONNECT_SHA256=9c9d28e7d905d8e8519339a78890193f252bc8134993349b40d80e3a67b93512
RUN test "$(uname -m)" = x86_64 && curl -fsSL "https://github.com/mixelpixx/Konnect/releases/download/v${KONNECT_VERSION}/konnect-v${KONNECT_VERSION}-x86_64-unknown-linux-gnu.tar.gz" -o /tmp/konnect.tar.gz && \
    echo "${KONNECT_SHA256}  /tmp/konnect.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/konnect.tar.gz -C /usr/local/bin konnect && rm /tmp/konnect.tar.gz && chmod +x /usr/local/bin/konnect
RUN usermod -l cad -d /home/cad -m ubuntu && groupmod -n cad ubuntu && mkdir -p /workspace /home/cad/.config /tmp/nginx && chown -R cad:cad /workspace /home/cad /tmp/nginx
COPY docker/ /opt/
ENV DISPLAY=:0 HOME=/home/cad XDG_RUNTIME_DIR=/tmp/runtime-cad LIBGL_ALWAYS_SOFTWARE=1 QT_X11_NO_MITSHM=1
USER cad
WORKDIR /workspace
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s CMD ["python3", "/opt/healthcheck.py"]
CMD ["/bin/sh", "/opt/entrypoint.sh"]
LABEL org.opencontainers.image.title="agent-tool-kicad" org.opencontainers.image.licenses="AGPL-3.0" org.opencontainers.image.version="0.1.0"
COPY LICENSE UPSTREAM.md /usr/share/doc/agent-tool-kicad/

LABEL org.opencontainers.image.source="https://github.com/RexSpex/agent-tool-kicad"
