FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .
EXPOSE 8766
CMD ["hermes-maintainer", "serve", "--host", "0.0.0.0", "--port", "8766"]
