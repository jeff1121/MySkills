"""Tests for anomaly detection rules against sample data."""

from __future__ import annotations

import pytest

from pa_agent.skills.anomaly import (
    _parse_window,
    _rule_deny_rate_anomaly,
    _rule_port_scan,
    _rule_suspicious_outbound,
    _rule_top_talker_surge,
)


# ---------------------------------------------------------------------------
# _parse_window
# ---------------------------------------------------------------------------


class TestParseWindow:
    def test_15m(self):
        assert _parse_window("15m") == 900

    def test_1h(self):
        assert _parse_window("1h") == 3600

    def test_24h(self):
        assert _parse_window("24h") == 86400

    def test_7d(self):
        assert _parse_window("7d") == 604800

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_window("10x")


# ---------------------------------------------------------------------------
# _rule_port_scan
# ---------------------------------------------------------------------------


def test_port_scan_detected_above_threshold():
    """A source connecting to >50 unique dst ports triggers a finding."""
    logs = [
        {"src": "10.1.1.99", "dport": str(p)} for p in range(60)
    ]
    finding = _rule_port_scan(logs, threshold=50)
    assert finding is not None
    assert finding.rule_id == "port_scan"
    assert finding.severity == "high"
    assert finding.evidence["distinct_dst_ports"] == 60


def test_port_scan_not_detected_below_threshold():
    """Normal traffic (< threshold) produces no finding."""
    logs = [
        {"src": "10.1.1.99", "dport": str(p)} for p in range(10)
    ]
    finding = _rule_port_scan(logs, threshold=50)
    assert finding is None


# ---------------------------------------------------------------------------
# _rule_top_talker_surge
# ---------------------------------------------------------------------------


def test_top_talker_surge_detected():
    """Surge traffic exceeding baseline * multiplier triggers a finding."""
    baseline = [{"src": f"10.0.0.{i}"} for i in range(10)]
    # One IP generates 50 connections — baseline avg is 1
    current = [{"src": "10.1.1.1"}] * 50
    finding = _rule_top_talker_surge(current, baseline, multiplier=3.0)
    assert finding is not None
    assert finding.rule_id == "top_talker_surge"
    assert finding.evidence["src_ip"] == "10.1.1.1"


def test_top_talker_surge_not_detected():
    """Traffic within baseline * multiplier produces no finding."""
    baseline = [{"src": "10.0.0.1"}] * 10
    current = [{"src": "10.0.0.1"}] * 10
    finding = _rule_top_talker_surge(current, baseline, multiplier=3.0)
    assert finding is None


# ---------------------------------------------------------------------------
# _rule_deny_rate_anomaly
# ---------------------------------------------------------------------------


def test_deny_rate_anomaly_high_vs_low():
    """High deny count vs low baseline triggers a finding."""
    baseline = [{"action": "deny"}] * 5 + [{"action": "allow"}] * 95
    current = [{"action": "deny"}] * 50 + [{"action": "allow"}] * 50
    finding = _rule_deny_rate_anomaly(current, baseline, multiplier=2.0)
    assert finding is not None
    assert finding.rule_id == "deny_rate_anomaly"
    assert finding.evidence["current_deny_count"] == 50


def test_deny_rate_anomaly_within_baseline():
    """Deny rate within multiplier produces no finding."""
    baseline = [{"action": "deny"}] * 10
    current = [{"action": "deny"}] * 15
    finding = _rule_deny_rate_anomaly(current, baseline, multiplier=2.0)
    assert finding is None


# ---------------------------------------------------------------------------
# _rule_suspicious_outbound
# ---------------------------------------------------------------------------


def test_suspicious_outbound_new_destinations():
    """Over 20% new destination IPs vs baseline triggers a finding."""
    baseline = [{"dst": f"1.1.1.{i}"} for i in range(5)]
    # All current dsts are new
    current = [{"dst": f"9.9.9.{i}"} for i in range(10)]
    finding = _rule_suspicious_outbound(current, baseline)
    assert finding is not None
    assert finding.rule_id == "suspicious_outbound"
    assert finding.evidence["new_dst_pct"] == 100.0


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------


def test_empty_logs_no_crash():
    """Empty log lists produce no findings and no crash."""
    assert _rule_port_scan([], threshold=50) is None
    assert _rule_top_talker_surge([], [], multiplier=3.0) is None
    assert _rule_deny_rate_anomaly([], [], multiplier=2.0) is None
    assert _rule_suspicious_outbound([], []) is None
