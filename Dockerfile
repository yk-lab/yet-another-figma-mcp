# syntax=docker/dockerfile:1

# Build stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy all project files (needed for hatch-vcs version detection)
COPY . .

# Set fallback version for builds without git history
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}

# Install dependencies and the package
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

# Health check - verify CLI is functional (stdio-based server, no HTTP endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["yet-another-figma-mcp", "--help"]

ENTRYPOINT ["yet-another-figma-mcp"]
CMD ["serve"]
