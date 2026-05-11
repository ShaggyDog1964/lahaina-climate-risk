FROM python:3.13-slim

LABEL org.opencontainers.image.title="lahaina-climate-risk-api" \
      org.opencontainers.image.description="Lahaina climate-risk spatial results API" \
      org.opencontainers.image.source="https://github.com/noahkoikesmith/lahaina-climate-risk"

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml ./

# Copy source before install so the editable install resolves correctly
COPY src/ ./src/

# Install project dependencies
RUN uv pip install --system -e .

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
