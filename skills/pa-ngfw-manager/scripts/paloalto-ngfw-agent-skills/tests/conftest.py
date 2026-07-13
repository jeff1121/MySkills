from __future__ import annotations

import pytest

from pa_agent.config import Settings
from pa_agent.models import SecurityRule


@pytest.fixture
def mock_settings():
    """Settings with test values."""
    return Settings(
        PANOS_HOST="https://10.0.0.1",
        PANOS_API_KEY="test-api-key-12345",
        PANOS_VSYS="vsys1",
        PANOS_VERIFY_TLS=False,
        PANOS_TIMEOUT=10,
        BACKUP_DIR="/tmp/test-backups",
    )


@pytest.fixture
def sample_rule():
    """Sample SecurityRule for testing."""
    return SecurityRule(
        name="Allow-Web",
        from_zones=["trust"],
        to_zones=["untrust"],
        source=["10.0.0.0/8"],
        destination=["any"],
        service=["service-http", "service-https"],
        application=["web-browsing", "ssl"],
        action="allow",
        description="Allow web traffic",
        tags=["managed"],
    )


@pytest.fixture
def sample_panos_rule_xml():
    """Sample PAN-OS XML response for a security rule entry."""
    return '''<entry name="Allow-Web">
        <from><member>trust</member></from>
        <to><member>untrust</member></to>
        <source><member>10.0.0.0/8</member></source>
        <destination><member>any</member></destination>
        <service><member>service-http</member><member>service-https</member></service>
        <application><member>web-browsing</member><member>ssl</member></application>
        <action>allow</action>
        <disabled>no</disabled>
        <description>Allow web traffic</description>
        <tag><member>managed</member></tag>
    </entry>'''


@pytest.fixture
def sample_traffic_logs():
    """Sample traffic log entries for anomaly testing."""
    return [
        {"src": "10.1.1.1", "dst": "8.8.8.8", "dport": "443", "sport": "12345", "bytes": "1024", "packets": "10", "action": "allow", "app": "ssl", "rule": "Allow-Web", "receive_time": "2024/01/15 10:00:00"},
        {"src": "10.1.1.1", "dst": "8.8.4.4", "dport": "443", "sport": "12346", "bytes": "2048", "packets": "20", "action": "allow", "app": "ssl", "rule": "Allow-Web", "receive_time": "2024/01/15 10:01:00"},
        {"src": "10.1.1.1", "dst": "1.1.1.1", "dport": "53", "sport": "54321", "bytes": "128", "packets": "2", "action": "allow", "app": "dns", "rule": "Allow-DNS", "receive_time": "2024/01/15 10:02:00"},
        {"src": "10.1.1.2", "dst": "192.168.1.1", "dport": "80", "sport": "23456", "bytes": "512", "packets": "5", "action": "deny", "app": "web-browsing", "rule": "Deny-Default", "receive_time": "2024/01/15 10:03:00"},
        {"src": "10.1.1.2", "dst": "192.168.1.1", "dport": "22", "sport": "23457", "bytes": "256", "packets": "3", "action": "deny", "app": "ssh", "rule": "Deny-Default", "receive_time": "2024/01/15 10:04:00"},
    ]


@pytest.fixture
def sample_threat_logs():
    """Sample threat log entries."""
    return [
        {"src": "10.1.1.1", "dst": "8.8.8.8", "severity": "critical", "type": "vulnerability", "subtype": "exploit", "receive_time": "2024/01/15 10:00:00"},
        {"src": "10.1.1.3", "dst": "1.2.3.4", "severity": "high", "type": "spyware", "subtype": "phone-home", "receive_time": "2024/01/15 10:01:00"},
        {"src": "10.1.1.4", "dst": "5.6.7.8", "severity": "medium", "type": "virus", "subtype": "wildfire", "receive_time": "2024/01/15 10:02:00"},
    ]
