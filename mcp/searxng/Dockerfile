FROM alpine:3.18

# Install dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    openssl \
    ca-certificates \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev \
    openssl-dev \
    git

# Set working directory
WORKDIR /app

# Clone SearXNG
RUN git clone https://github.com/searxng/searxng.git .

# Install required dependencies first
RUN pip3 install --no-cache-dir pyyaml requests babel flask flask-babel lxml pygments python-dateutil simplejson httpx pyopenssl certifi uvloop httptools

# Install SearXNG and dependencies
RUN pip3 install --no-cache-dir -e .

# Create MCP API layer
COPY ./mcp_api.py /app/mcp_api.py

# Install MCP API dependencies
RUN pip3 install --no-cache-dir fastapi uvicorn[standard]

# Expose port
EXPOSE 8080

# Start SearXNG with MCP API
CMD ["python3", "/app/mcp_api.py"]
