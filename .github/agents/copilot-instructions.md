# MySkills Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-04

## Active Technologies

- Python 3.11+ + paramiko (SSH)、PyYAML (設定檔)、click (CLI) (001-skill-framework)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 001-skill-framework: Added Python 3.11+ + paramiko (SSH)、PyYAML (設定檔)、click (CLI)

<!-- MANUAL ADDITIONS START -->

## Skill Development Style Guide

Each skill is **independently deployed**. Do NOT create cross-skill imports or shared modules.
When writing Python scripts for a skill, follow these conventions:

### Error Handling

- Define a base exception per skill: `class <Skill>Error(Exception)`
- Include `error_code: str` and `remediation: str` fields (follow pa-ngfw-manager pattern)
- Use specific subclasses: `AuthenticationError`, `ConnectionError`, `ValidationError`, `TimeoutError`
- Never use bare `except Exception` — always catch specific exceptions first
- Provide `.to_dict()` method for JSON serialization

```python
class SkillError(Exception):
    def __init__(self, message: str, error_code: str = "UNKNOWN", remediation: str = ""):
        super().__init__(message)
        self.error_code = error_code
        self.remediation = remediation

    def to_dict(self) -> dict:
        return {"error_code": self.error_code, "message": str(self), "remediation": self.remediation}
```

### Logging

- Use Python `logging` module — not `print()` or `click.echo()` for debug output
- `click.echo()` is for user-facing output only (progress, results)
- Log format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Logger name = skill name: `logger = logging.getLogger("k8s-installer")`
- Redact sensitive fields (password, token, api_key) before logging

### CLI Options (Click)

All CLI-based skills should support these standard options:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--verbose` | `-v` | flag | False | Enable debug logging |
| `--json-output` | | flag | False | Output results as JSON |
| `--yes` | `-y` | flag | False | Skip confirmations |
| `--dry-run` | | flag | False | Preview commands without executing |

### Result Model

Every skill script should return a structured result:

```python
@dataclass
class ExecutionResult:
    success: bool
    message: str
    details: dict | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
```

### Retry Logic

For network operations (SSH, API calls), implement retry with exponential backoff:

```python
import time
import random

def retry_with_backoff(fn, max_retries=3, base_delay=1.0, max_delay=30.0):
    for attempt in range(max_retries):
        try:
            return fn()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            time.sleep(delay)
```

### SSH Connection Constants

```python
SSH_TIMEOUT = 30
BANNER_TIMEOUT = 30
AUTH_TIMEOUT = 30
```

### SKILL.md Structure

Every SKILL.md must include these sections in order:
1. YAML frontmatter (`name`, `description`, `version`)
2. Overview
3. When to Use / Supported Platforms
4. Parameters (required inputs)
5. Execution Workflow (numbered steps)
6. Output (what to report)
7. Error Handling (troubleshooting)
8. Scripts (file listing)
9. References (file listing)

### File Naming

- Entry point: `scripts/main.py`
- Data models: `scripts/models.py`
- SSH wrapper: `scripts/ssh_client.py`
- Dependencies: `scripts/requirements.txt`
- Platform-specific commands: `scripts/commands/` or `scripts/commands.py`

<!-- MANUAL ADDITIONS END -->
