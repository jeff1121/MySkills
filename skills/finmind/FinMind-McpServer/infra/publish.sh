#!/usr/bin/env bash
# FinMind MCP Server — 推送映像檔到 DockerHub
#
# 使用方式：
#   ./publish.sh              # 推送 latest 標籤
#   ./publish.sh v0.1.0       # 推送指定版本標籤
#
# 前置需求：
#   docker login（以 jeffhou 帳號登入 DockerHub）

set -euo pipefail

IMAGE_NAME="jeffhou/finmind-mcp-server"
VERSION="${1:-latest}"

echo "🔨 建置映像檔..."
docker compose -f docker-compose.build.yml build

echo "🏷️  標記版本: ${VERSION}"
docker tag "${IMAGE_NAME}:latest" "${IMAGE_NAME}:${VERSION}"

echo "📤 推送映像檔到 DockerHub..."
docker push "${IMAGE_NAME}:latest"

if [ "${VERSION}" != "latest" ]; then
    docker push "${IMAGE_NAME}:${VERSION}"
    echo "✅ 已推送: ${IMAGE_NAME}:latest 與 ${IMAGE_NAME}:${VERSION}"
else
    echo "✅ 已推送: ${IMAGE_NAME}:latest"
fi
