ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE}

# Install common dev tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Agent tools layer — workspace utilities
RUN mkdir -p /workspace/.aoc

WORKDIR /workspace

# Keep container alive for exec commands from orchestrator
CMD ["tail", "-f", "/dev/null"]
