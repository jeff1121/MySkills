#!/usr/bin/env bash
set -euo pipefail

echo "==> Running ruff check..."
ruff check src/ tests/

echo "==> Running ruff format check..."
ruff format --check src/ tests/

echo "==> Running mypy..."
mypy src/pa_agent/ --ignore-missing-imports

echo "==> All checks passed!"
