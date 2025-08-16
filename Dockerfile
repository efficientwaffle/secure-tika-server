# Use OpenJDK 11 as base image (required for Tika)
FROM openjdk:11-jre-slim

# Install system dependencies including OCR support
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    imagemagick \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Download specific Tika version (known to work)
RUN echo "=== Downloading Apache Tika 3.0.0 ===" && \
    wget --timeout=300 --tries=3 \
    "https://dlcdn.apache.org/tika/3.0.0/tika-server-3.0.0.jar" \
    -O tika-server.jar && \
    echo "Download completed. File info:" && \
    ls -lh tika-server.jar && \
    echo "=== Tika download completed ==="

# Verify the download worked
RUN echo "=== Verifying Tika installation ===" && \
    ls -la tika-server.jar && \
    echo "File size: $(du -h tika-server.jar | cut -f1)" && \
    echo "=== Tika verification completed ==="

# Copy Python requirements first (for better Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Configure ImageMagick for better document processing
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' /etc/ImageMagick-6/policy.xml || echo "ImageMagick policy update skipped"

# Create non-root user for security
RUN groupadd -r tikauser && useradd -r -g tikauser tikauser
RUN chown -R tikauser:tikauser /app
USER tikauser

# Expose port
EXPOSE 8080

# Health check (longer start period for Tika to fully initialize)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["python3", "app.py"]
