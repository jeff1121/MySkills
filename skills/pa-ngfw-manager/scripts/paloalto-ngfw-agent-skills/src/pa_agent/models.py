"""Pydantic v2 data models for PAN-OS firewall agent."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Literal

from pydantic import BaseModel, Field


class SecurityRule(BaseModel):
    """Represents a security rule in PAN-OS."""

    name: str
    from_zones: list[str] = Field(default=["any"])
    to_zones: list[str] = Field(default=["any"])
    source: list[str] = Field(default=["any"])
    destination: list[str] = Field(default=["any"])
    service: list[str] = Field(default=["application-default"])
    application: list[str] = Field(default=["any"])
    action: Literal["allow", "deny", "drop", "reset-client", "reset-server", "reset-both"] = "allow"
    log_setting: str | None = None
    disabled: bool = False
    description: str = ""
    tags: list[str] = Field(default=[])

    def to_panos_xml(self) -> str:
        """Convert rule to PAN-OS XML element string.

        Returns:
            XML string representation of the security rule for config set.
        """
        root = ET.Element("entry", name=self.name)

        # From zones
        from_elem = ET.SubElement(root, "from")
        for zone in self.from_zones:
            ET.SubElement(from_elem, "member").text = zone

        # To zones
        to_elem = ET.SubElement(root, "to")
        for zone in self.to_zones:
            ET.SubElement(to_elem, "member").text = zone

        # Source
        source_elem = ET.SubElement(root, "source")
        for src in self.source:
            ET.SubElement(source_elem, "member").text = src

        # Destination
        dest_elem = ET.SubElement(root, "destination")
        for dst in self.destination:
            ET.SubElement(dest_elem, "member").text = dst

        # Service
        service_elem = ET.SubElement(root, "service")
        for svc in self.service:
            ET.SubElement(service_elem, "member").text = svc

        # Application
        app_elem = ET.SubElement(root, "application")
        for app in self.application:
            ET.SubElement(app_elem, "member").text = app

        # Action
        ET.SubElement(root, "action").text = self.action

        # Disabled
        ET.SubElement(root, "disabled").text = "yes" if self.disabled else "no"

        # Optional fields
        if self.description:
            ET.SubElement(root, "description").text = self.description

        if self.log_setting:
            ET.SubElement(root, "log-setting").text = self.log_setting

        if self.tags:
            tags_elem = ET.SubElement(root, "tag")
            for tag in self.tags:
                ET.SubElement(tags_elem, "member").text = tag

        return ET.tostring(root, encoding="unicode")

    @classmethod
    def from_panos_xml(cls, element: ET.Element) -> SecurityRule:
        """Parse a security rule from a PAN-OS XML element.

        Args:
            element: An xml.etree.ElementTree.Element representing a security rule entry.

        Returns:
            SecurityRule instance parsed from XML.
        """
        name = element.get("name", "")

        def get_members(parent_elem: ET.Element, tag: str) -> list[str]:
            """Extract list of members from XML element."""
            parent = parent_elem.find(tag)
            if parent is None:
                return ["any"]
            members = [m.text for m in parent.findall("member") if m.text]
            return members if members else ["any"]

        from_zones = get_members(element, "from")
        to_zones = get_members(element, "to")
        source = get_members(element, "source")
        destination = get_members(element, "destination")
        service = get_members(element, "service")
        application = get_members(element, "application")

        action_elem = element.find("action")
        action = action_elem.text if action_elem is not None else "allow"

        disabled_elem = element.find("disabled")
        disabled = (disabled_elem.text or "").lower() == "yes"

        description_elem = element.find("description")
        description = description_elem.text or ""

        log_setting_elem = element.find("log-setting")
        log_setting = log_setting_elem.text if log_setting_elem is not None else None

        tags_elem = element.find("tag")
        tags: list[str] = []
        if tags_elem is not None:
            tags = [m.text for m in tags_elem.findall("member") if m.text]

        return cls(
            name=name,
            from_zones=from_zones,
            to_zones=to_zones,
            source=source,
            destination=destination,
            service=service,
            application=application,
            action=action,
            log_setting=log_setting,
            disabled=disabled,
            description=description,
            tags=tags,
        )


class PolicyFilter(BaseModel):
    """Filter for querying security rules."""

    name_contains: str | None = None
    tag: str | None = None
    from_zone: str | None = None
    to_zone: str | None = None
    action: str | None = None

    def matches(self, rule: SecurityRule) -> bool:
        """Check if a security rule matches this filter.

        Args:
            rule: SecurityRule to check against this filter.

        Returns:
            True if the rule matches all filter criteria, False otherwise.
        """
        if self.name_contains and self.name_contains.lower() not in rule.name.lower():
            return False

        if self.tag and self.tag not in rule.tags:
            return False

        if self.from_zone and self.from_zone not in rule.from_zones:
            return False

        if self.to_zone and self.to_zone not in rule.to_zones:
            return False

        if self.action and rule.action != self.action:
            return False

        return True


class AnomalyFinding(BaseModel):
    """Represents a single anomaly finding in a security analysis."""

    rule_id: str
    severity: Literal["low", "medium", "high", "critical"]
    summary: str
    evidence: dict[str, Any]
    first_seen: str
    last_seen: str


class AnomalyReport(BaseModel):
    """Report containing anomaly findings and analysis details."""

    findings: list[AnomalyFinding] = Field(default=[])
    data_gaps: list[str] = Field(default=[])
    window: str
    baseline: str


class SystemUsage(BaseModel):
    """System resource usage metrics."""

    cpu_percent: float | None = None
    memory_percent: float | None = None
    sessions_active: int | None = None
    sessions_max: int | None = None
    dp_load: float | None = None


class BackupMetadata(BaseModel):
    """Metadata for a configuration backup."""

    filename: str
    hostname: str
    timestamp: str
    sha256: str
    backend: Literal["local", "s3"]
    size_bytes: int


class ToolResponse(BaseModel):
    """Generic response wrapper for tool operations."""

    ok: bool
    result: Any | None = None
    error: dict[str, str] | None = Field(default=None)

    class ErrorInfo:
        """Expected keys in error dict: error_code, message, remediation."""

        pass
