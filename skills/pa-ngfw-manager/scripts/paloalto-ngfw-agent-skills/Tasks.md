# Palo Alto NGFW Agent Skills — Implementation Tasks

## Overview

Build a production-ready **Palo Alto NGFW Agent Skills** project providing 6 core capabilities
(anomaly detection, policy list, policy CRUD, backup, restore, system usage) accessible via
CLI (`pa-agent`) and MCP/HTTP server. All write operations have safety guardrails
(dry-run, confirm, commit control).

**Project root**: `skills/pa-ngfw-manager/scripts/paloalto-ngfw-agent-skills/`

---

## Phase 1: Foundation

### Task 1 — Project Scaffold
- Create `pyproject.toml` with all dependencies (httpx, pydantic, typer, rich, boto3, pytest, tenacity, structlog, python-dotenv)
- Create directory tree: `src/pa_agent/`, `src/pa_agent/storage/`, `src/pa_agent/skills/`, `tests/`, `docker/`, `scripts/`
- Create all `__init__.py` files
- Configure `[project.scripts]` entry point: `pa-agent = "pa_agent.cli:app"`

### Task 2 — Config Module (`src/pa_agent/config.py`)
- Pydantic `BaseSettings` class reading from ENV / `.env`
- Fields: `PANOS_HOST`, `PANOS_API_KEY`, `PANOS_USERNAME`, `PANOS_PASSWORD`, `PANOS_VSYS` (default `vsys1`), `PANOS_VERIFY_TLS` (default `True`), `PANOS_TIMEOUT` (default 30), `PANOS_RATE_LIMIT` (default 10 req/s)
- S3 fields: `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_PREFIX`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_REGION`, `S3_USE_SSL`
- Backup fields: `BACKUP_DIR` (default `./backups`)
- Validators: require either `PANOS_API_KEY` or (`PANOS_USERNAME` + `PANOS_PASSWORD`)

### Task 3 — Logging Module (`src/pa_agent/log.py`)
- structlog configuration with JSON output
- Secret redaction processor (mask `PANOS_PASSWORD`, `PANOS_API_KEY`, `AWS_SECRET_ACCESS_KEY` in log events)
- `get_logger(name)` factory function

### Task 4 — Errors Module (`src/pa_agent/errors.py`)
- Base `PAAgentError(Exception)` with `error_code: str`, `message: str`, `remediation: str`
- Subclasses: `AuthenticationError`, `ConnectionError`, `APIError`, `CommitError`, `ValidationError`, `ConfigError`, `StorageError`
- Each with default remediation text

### Task 5 — HTTP Client (`src/pa_agent/http.py`)
- `PanosHttpClient` class wrapping `httpx.AsyncClient`
- TLS verify toggle from config
- Configurable timeout (10–30s)
- `tenacity` retry decorator (only for GET/idempotent ops; max 3 retries, exponential backoff)
- Token-bucket rate limiter (configurable req/s)
- Methods: `request(method, params, data, files)` → returns `httpx.Response`
- Dependency: Task 2, Task 3, Task 4

---

## Phase 2: PAN-OS API Core

### Task 6 — PAN-OS API Wrapper (`src/pa_agent/panos_api.py`)
- `PanosAPI` class using `PanosHttpClient`
- `keygen()` — call `type=keygen` with username/password → cache API key in-memory (never disk)
- `ensure_auth()` — use API key from ENV or keygen
- `op_command(cmd: str) → ET.Element` — `type=op&cmd=<xml>`
- `config_get(xpath: str) → ET.Element` — `type=config&action=get`
- `config_set(xpath: str, element: str) → ET.Element` — `type=config&action=set`
- `config_edit(xpath: str, element: str) → ET.Element` — `type=config&action=edit`
- `config_delete(xpath: str) → ET.Element` — `type=config&action=delete`
- `commit(comment: str | None, force: bool) → ET.Element` — `type=commit`
- `export_config(category: str) → bytes` — `type=export&category=configuration`
- `import_config(filename: str, data: bytes) → ET.Element` — `type=import`
- `load_config(filename: str) → ET.Element` — op command `<load><config><from>filename</from></config></load>`
- `_parse_response(resp) → ET.Element` — parse XML, detect `<response status="error">`, raise `APIError`
- Dependency: Task 5

### Task 7 — Data Models (`src/pa_agent/models.py`)
- `SecurityRule(BaseModel)` — name, from_zones, to_zones, source, destination, service, application, action, log_setting, disabled, description, tags
- `AnomalyFinding(BaseModel)` — rule_id, severity (low|medium|high|critical), summary, evidence (dict), first_seen, last_seen
- `AnomalyReport(BaseModel)` — findings: list[AnomalyFinding], data_gaps: list[str], window, baseline
- `SystemUsage(BaseModel)` — cpu_percent, memory_percent, sessions_active, sessions_max, dp_load (optional)
- `BackupMetadata(BaseModel)` — filename, hostname, timestamp, sha256, backend, size_bytes
- `ToolResponse(BaseModel)` — ok: bool, result: Any | None, error: dict | None (error_code, message, remediation)
- `PolicyFilter(BaseModel)` — name_contains, tag, from_zone, to_zone, action
- Dependency: Task 1

---

## Phase 3: Storage Backends

### Task 8 — Local Storage (`src/pa_agent/storage/local.py`)
- `LocalStorage` class
- `save(data: bytes, hostname: str) → BackupMetadata` — filename: `<hostname>_<ISO8601>_<sha256>.xml`, save to `BACKUP_DIR`
- `list() → list[BackupMetadata]` — scan backup dir, return sorted by timestamp desc
- `read(filename: str) → bytes` — read backup file
- `delete(filename: str)` — remove backup file
- Dependency: Task 2, Task 7

### Task 9 — S3/MinIO Storage (`src/pa_agent/storage/s3.py`)
- `S3Storage` class using boto3
- Same interface as LocalStorage: `save()`, `list()`, `read()`, `delete()`
- Support `S3_ENDPOINT_URL` for MinIO
- Server-side encryption (AES256) if available
- Graceful error if boto3 credentials not configured
- Dependency: Task 2, Task 7

---

## Phase 4: Skills

### Task 10 — Policy Skill (`src/pa_agent/skills/policy.py`)
- `list_rules(api, filters: PolicyFilter) → list[SecurityRule]`
  - GET xpath `/config/devices/entry/vsys/entry[@name='vsys1']/rulebase/security/rules`
  - Apply filters (name contains, tag, zone, action)
  - Parse XML entries → SecurityRule models
- `add_rule(api, rule: SecurityRule, dry_run=True, confirm=False, validate=False, commit=False, commit_comment=None) → ToolResponse`
  - Build xpath + element XML from SecurityRule model
  - If `dry_run`: return planned xpath/element without sending
  - If not `confirm`: raise error requiring --confirm
  - Send `config_set`
  - If `validate`: re-fetch and compare
  - If `commit`: call `api.commit()`
- `update_rule(api, name, patches: dict, dry_run, confirm, validate, commit, commit_comment) → ToolResponse`
  - Fetch existing rule, apply patches, use `config_edit`
  - Same safety flow as add
- `delete_rule(api, name, dry_run, confirm, commit, commit_comment) → ToolResponse`
  - `config_delete` with safety flow
- Dependency: Task 6, Task 7

### Task 11 — Backup & Restore Skill (`src/pa_agent/skills/backup_restore.py`)
- `backup(api, storage_backend) → BackupMetadata`
  - `export_config("running-config")` → bytes
  - Get hostname via `op_command("<show><system><info></info></system></show>")`
  - Compute SHA256, save via storage backend
- `restore(api, storage_backend, key: str, dry_run=True, confirm=False, commit=False) → ToolResponse`
  - If `dry_run`: show backup metadata + checksum, don't restore
  - If not `confirm`: raise error
  - Read backup → `import_config(filename, data)` → `load_config(filename)`
  - If `commit`: call `api.commit()`
- `list_backups(storage_backend) → list[BackupMetadata]`
- Dependency: Task 6, Task 8, Task 9

### Task 12 — System Usage Skill (`src/pa_agent/skills/system.py`)
- `get_usage(api) → SystemUsage`
  - `<show><system><resources></resources></system></show>` → parse CPU/memory
  - `<show><session><info></info></session></show>` → parse session count/max
  - `<show><running><resource-monitor></resource-monitor></running></show>` → dataplane (graceful degrade)
- Return `SystemUsage` model; mark unavailable fields as None
- Dependency: Task 6, Task 7

### Task 13 — Anomaly Detection Skill (`src/pa_agent/skills/anomaly.py`)
- `detect(api, window: str, baseline: str, thresholds: dict | None) → AnomalyReport`
- Fetch traffic logs: `<show><log><traffic><query>...</query></traffic></log></show>` (time-windowed)
- Fetch threat logs: similar query
- **6 Detection Rules:**
  1. `top_talker_surge` — single src IP traffic/connections > baseline × K (default K=3)
  2. `port_scan` — single src → distinct dst ports > threshold (default 50)
  3. `ddos_approx` — single dst connections spike in short window
  4. `suspicious_outbound` — connections to IPs not seen in baseline period ("new destination")
  5. `threat_severity_spike` — high-severity threat events increase rate
  6. `deny_rate_anomaly` — policy deny hit rate exceeds baseline × K
- Each rule returns `AnomalyFinding` or None
- Graceful degradation: if log fields unavailable, skip rule & add to `data_gaps`
- Configurable thresholds via params
- Dependency: Task 6, Task 7

---

## Phase 5: CLI & Server

### Task 14 — CLI Entrypoint (`src/pa_agent/cli.py`)
- `typer.Typer()` app with sub-apps:
  - `policy` → `list`, `add`, `update`, `delete`
  - `config` → `backup`, `restore`
  - `system` → `usage`
  - `anomaly` → `detect`
- Common options: `--output {json,table}` (default table), `--dry-run`, `--confirm`, `--commit`, `--commit-comment`
- Use `rich` for table output, console formatting
- `asyncio.run()` wrapper for async API calls
- Dependency: Task 10, 11, 12, 13

### Task 15 — MCP/HTTP Server (`src/pa_agent/server_mcp.py`)
- HTTP JSON server (using Python stdlib `http.server` or lightweight approach)
- Routes: `POST /tools/anomaly.detect`, `POST /tools/policy.list`, `POST /tools/policy.add`, `POST /tools/policy.update`, `POST /tools/policy.delete`, `POST /tools/config.backup`, `POST /tools/config.restore`, `POST /tools/system.usage`
- Each accepts JSON body (pydantic validated), returns `ToolResponse` JSON
- Logging: request_id, duration, target host (no secrets)
- MCP stdio skeleton: `handle_mcp_message(json_line) → json_line`
- Dependency: Task 10, 11, 12, 13

---

## Phase 6: Tests, Docker, Docs

### Task 16 — Unit Tests
- `tests/conftest.py` — shared fixtures: mock PAN-OS XML responses, mock API client
- `tests/test_policy.py` — test SecurityRule model validation, xpath/element assembly, filter logic, dry-run behavior
- `tests/test_backup_restore.py` — test filename format `<hostname>_<datetime>_<sha256>.xml`, checksum computation, local storage save/read
- `tests/test_anomaly.py` — test each of 6 rules against sample log data (mock dataset), threshold logic, graceful degradation
- All API calls mocked (no real firewall)
- Dependency: Task 10, 11, 13

### Task 17 — Docker
- `docker/Dockerfile` — Python 3.11-slim, install deps, copy source, expose port, CMD run server
- `docker/docker-compose.yml` — service with env_file, port mapping, optional MinIO service
- Dependency: Task 15

### Task 18 — Shell Scripts
- `scripts/dev.sh` — install editable + dev deps
- `scripts/lint.sh` — ruff check + mypy
- `scripts/test.sh` — pytest with coverage
- Dependency: Task 1

### Task 19 — README
- Installation (pip, docker)
- All ENV variables table
- 10+ CLI command examples (from spec section 7)
- MCP server usage
- Troubleshooting: 401/403, timeout, xpath error, commit fail, S3 connection error
- Dependency: Task 14, 15

### Task 20 — SKILL.md
- Follow repo convention (YAML frontmatter: name, description, version)
- Overview, When to Use, Parameters, Execution Workflow, Output, Error Handling
- Dependency: Task 19
