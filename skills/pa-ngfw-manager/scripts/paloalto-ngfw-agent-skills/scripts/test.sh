#!/usr/bin/env bash
set -euo pipefail

echo "==> Running pytest with coverage..."
pytest tests/ -v --cov=pa_agent --cov-report=term-missing --cov-report=html

echo "==> Tests complete! Coverage report: htmlcov/index.html"
