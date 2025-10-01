FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project config and uv.lock
COPY pyproject.toml uv.lock ./
# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ .

# Smithery will hit the Streamable HTTP endpoint; we listen on $PORT
ENV MCP_TRANSPORT=http
EXPOSE 8081

# Start the server
CMD ["uv", "run", "python", "weather.py"]