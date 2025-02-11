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
COPY control-scripts/ /app/control-scripts/
COPY lib /app/lib
COPY api /app/api

# Ensure scripts are executable
RUN chmod +x /app/control-scripts/*

# Expose port 8080
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/app/control-scripts/entrypoint.sh"]

