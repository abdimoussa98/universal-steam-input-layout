# Match the Ubuntu/Chrome pair used by the browser workflow. Run with
# --platform linux/amd64 on Apple Silicon; mount only the overlay directory.
FROM ubuntu:24.04
ARG CHROME_VERSION=155.0.8059.84
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl unzip python3 fonts-liberation \
    libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 \
    libcups2t64 libdrm2 libgbm1 libgtk-3-0t64 libnss3 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" -o /tmp/chrome.zip \
    && curl -fsSL "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" -o /tmp/driver.zip \
    && unzip -q /tmp/chrome.zip -d /opt \
    && unzip -q /tmp/driver.zip -d /opt \
    && rm /tmp/chrome.zip /tmp/driver.zip
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
ENTRYPOINT ["python3", "-u", "overlay/scripts/browser_smoke.py", "--bundle", "overlay/dist", "--webhid", "--driver", "/opt/chromedriver-linux64/chromedriver", "--browser-binary", "/opt/chrome-linux64/chrome"]
