FROM node:22-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 make curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN npm install -g snarkjs@0.7.6 --cache /tmp/npm-cache \
    && curl -fsSL https://github.com/iden3/circom/releases/download/v2.2.3/circom-linux-amd64 -o /usr/local/bin/circom \
    && chmod +x /usr/local/bin/circom \
    && npm install circomlib@2.0.5 --cache /tmp/npm-cache

CMD ["python3", "aion_cycle.py", "--verify-statement", "aion.statement.json"]
