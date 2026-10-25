FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY sau_frontend/package*.json ./
RUN npm install --ignore-scripts --no-audit --no-fund
COPY sau_frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    OMNISOCIAL_ENV=production \
    OMNISOCIAL_AUTH_MODE=production \
    OMNISOCIAL_ENABLE_REAL_PUBLISH=0
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0 && \
    patchright install chromium --with-deps
COPY . .
COPY --from=frontend /build/dist/ /app/
RUN cp conf.example.py conf.py && \
    mkdir -p /app/db /app/videoFile /app/cookiesFile /app/cookies /app/logs && \
    useradd --system --home /app --shell /usr/sbin/nologin omnisocial && \
    chown -R omnisocial:omnisocial /app/db /app/videoFile /app/cookiesFile /app/cookies /app/logs && \
    chmod 700 /app/db /app/videoFile /app/cookiesFile /app/cookies /app/logs
USER omnisocial
EXPOSE 5409
CMD ["gunicorn", "--bind", "0.0.0.0:5409", "--workers", "1", "--threads", "8", "--timeout", "300", "sau_backend:app"]
