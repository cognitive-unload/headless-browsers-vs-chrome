FROM mcr.microsoft.com/playwright@sha256:9bd26ad900bb5e0f4dee75839e957a89ae89c2b7ab1e76050e559790e946b948
LABEL rig.fixture="1"
COPY --chown=1000:1000 runtime/ /opt/headless/
COPY --chown=1000:1000 SMOKE.py /opt/headless/SMOKE.py
ENV HOME=/home/pwuser PATH=/opt/headless/bin:/usr/local/bin:/usr/bin:/bin LIGHTPANDA_DISABLE_TELEMETRY=1 AGENT_BROWSER_NO_VERSION_CHECK=1
USER 1000:1000
WORKDIR /tmp
ENTRYPOINT ["/usr/bin/python3", "/opt/headless/SMOKE.py"]
