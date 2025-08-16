# Use the official Apache Tika full Docker image
FROM apache/tika:3.2.2.0-full

# Install Python and dependencies
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create non-root user for security
RUN groupadd -r tikauser && useradd -r -g tikauser tikauser
RUN chown -R tikauser:tikauser /app

# Switch to non-root user
USER tikauser

# Expose port for our Flask app
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start our Flask app (Tika server is already running in the base image)
CMD ["python3", "app.py"]
