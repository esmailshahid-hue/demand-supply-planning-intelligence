FROM node:24-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHON=python HOST=0.0.0.0 PORT=8000
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 planner
COPY backend/ ./backend/
COPY scripts/start.sh scripts/smoke.py scripts/planning_smoke.py scripts/planning_profile.py scripts/scenario_smoke.py scripts/solver_smoke.py ./scripts/
COPY --from=frontend /build/frontend/dist ./frontend/dist
USER planner
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:'+__import__('os').environ.get('PORT','8000')+'/api/health',timeout=3)"
CMD ["./scripts/start.sh"]
