# Start from Ubuntu 24.04
FROM ubuntu:24.04

# Set non-interactive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary apt packages
RUN apt-get update && apt-get install -y \
    curl \
    python3-dask \
    python3-flask \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy scripts into the container
COPY control-scripts/ /app/scripts/
COPY lib /app/lib
COPY api /app/api

# Ensure scripts are executable
RUN chmod +x /app/control-scripts/*

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

