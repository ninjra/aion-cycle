# Base image pinned by immutable digest for reproducibility.
# Refresh intentionally with:
#   TOKEN=$(curl -fsSL "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/node:pull" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
#   curl -fsSL -o /dev/null -D - -H "Authorization: Bearer $TOKEN" \
#     -H "Accept: application/vnd.oci.image.index.v1+json" \
#     -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
#     https://registry-1.docker.io/v2/library/node/manifests/22-bookworm | grep -i docker-content-digest
FROM node:22-bookworm@sha256:c601a46abb4d2ab80a9dc3da208d50d1122642d53f17a101926ace71e5a9bf1c

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 make curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package.json package-lock.json /app/
RUN npm ci --cache /tmp/npm-cache

RUN curl -fsSL https://github.com/iden3/circom/releases/download/v2.2.3/circom-linux-amd64 -o /usr/local/bin/circom \
    && chmod +x /usr/local/bin/circom \
    && echo "85342c7ff332d948df7c0c50ecf201e6129349aef550ce873f3c811b79fe53a3  /usr/local/bin/circom" | sha256sum -c -

COPY . /app

CMD ["python3", "aion_cycle.py", "--verify-statement", "aion.statement.json"]
