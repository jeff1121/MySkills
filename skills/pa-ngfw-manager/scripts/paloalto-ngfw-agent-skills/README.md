# Palo Alto NGFW Agent Skills

## 概要 Overview

CLI + MCP server for PAN-OS firewall management. Provides 6 core skills: anomaly detection, policy CRUD, configuration backup/restore, and system usage monitoring. Designed for AI agent integration via MCP protocol or standalone CLI usage.

## 機能一覧 Features

- **Anomaly Detection** — 6 built-in detection rules (top-talker surge, port scan, DDoS approximation, suspicious outbound, threat severity spike, deny rate anomaly)
- **Policy Management** — List / add / update / delete security rules with safety guardrails
- **Configuration Backup & Restore** — Local filesystem and S3/MinIO storage backends
- **System Usage Monitoring** — CPU, memory, disk, and session utilization
- **MCP/HTTP Server** — Expose all skills as tools for AI agent integration
- **Safety** — Dry-run by default, explicit confirmation required, commit control, secret redaction

## クイックスタート Quick Start

### インストール Installation

```bash
# From source
pip install -e ".[dev]"

# Or using dev script
bash scripts/dev.sh
```

### Docker

```bash
# Build and run
cd docker
docker-compose up -d

# With MinIO storage
docker-compose --profile storage up -d
```

## 環境変数 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PANOS_HOST | ✅ | — | Firewall URL (e.g., https://10.0.0.1) |
| PANOS_API_KEY | ⚠️ | — | XML API key (or use username/password) |
| PANOS_USERNAME | ⚠️ | — | Username (with PANOS_PASSWORD) |
| PANOS_PASSWORD | ⚠️ | — | Password (with PANOS_USERNAME) |
| PANOS_VSYS | — | vsys1 | Virtual system |
| PANOS_VERIFY_TLS | — | true | Verify TLS certificate |
| PANOS_TIMEOUT | — | 30 | Request timeout (seconds) |
| PANOS_RATE_LIMIT | — | 10 | Max requests per second |
| BACKUP_DIR | — | ./backups | Local backup directory |
| S3_ENDPOINT_URL | — | — | S3/MinIO endpoint |
| S3_BUCKET | — | — | S3 bucket name |
| S3_PREFIX | — | — | S3 key prefix |
| AWS_ACCESS_KEY_ID | — | — | AWS/MinIO access key |
| AWS_SECRET_ACCESS_KEY | — | — | AWS/MinIO secret key |
| S3_REGION | — | — | S3 region |
| S3_USE_SSL | — | true | Use SSL for S3 |

⚠️ Either `PANOS_API_KEY` or (`PANOS_USERNAME` + `PANOS_PASSWORD`) is required.

## CLI使用方法 CLI Usage (pa-agent)

### ポリシー管理 Policy Management

```bash
# List all security rules
pa-agent policy list

# Filter rules by name
pa-agent policy list --contains "Allow-Web" --output json

# Filter by zones
pa-agent policy list --from-zone trust --to-zone untrust

# Add a rule (dry-run — shows what would be sent)
pa-agent policy add --name "Allow-DNS" \
  --from-zone trust --to-zone untrust \
  --source any --destination any \
  --service service-dns --application dns \
  --action allow --dry-run

# Add a rule (confirm + commit)
pa-agent policy add --name "Allow-DNS" \
  --from-zone trust --to-zone untrust \
  --source any --destination any \
  --service service-dns --application dns \
  --action allow \
  --no-dry-run --confirm --commit \
  --commit-comment "Add Allow-DNS rule"

# Update rule fields
pa-agent policy update --name "Allow-DNS" \
  --set description="Managed by agent" \
  --no-dry-run --confirm --commit

# Delete a rule
pa-agent policy delete --name "Temp-Rule" --no-dry-run --confirm
```

### バックアップと復元 Backup & Restore

```bash
# Backup to local filesystem
pa-agent config backup --backend local

# Backup to S3/MinIO
pa-agent config backup --backend s3

# List backups
pa-agent config list --backend local --output json

# Restore (dry-run — shows backup info)
pa-agent config restore --backend s3 --key "fw01_20240115T100000Z_a1b2c3d4e5f6.xml" --dry-run

# Restore (execute)
pa-agent config restore --backend local --key "fw01_20240115T100000Z_a1b2c3d4e5f6.xml" \
  --no-dry-run --confirm --commit --commit-comment "Restore from backup"
```

### システム使用状況 System Usage

```bash
# Show system resources
pa-agent system usage

# JSON output
pa-agent system usage --output json
```

### 異常検知 Anomaly Detection

```bash
# Detect anomalies (last 1h, baseline 24h)
pa-agent anomaly detect --window 1h --baseline 24h

# Short window detection
pa-agent anomaly detect --window 15m --baseline 1h --output json

# Extended analysis
pa-agent anomaly detect --window 24h --baseline 7d
```

