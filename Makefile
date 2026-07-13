.PHONY: lint format test validate check help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run ruff linter on all skills
	ruff check skills/

format: ## Format all Python files with ruff
	ruff format skills/

format-check: ## Check formatting without changes
	ruff format --check skills/

test: ## Run pytest across all skills
	pytest skills/ -v --tb=short

validate: ## Validate all SKILL.md files have required sections
	@echo "Validating SKILL.md files..."
	@for dir in skills/*/; do \
		skill=$$(basename "$$dir"); \
		if [ ! -f "$$dir/SKILL.md" ]; then \
			echo "❌ $$skill: SKILL.md missing"; \
		else \
			missing=""; \
			grep -q "^name:" "$$dir/SKILL.md" || missing="$$missing name"; \
			grep -q "^description:" "$$dir/SKILL.md" || missing="$$missing description"; \
			grep -q "^version:" "$$dir/SKILL.md" || missing="$$missing version"; \
			grep -qiE "^## .*(overview|概覽)" "$$dir/SKILL.md" || missing="$$missing overview"; \
			grep -qiE "^##+ .*(workflow|工作流程|快速流程|stage one)" "$$dir/SKILL.md" || missing="$$missing workflow"; \
			grep -qiE "^## .*(error|troubleshoot|疑難排解|錯誤處理|常見問題)" "$$dir/SKILL.md" || missing="$$missing error-handling"; \
			if [ -z "$$missing" ]; then \
				echo "✅ $$skill"; \
			else \
				echo "⚠️  $$skill: missing sections:$$missing"; \
			fi; \
		fi; \
	done

check: lint format-check validate ## Run all checks (lint + format + validate)
