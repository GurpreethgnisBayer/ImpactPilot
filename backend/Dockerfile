FROM python:3.12-slim

WORKDIR /app

# DejaVu gives the PDF export full Unicode text (dashes, quotes, euro sign).
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/impactpilot /app/backend/impactpilot
COPY config /app/config

RUN pip install --no-cache-dir \
    fastapi "uvicorn[standard]" sqlalchemy alembic pydantic pydantic-settings \
    pyyaml requests python-dotenv python-multipart markdown python-pptx fpdf2

ENV PYTHONPATH=/app/backend
ENV IMPACTPILOT_CONFIG_DIR=/app/config
ENV IMPACTPILOT_DB_URL=sqlite:////app/data/impactpilot.db

RUN mkdir -p /app/data
EXPOSE 5001
CMD ["uvicorn", "impactpilot.main:app", "--host", "0.0.0.0", "--port", "5001"]
