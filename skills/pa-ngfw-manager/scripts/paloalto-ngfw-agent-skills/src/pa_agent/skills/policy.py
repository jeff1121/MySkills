"""Policy skill — CRUD operations for PAN-OS security rules."""

from __future__ import annotations

from typing import Any

from pa_agent.errors import APIError, CommitError, DryRunAbort, ValidationError
from pa_agent.log import get_logger
from pa_agent.models import PolicyFilter, SecurityRule, ToolResponse
from pa_agent.panos_api import PanosAPI

logger = get_logger(__name__)


def _error_response(exc: Exception, *, default_code: str = "UNKNOWN") -> ToolResponse:
    """Build a ToolResponse from an exception."""
    if hasattr(exc, "to_dict"):
        return ToolResponse(ok=False, error=exc.to_dict())
    return ToolResponse(
        ok=False,
        error={
            "error_code": default_code,
            "message": str(exc),
            "remediation": "",
        },
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

async def list_rules(
    api: PanosAPI,
    filters: PolicyFilter | None = None,
) -> ToolResponse:
    """List security rules with optional filtering."""
    logger.info("list_rules.start", filters=filters.model_dump() if filters else None)
    try:
        response = await api.config_get(api.security_rule_xpath())
    except (APIError, Exception) as exc:
        logger.error("list_rules.fetch_failed", error=str(exc))
        return _error_response(exc, default_code="API_ERROR")

    entries = response.findall(".//entry")
    rules: list[SecurityRule] = []
    for entry in entries:
        try:
            rules.append(SecurityRule.from_panos_xml(entry))
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_rules.parse_failed", entry=entry.get("name"), error=str(exc))

    if filters:
        rules = [r for r in rules if filters.matches(r)]

    logger.info("list_rules.done", count=len(rules))
    return ToolResponse(ok=True, result=[rule.model_dump() for rule in rules])


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

async def add_rule(
    api: PanosAPI,
    rule: SecurityRule,
    dry_run: bool = True,
    confirm: bool = False,
    validate: bool = False,
    commit: bool = False,
    commit_comment: str | None = None,
) -> ToolResponse:
    """Add a new security rule."""
    xpath = api.security_rule_xpath()
    element = rule.to_panos_xml()
    logger.info("add_rule.start", rule=rule.name, dry_run=dry_run, confirm=confirm)

    if dry_run:
        return ToolResponse(
            ok=True,
            result={
                "action": "dry_run",
                "rule": rule.name,
                "xpath": xpath,
                "element": element,
                "message": "Dry-run mode — no changes applied.",
            },
        )

    if not confirm:
        err = DryRunAbort("Operation requires explicit confirmation to proceed.")
        logger.warning("add_rule.not_confirmed", rule=rule.name)
        return _error_response(err)

    try:
        await api.config_set(xpath, element)
    except (APIError, Exception) as exc:
        logger.error("add_rule.set_failed", rule=rule.name, error=str(exc))
        return _error_response(exc, default_code="API_ERROR")

    if validate:
        try:
            verify_resp = await api.config_get(api.security_rule_xpath(rule.name))
            verify_entry = verify_resp.find(".//entry")
            if verify_entry is None:
                raise ValidationError(f"Rule '{rule.name}' not found after add.")
            fetched = SecurityRule.from_panos_xml(verify_entry)
            if fetched.name != rule.name:
                raise ValidationError(
                    f"Rule name mismatch: expected '{rule.name}', got '{fetched.name}'."
                )
        except ValidationError:
            raise
        except Exception as exc:
            logger.error("add_rule.validate_failed", rule=rule.name, error=str(exc))
            return _error_response(exc, default_code="VALIDATION_ERROR")

    if commit:
        try:
            await api.commit(comment=commit_comment)
        except (CommitError, Exception) as exc:
            logger.error("add_rule.commit_failed", rule=rule.name, error=str(exc))
            return _error_response(exc, default_code="COMMIT_ERROR")

    logger.info("add_rule.done", rule=rule.name, committed=commit)
    return ToolResponse(
        ok=True,
        result={
            "action": "added",
            "rule": rule.name,
            "committed": commit,
            "validated": validate,
        },
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_rule(
    api: PanosAPI,
    name: str,
    patches: dict[str, Any],
    dry_run: bool = True,
    confirm: bool = False,
    validate: bool = False,
    commit: bool = False,
    commit_comment: str | None = None,
) -> ToolResponse:
    """Update specific fields of an existing rule (patch-like)."""
    logger.info("update_rule.start", rule=name, patches=list(patches.keys()), dry_run=dry_run)

    # Fetch existing rule
    try:
        response = await api.config_get(api.security_rule_xpath(name))
        entry = response.find(".//entry")
        if entry is None:
            raise ValidationError(f"Rule '{name}' not found.")
        existing = SecurityRule.from_panos_xml(entry)
    except (ValidationError, APIError) as exc:
        logger.error("update_rule.fetch_failed", rule=name, error=str(exc))
        return _error_response(exc, default_code="API_ERROR")
    except Exception as exc:
        logger.error("update_rule.fetch_failed", rule=name, error=str(exc))
        return _error_response(exc, default_code="API_ERROR")

    # Apply patches
    updated = existing.model_copy(update=patches)
    xpath = api.security_rule_xpath(name)
    element = updated.to_panos_xml()

    if dry_run:
        return ToolResponse(
            ok=True,
            result={
                "action": "dry_run",
                "rule": name,
                "xpath": xpath,
                "patches": patches,
                "before": existing.model_dump(),
                "after": updated.model_dump(),
                "message": "Dry-run mode — no changes applied.",
            },
        )

    if not confirm:
        err = DryRunAbort("Operation requires explicit confirmation to proceed.")
        logger.warning("update_rule.not_confirmed", rule=name)
        return _error_response(err)

    try:
        await api.config_edit(xpath, element)
    except (APIError, Exception) as exc:
        logger.error("update_rule.edit_failed", rule=name, error=str(exc))
        return _error_response(exc, default_code="API_ERROR")

    if validate:
        try:
            verify_resp = await api.config_get(api.security_rule_xpath(name))
            verify_entry = verify_resp.find(".//entry")
            if verify_entry is None:
                raise ValidationError(f"Rule '{name}' not found after update.")
            fetched = SecurityRule.from_panos_xml(verify_entry)
            for field, value in patches.items():
                if getattr(fetched, field, None) != value:
                    raise ValidationError(
                        f"Field '{field}' mismatch after update: "
                        f"expected {value!r}, got {getattr(fetched, field, None)!r}."
                    )
        except ValidationError:
            raise
        except Exception as exc:
            logger.error("update_rule.validate_failed", rule=name, error=str(exc))
            return _error_response(exc, default_code="VALIDATION_ERROR")

    if commit:
        try:
            await api.commit(comment=commit_comment)
        except (CommitError, Exception) as exc:
            logger.error("update_rule.commit_failed", rule=name, error=str(exc))
            return _error_response(exc, default_code="COMMIT_ERROR")

    logger.info("update_rule.done", rule=name, committed=commit)
    return ToolResponse(
        ok=True,
        result={
            "action": "updated",
            "rule": name,
            "patches": patches,
            "committed": commit,
            "validated": validate,
        },
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_rule(
    api: PanosAPI,
    name: str,
    dry_run: bool = True,
    confirm: bool = False,
    commit: bool = False,
    commit_comment: str | None = None,
) -> ToolResponse:
    """Delete a security rule."""
    xpath = api.security_rule_xpath(name)
    logger.info("delete_rule.start", rule=name, dry_run=dry_run, confirm=confirm)

    if dry_run:
        return ToolResponse(
            ok=True,
            result={
                "action": "dry_run",
                "rule": name,
                "xpath": xpath,
                "message": "Dry-run mode — rule would be deleted. No changes applied.",
            },
        )

    if not confirm:
        err = DryRunAbort("Operation requires explicit confirmation to proceed.")
        logger.warning("delete_rule.not_confirmed", rule=name)
        return _error_response(err)

    try:
        await api.config_delete(xpath)
    except (APIError, Exception) as exc:
        logger.error("delete_rule.delete_failed", rule=name, error=str(exc))
        return _error_response(exc, default_code="API_ERROR")

    if commit:
        try:
            await api.commit(comment=commit_comment)
        except (CommitError, Exception) as exc:
            logger.error("delete_rule.commit_failed", rule=name, error=str(exc))
            return _error_response(exc, default_code="COMMIT_ERROR")

    logger.info("delete_rule.done", rule=name, committed=commit)
    return ToolResponse(
        ok=True,
        result={
            "action": "deleted",
            "rule": name,
            "committed": commit,
        },
    )
