# syntax=docker/dockerfile:1

# Build stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first for better cache utilization
COPY pyproject.toml uv.lock ./

# Install dependencies only (without the package itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY src/ ./src/
COPY README.md LICENSE ./

# Install the package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Runtime stage
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create cache directory with correct permissions
RUN mkdir -p /home/app/.yet_another_figma_mcp && \
    chown -R app:app /home/app/.yet_another_figma_mcp

# Switch to non-root user
USER app

# Default cache directory
ENV YET_ANOTHER_FIGMA_MCP_CACHE_DIR=/home/app/.yet_another_figma_mcp

# Expose no ports by default (stdio-based MCP server)

ENTRYPOINT ["yet-another-figma-mcp"]
CMD ["serve"]
