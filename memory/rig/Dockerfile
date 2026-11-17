FROM sha256:94b391782aa042272956ee8d4c6ccbdb75bd00d36648d97e08145be1b19b1739 AS engines
FROM sha256:7e44291716e341b3c0426e6d740a581e073fe0076d177a0a2b155f9fd9a3f3ca
USER 0:0
COPY --from=engines /opt/headless/bin/lightpanda /opt/headless/bin/obscura /opt/headless/bin/obscura-worker /opt/headless/bin/moli /opt/headless/bin/
COPY rig/ /opt/rig/
COPY wpt/ /opt/wpt/
COPY demo-root/ /opt/demo/
RUN python3 /opt/rig/IMAGE_CHECK.py --root /opt/headless --manifest /opt/rig/ENGINE_BINARIES.json
RUN mkdir -p /opt/rig/bin && ln -s /ms-playwright/ffmpeg-1011/ffmpeg-linux /opt/rig/bin/ffmpeg && cat /etc/ssl/certs/ca-certificates.crt /opt/wpt/tools/certs/cacert.pem > /opt/rig/ca-bundle.pem
LABEL rig.fixture="1"
USER 1000:1000
WORKDIR /tmp
ENV PYTHONDONTWRITEBYTECODE=1 SSL_CERT_FILE=/opt/rig/ca-bundle.pem CURL_CA_BUNDLE=/opt/rig/ca-bundle.pem
ENTRYPOINT ["/usr/bin/python3", "/opt/rig/ENTRY.py"]
