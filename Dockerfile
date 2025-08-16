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

# Download Apache Tika Server 3.2.2 (latest stable version)
RUN wget https://dlcdn.apache.org/tika/3.2.2/tika-server-3.2.2.jar -O tika-server.jar

# Verify the download worked
RUN ls -lh tika-server.jar

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["python3", "app.py"]