## MCP/HTTPサーバー MCP/HTTP Server

### サーバー起動 Start Server

```bash
# HTTP mode (default port 8080)
python -m pa_agent.server_mcp

# Custom port
python -m pa_agent.server_mcp 9090

# MCP stdio mode
python -m pa_agent.server_mcp --stdio
```

### APIエンドポイント API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /tools | List available tools |
| GET | /health | Health check |
| POST | /tools/policy.list | List security rules |
| POST | /tools/policy.add | Add security rule |
| POST | /tools/policy.update | Update security rule |
| POST | /tools/policy.delete | Delete security rule |
| POST | /tools/config.backup | Backup configuration |
| POST | /tools/config.restore | Restore configuration |
| POST | /tools/system.usage | System resource usage |
| POST | /tools/anomaly.detect | Anomaly detection |

### API呼び出し例 Example API Call

```bash
curl -X POST http://localhost:8080/tools/policy.list \
  -H "Content-Type: application/json" \
  -d '{"from_zone": "trust"}'
```

## 安全機構 Safety Guardrails

All write operations follow these safety principles:

1. **Dry-run by default** — `--dry-run` shows planned changes without executing
2. **Explicit confirmation** — `--confirm` required to execute changes
3. **No auto-commit** — `--commit` must be explicitly enabled
4. **Candidate config** — Changes go to candidate config, not running config
5. **Validation** — `--validate` re-fetches and verifies changes
6. **Commit comments** — `--commit-comment` for audit trail
7. **Rate limiting** — Built-in request throttling
8. **Secret redaction** — API keys and passwords never appear in logs

## 異常検知ルール Anomaly Detection Rules

| # | Rule | Severity | Description |
|---|------|----------|-------------|
| 1 | top_talker_surge | medium | Single src IP traffic exceeds baseline × K |
| 2 | port_scan | high | Src connects to >50 distinct dst ports |
| 3 | ddos_approx | critical | Dst connection spike in short window |
| 4 | suspicious_outbound | medium | Connections to new (unseen) destinations |
| 5 | threat_severity_spike | high | High-severity threat events increase rate |
| 6 | deny_rate_anomaly | medium | Policy deny rate exceeds baseline |

## 開発 Development

```bash
# Setup dev environment
bash scripts/dev.sh

# Run tests
bash scripts/test.sh

# Run linter
bash scripts/lint.sh
```

## トラブルシューティング Troubleshooting

### 401 Unauthorized

- Verify `PANOS_API_KEY` is valid and not expired
- Or check `PANOS_USERNAME`/`PANOS_PASSWORD` credentials
- Ensure the API user has sufficient permissions

### 403 Forbidden

- Check user role and access domain in PAN-OS
- Verify vsys access permissions

### Connection Timeout

- Check `PANOS_HOST` is reachable
- Increase `PANOS_TIMEOUT` if firewall is under load
- Verify network/firewall rules between agent and PAN-OS

### XPath Error

- Verify `PANOS_VSYS` is correct (default: vsys1)
- Check rule names don't contain special characters
- Use `--dry-run` to inspect the xpath before sending

### Commit Failed

- Check for conflicting changes in candidate config
- Review commit errors in PAN-OS web UI
- Consider restoring from backup: `pa-agent config restore --backend local --key <backup>`

### S3/MinIO Connection Error

- Verify `S3_ENDPOINT_URL` is reachable
- Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- For MinIO, ensure `S3_USE_SSL=false` if not using TLS

### TLS Certificate Error

- Set `PANOS_VERIFY_TLS=false` for self-signed certificates
- Or add the CA certificate to the system trust store

## プロジェクト構成 Project Structure

```
paloalto-ngfw-agent-skills/
├── README.md
├── pyproject.toml
├── src/pa_agent/
│   ├── __init__.py
│   ├── config.py          # ENV-based configuration
│   ├── log.py             # Structured logging
│   ├── errors.py          # Error hierarchy
│   ├── http.py            # HTTP client with retry
│   ├── panos_api.py       # PAN-OS XML API wrapper
│   ├── models.py          # Pydantic data models
│   ├── storage/
│   │   ├── local.py       # Local backup storage
│   │   └── s3.py          # S3/MinIO storage
│   ├── skills/
│   │   ├── anomaly.py     # Anomaly detection
│   │   ├── policy.py      # Policy management
│   │   ├── backup_restore.py  # Backup & restore
│   │   └── system.py      # System monitoring
│   ├── cli.py             # CLI entrypoint (pa-agent)
│   └── server_mcp.py      # MCP/HTTP server
├── tests/
│   ├── conftest.py
│   ├── test_policy.py
│   ├── test_backup_restore.py
│   └── test_anomaly.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── scripts/
    ├── dev.sh
    ├── lint.sh
    └── test.sh
```

## ライセンス License

MIT