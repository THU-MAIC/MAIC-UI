# Backend Dockerfile - Optimized for China
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Use Chinese Debian mirror (Tsinghua) for faster downloads
RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g; s|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list; \
    fi; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g; s|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get install -y --no-install-recommends \
      gcc \
      g++ \
      curl \
      libreoffice-nogui \
      fonts-noto-cjk \
      fonts-wqy-microhei \
      fonts-wqy-zenhei; \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and use Chinese mirror
RUN pip3 install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY requirements.txt .

# Install Python dependencies with Chinese mirror
RUN pip3 install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --retries 3 --timeout 300 \
    -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory for PDF processing
RUN mkdir -p uploads

# Create .env file from template if it doesn't exist
RUN if [ ! -f .env ]; then \
    echo 'DATABASE_URL=sqlite:///./learn_your_way.db' > .env && \
    echo 'SECRET_KEY=your-super-secret-key-change-this-in-production' >> .env && \
    echo 'ALGORITHM=HS256' >> .env && \
    echo 'ACCESS_TOKEN_EXPIRE_MINUTES=1440' >> .env && \
    echo 'MAX_FILE_SIZE=50MB' >> .env && \
    echo 'UPLOAD_DIR=./uploads' >> .env && \
    echo 'ENVIRONMENT=production' >> .env && \
    echo 'DEBUG=false' >> .env && \
    echo 'PORT=8000' >> .env; \
    fi

# Expose port
EXPOSE 8000

# Command to run the application with multiple workers for better concurrency
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8", "--loop", "uvloop", "--log-level", "info"]
