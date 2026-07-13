"""Tests for policy model validation, XML serialisation, and skill logic."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, MagicMock

import pytest

from pa_agent.models import PolicyFilter, SecurityRule, ToolResponse
from pa_agent.skills.policy import add_rule


# ---------------------------------------------------------------------------
# XML serialisation
# ---------------------------------------------------------------------------


class TestSecurityRuleToXml:
    """SecurityRule.to_panos_xml() generates correct XML."""

    def test_to_panos_xml_contains_entry_name(self, sample_rule: SecurityRule):
        xml_str = sample_rule.to_panos_xml()
        root = ET.fromstring(xml_str)
        assert root.tag == "entry"
        assert root.get("name") == "Allow-Web"

    def test_to_panos_xml_zones(self, sample_rule: SecurityRule):
        xml_str = sample_rule.to_panos_xml()
        root = ET.fromstring(xml_str)
        from_members = [m.text for m in root.findall("from/member")]
        to_members = [m.text for m in root.findall("to/member")]
        assert from_members == ["trust"]
        assert to_members == ["untrust"]

    def test_to_panos_xml_services_and_apps(self, sample_rule: SecurityRule):
        xml_str = sample_rule.to_panos_xml()
        root = ET.fromstring(xml_str)
        services = [m.text for m in root.findall("service/member")]
        apps = [m.text for m in root.findall("application/member")]
        assert services == ["service-http", "service-https"]
        assert apps == ["web-browsing", "ssl"]

    def test_to_panos_xml_action_and_disabled(self, sample_rule: SecurityRule):
        xml_str = sample_rule.to_panos_xml()
        root = ET.fromstring(xml_str)
        assert root.findtext("action") == "allow"
        assert root.findtext("disabled") == "no"

    def test_to_panos_xml_tags(self, sample_rule: SecurityRule):
        xml_str = sample_rule.to_panos_xml()
        root = ET.fromstring(xml_str)
        tags = [m.text for m in root.findall("tag/member")]
        assert tags == ["managed"]


# ---------------------------------------------------------------------------
# XML parsing
# ---------------------------------------------------------------------------


class TestSecurityRuleFromXml:
    """SecurityRule.from_panos_xml() parses XML correctly."""

    def test_from_panos_xml_name(self, sample_panos_rule_xml: str):
        element = ET.fromstring(sample_panos_rule_xml)
        rule = SecurityRule.from_panos_xml(element)
        assert rule.name == "Allow-Web"

    def test_from_panos_xml_fields(self, sample_panos_rule_xml: str):
        element = ET.fromstring(sample_panos_rule_xml)
        rule = SecurityRule.from_panos_xml(element)
        assert rule.from_zones == ["trust"]
        assert rule.to_zones == ["untrust"]
        assert rule.source == ["10.0.0.0/8"]
        assert rule.destination == ["any"]
        assert rule.service == ["service-http", "service-https"]
        assert rule.application == ["web-browsing", "ssl"]
        assert rule.action == "allow"
        assert rule.disabled is False
        assert rule.description == "Allow web traffic"
        assert rule.tags == ["managed"]


# ---------------------------------------------------------------------------
# Roundtrip
# ---------------------------------------------------------------------------


def test_roundtrip_xml(sample_rule: SecurityRule):
    """to_xml -> parse -> from_xml gives the same model."""
    xml_str = sample_rule.to_panos_xml()
    element = ET.fromstring(xml_str)
    rebuilt = SecurityRule.from_panos_xml(element)
    assert rebuilt == sample_rule


# ---------------------------------------------------------------------------
# PolicyFilter.matches()
# ---------------------------------------------------------------------------


class TestPolicyFilterMatches:
    """PolicyFilter.matches() with various filter criteria."""

    def test_matches_name_contains(self, sample_rule: SecurityRule):
        f = PolicyFilter(name_contains="web")
        assert f.matches(sample_rule) is True

    def test_no_match_name_contains(self, sample_rule: SecurityRule):
        f = PolicyFilter(name_contains="vpn")
        assert f.matches(sample_rule) is False

    def test_matches_tag(self, sample_rule: SecurityRule):
        f = PolicyFilter(tag="managed")
        assert f.matches(sample_rule) is True

    def test_no_match_tag(self, sample_rule: SecurityRule):
        f = PolicyFilter(tag="unmanaged")
        assert f.matches(sample_rule) is False

    def test_matches_from_zone(self, sample_rule: SecurityRule):
        f = PolicyFilter(from_zone="trust")
        assert f.matches(sample_rule) is True

    def test_matches_action(self, sample_rule: SecurityRule):
        f = PolicyFilter(action="allow")
        assert f.matches(sample_rule) is True

    def test_no_match_action(self, sample_rule: SecurityRule):
        f = PolicyFilter(action="deny")
        assert f.matches(sample_rule) is False

    def test_empty_filter_matches_everything(self, sample_rule: SecurityRule):
        f = PolicyFilter()
        assert f.matches(sample_rule) is True


# ---------------------------------------------------------------------------
# Dry-run / confirm guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_rule_dry_run_returns_planned_actions(
    mock_settings, sample_rule: SecurityRule
):
    """dry_run=True returns planned actions without calling the API."""
    from pa_agent.panos_api import PanosAPI

    api = MagicMock(spec=PanosAPI)
    api.security_rule_xpath = MagicMock(return_value="/xpath/test")

    resp = await add_rule(api, sample_rule, dry_run=True)
    assert resp.ok is True
    assert resp.result["action"] == "dry_run"
    assert resp.result["rule"] == "Allow-Web"
    # config_set must not have been called
    api.config_set.assert_not_called()


@pytest.mark.asyncio
async def test_add_rule_without_confirm_returns_error(
    mock_settings, sample_rule: SecurityRule
):
    """add_rule with dry_run=False but confirm=False returns error."""
    from pa_agent.panos_api import PanosAPI

    api = MagicMock(spec=PanosAPI)
    api.security_rule_xpath = MagicMock(return_value="/xpath/test")

    resp = await add_rule(api, sample_rule, dry_run=False, confirm=False)
    assert resp.ok is False
    assert resp.error is not None
    assert resp.error["error_code"] == "DRY_RUN"
    api.config_set.assert_not_called()


# ---------------------------------------------------------------------------
# XPath generation
# ---------------------------------------------------------------------------


def test_security_rule_xpath_no_name(mock_settings):
    """security_rule_xpath() without name targets the rules container."""
    from pa_agent.panos_api import PanosAPI

    api = PanosAPI(mock_settings)
    xpath = api.security_rule_xpath()
    assert xpath.endswith("/rulebase/security/rules")
    assert "vsys1" in xpath


def test_security_rule_xpath_with_name(mock_settings):
    """security_rule_xpath(name) targets a specific rule entry."""
    from pa_agent.panos_api import PanosAPI

    api = PanosAPI(mock_settings)
    xpath = api.security_rule_xpath("Allow-Web")
    assert xpath.endswith("/entry[@name='Allow-Web']")
    assert "vsys1" in xpath
