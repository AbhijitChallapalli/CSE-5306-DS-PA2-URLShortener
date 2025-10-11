FROM python:3.11-slim
WORKDIR /app

# --- Install grpcurl (static binary) ---
ARG GRPCURL_VERSION=1.9.1
RUN set -eux; \
    apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl tar \
    && rm -rf /var/lib/apt/lists/*; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
    amd64)  url="https://github.com/fullstorydev/grpcurl/releases/download/v${GRPCURL_VERSION}/grpcurl_${GRPCURL_VERSION}_linux_x86_64.tar.gz" ;; \
    arm64)  url="https://github.com/fullstorydev/grpcurl/releases/download/v${GRPCURL_VERSION}/grpcurl_${GRPCURL_VERSION}_linux_arm64.tar.gz" ;; \
    armhf|armel) url="https://github.com/fullstorydev/grpcurl/releases/download/v${GRPCURL_VERSION}/grpcurl_${GRPCURL_VERSION}_linux_armv6.tar.gz" ;; \
    *) echo "Unsupported arch: $arch"; exit 1 ;; \
    esac; \
    curl -L "$url" -o /tmp/grpcurl.tgz; \
    tar -xzf /tmp/grpcurl.tgz -C /usr/local/bin grpcurl; \
    chmod +x /usr/local/bin/grpcurl; \
    rm -f /tmp/grpcurl.tgz; \
    /usr/local/bin/grpcurl -version

# --- Python deps ---
COPY layered_simple/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- gRPC stubs ---
COPY layered_simple/src/proto/*.proto ./proto/
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/*.proto

# --- App code ---
COPY layered_simple/src/repository/ ./repository/
COPY layered_simple/src/service/ ./service/
COPY layered_simple/src/presentation/ ./presentation/
COPY layered_simple/src/app.py .

ENV PYTHONPATH=/app
EXPOSE 50051
CMD ["python", "app.py"]
