FROM python:3.11-slim AS base

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製專案檔案
COPY pyproject.toml .
COPY README.md .
COPY src/ src/

# 安裝 Python 套件
RUN pip install --no-cache-dir .

# MCP Server 預設連接埠
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8080/sse || exit 1

# 預設以 HTTP/SSE 模式啟動
CMD ["python", "-m", "finmind_mcp.server", "--http", "8080"]
