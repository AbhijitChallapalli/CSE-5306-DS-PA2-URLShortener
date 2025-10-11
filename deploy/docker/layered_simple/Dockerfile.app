FROM python:3.11-slim
WORKDIR /app

# Copy requirements
COPY layered_simple/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and generate gRPC code
COPY layered_simple/src/proto/*.proto ./proto/
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=. \
    --grpc_python_out=. \
    ./proto/*.proto

# Copy application source
COPY layered_simple/src/repository/ ./repository/
COPY layered_simple/src/service/ ./service/
COPY layered_simple/src/presentation/ ./presentation/
COPY layered_simple/src/app.py .

ENV PYTHONPATH=/app
EXPOSE 50051

CMD ["python", "app.py"]
