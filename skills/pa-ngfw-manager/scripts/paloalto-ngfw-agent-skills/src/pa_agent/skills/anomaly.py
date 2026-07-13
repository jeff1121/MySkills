"""Rule-based anomaly detection for PAN-OS traffic and threat logs."""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from pa_agent.errors import APIError
from pa_agent.log import get_logger
from pa_agent.models import AnomalyFinding, AnomalyReport, ToolResponse
from pa_agent.panos_api import PanosAPI

_log = get_logger(__name__)

_WINDOW_RE = re.compile(r"^(\d+)([mhd])$")
_UNIT_MAP = {"m": 60, "h": 3600, "d": 86400}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_window(window: str) -> int:
    """Parse window string like '15m', '1h', '24h', '7d' to seconds."""
    m = _WINDOW_RE.match(window.strip())
    if not m:
        raise ValueError(f"Invalid window format '{window}'. Use e.g. '15m', '1h', '24h', '7d'.")
    return int(m.group(1)) * _UNIT_MAP[m.group(2)]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _fmt_iso(dt: datetime) -> str:
    return dt.isoformat()


def _panos_time(dt: datetime) -> str:
    """Format datetime for PAN-OS log query filter."""
    return dt.strftime("%Y/%m/%d %H:%M:%S")


def _entry_to_dict(entry: ET.Element) -> dict[str, str]:
    """Convert a PAN-OS log <entry> element to a flat dict."""
    return {child.tag: (child.text or "") for child in entry}


async def _fetch_logs(
    api: PanosAPI,
    log_type: str,
    window_seconds: int,
    query_filter: str = "",
) -> list[dict]:
    """Fetch traffic or threat logs from PAN-OS.

    Sends the log query operational command and parses <entry> elements from
    the response.  For simplicity this issues a single request and parses
    whatever entries the device returns directly (works on PAN-OS versions
    that return results inline).
    """
    now = _now_utc()
    start = now - timedelta(seconds=window_seconds)
    time_filter = f"(receive_time geq '{_panos_time(start)}')"
    query = f"{time_filter} and {query_filter}" if query_filter else time_filter

    cmd = (
        f"<show><log><{log_type}>"
        f"<nlogs>5000</nlogs>"
        f"<direction>backward</direction>"
        f"<query>{query}</query>"
        f"</{log_type}></log></show>"
    )

    resp = await api.op_command(cmd)

    entries: list[dict] = []
    for entry in resp.iter("entry"):
        entries.append(_entry_to_dict(entry))

    _log.info("fetched_logs", log_type=log_type, count=len(entries), window_s=window_seconds)
    return entries


# ---------------------------------------------------------------------------
# Detection rules
# ---------------------------------------------------------------------------

def _rule_top_talker_surge(
    current_logs: list[dict],
    baseline_logs: list[dict],
    multiplier: float = 3.0,
) -> AnomalyFinding | None:
    """Single src IP traffic count exceeds baseline average * multiplier."""
    if not current_logs or not baseline_logs:
        return None

    cur_counts = Counter(e.get("src", "") for e in current_logs)
    base_counts = Counter(e.get("src", "") for e in baseline_logs)

    if not base_counts:
        return None

    baseline_avg = sum(base_counts.values()) / len(base_counts)
    threshold = baseline_avg * multiplier

    worst_ip, worst_count = cur_counts.most_common(1)[0]
    if worst_count <= threshold:
        return None

    now = _fmt_iso(_now_utc())
    return AnomalyFinding(
        rule_id="top_talker_surge",
        severity="medium",
        summary=f"Source {worst_ip} generated {worst_count} connections, exceeding baseline avg {baseline_avg:.0f} by {multiplier}x",
        evidence={
            "src_ip": worst_ip,
            "connections": worst_count,
            "baseline_avg": round(baseline_avg, 2),
            "multiplier": multiplier,
        },
        first_seen=now,
        last_seen=now,
    )


def _rule_port_scan(
    current_logs: list[dict],
    threshold: int = 50,
) -> AnomalyFinding | None:
    """Single src connecting to > threshold distinct dst ports."""
    if not current_logs:
        return None

    src_ports: dict[str, set[str]] = {}
    for e in current_logs:
        src = e.get("src", "")
        dport = e.get("dport", "")
        if src and dport:
            src_ports.setdefault(src, set()).add(dport)

    for src, ports in src_ports.items():
        if len(ports) > threshold:
            now = _fmt_iso(_now_utc())
            return AnomalyFinding(
                rule_id="port_scan",
                severity="high",
                summary=f"Source {src} connected to {len(ports)} distinct destination ports (threshold: {threshold})",
                evidence={
                    "src_ip": src,
                    "distinct_dst_ports": len(ports),
                    "threshold": threshold,
                    "sample_ports": sorted(ports)[:20],
                },
                first_seen=now,
                last_seen=now,
            )
    return None


def _rule_ddos_approx(
    current_logs: list[dict],
    baseline_logs: list[dict],
    multiplier: float = 5.0,
) -> AnomalyFinding | None:
    """Single dst receiving connections far exceeding baseline."""
    if not current_logs or not baseline_logs:
        return None

    cur_counts = Counter(e.get("dst", "") for e in current_logs)
    base_counts = Counter(e.get("dst", "") for e in baseline_logs)

    if not base_counts:
        return None

    baseline_avg = sum(base_counts.values()) / len(base_counts)
    threshold = baseline_avg * multiplier

    worst_dst, worst_count = cur_counts.most_common(1)[0]
    if worst_count <= threshold:
        return None

    now = _fmt_iso(_now_utc())
    return AnomalyFinding(
        rule_id="ddos_approx",
        severity="critical",
        summary=f"Destination {worst_dst} received {worst_count} connections, exceeding baseline avg {baseline_avg:.0f} by {multiplier}x",
        evidence={
            "dst_ip": worst_dst,
            "connections": worst_count,
            "baseline_avg": round(baseline_avg, 2),
            "multiplier": multiplier,
        },
        first_seen=now,
        last_seen=now,
    )


def _rule_suspicious_outbound(
    current_logs: list[dict],
    baseline_logs: list[dict],
) -> AnomalyFinding | None:
    """Flag when > 20% of current dst IPs were not seen in baseline."""
    if not current_logs or not baseline_logs:
        return None

    cur_dsts = {e.get("dst", "") for e in current_logs} - {""}
    base_dsts = {e.get("dst", "") for e in baseline_logs} - {""}

    if not cur_dsts:
        return None

    new_dsts = cur_dsts - base_dsts
    pct = len(new_dsts) / len(cur_dsts) * 100

    if pct <= 20.0:
        return None

    now = _fmt_iso(_now_utc())
    return AnomalyFinding(
        rule_id="suspicious_outbound",
        severity="medium",
        summary=f"{pct:.1f}% of destination IPs ({len(new_dsts)}/{len(cur_dsts)}) are new compared to baseline",
        evidence={
            "new_dst_count": len(new_dsts),
            "total_dst_count": len(cur_dsts),
            "new_dst_pct": round(pct, 2),
            "sample_new_dsts": sorted(new_dsts)[:20],
        },
        first_seen=now,
        last_seen=now,
    )


def _rule_threat_severity_spike(
    current_threats: list[dict],
    baseline_threats: list[dict],
    multiplier: float = 3.0,
) -> AnomalyFinding | None:
    """High-severity threat events rate increase vs baseline."""
    _HIGH = {"critical", "high"}

    cur_high = sum(1 for e in current_threats if e.get("severity", "").lower() in _HIGH)
    base_high = sum(1 for e in baseline_threats if e.get("severity", "").lower() in _HIGH)

    if base_high == 0:
        if cur_high > 0:
            now = _fmt_iso(_now_utc())
            return AnomalyFinding(
                rule_id="threat_severity_spike",
                severity="high",
                summary=f"{cur_high} high/critical threat events detected with none in baseline",
                evidence={
                    "current_high_count": cur_high,
                    "baseline_high_count": base_high,
                },
                first_seen=now,
                last_seen=now,
            )
        return None

    if cur_high <= base_high * multiplier:
        return None

    now = _fmt_iso(_now_utc())
    return AnomalyFinding(
        rule_id="threat_severity_spike",
        severity="high",
        summary=f"High/critical threats spiked to {cur_high} (baseline: {base_high}, multiplier: {multiplier}x)",
        evidence={
            "current_high_count": cur_high,
            "baseline_high_count": base_high,
            "multiplier": multiplier,
        },
        first_seen=now,
        last_seen=now,
    )


def _rule_deny_rate_anomaly(
    current_logs: list[dict],
    baseline_logs: list[dict],
    multiplier: float = 2.0,
) -> AnomalyFinding | None:
    """Policy deny hit rate exceeds baseline * multiplier."""
    cur_deny = sum(1 for e in current_logs if e.get("action", "").lower() == "deny")
    base_deny = sum(1 for e in baseline_logs if e.get("action", "").lower() == "deny")

    if base_deny == 0:
        if cur_deny > 0:
            now = _fmt_iso(_now_utc())
            return AnomalyFinding(
                rule_id="deny_rate_anomaly",
                severity="medium",
                summary=f"{cur_deny} deny actions detected with none in baseline",
                evidence={
                    "current_deny_count": cur_deny,
                    "baseline_deny_count": base_deny,
                },
                first_seen=now,
                last_seen=now,
            )
        return None

    if cur_deny <= base_deny * multiplier:
        return None

    now = _fmt_iso(_now_utc())
    return AnomalyFinding(
        rule_id="deny_rate_anomaly",
        severity="medium",
        summary=f"Deny rate spiked to {cur_deny} (baseline: {base_deny}, multiplier: {multiplier}x)",
        evidence={
            "current_deny_count": cur_deny,
            "baseline_deny_count": base_deny,
            "multiplier": multiplier,
        },
        first_seen=now,
        last_seen=now,
    )


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------

async def detect(
    api: PanosAPI,
    window: str = "1h",
    baseline: str = "24h",
    thresholds: dict | None = None,
) -> ToolResponse:
    """Run all anomaly detection rules against PAN-OS logs.

    Returns a ToolResponse wrapping an AnomalyReport with findings and any
    data gaps encountered during collection.
    """
    thresholds = thresholds or {}
    findings: list[AnomalyFinding] = []
    data_gaps: list[str] = []

    try:
        window_s = _parse_window(window)
        baseline_s = _parse_window(baseline)
    except ValueError as exc:
        return ToolResponse(ok=False, error={"error_code": "VALIDATION_ERROR", "message": str(exc), "remediation": "Use formats like '15m', '1h', '24h', '7d'."})

    # -- Fetch logs ----------------------------------------------------------
    current_traffic: list[dict] = []
    baseline_traffic: list[dict] = []
    current_threats: list[dict] = []
    baseline_threats: list[dict] = []

    try:
        current_traffic = await _fetch_logs(api, "traffic", window_s)
        baseline_traffic = await _fetch_logs(api, "traffic", baseline_s)
    except (APIError, Exception) as exc:
        _log.warning("traffic_logs_unavailable", error=str(exc))
        data_gaps.append("traffic_logs_unavailable")

    try:
        current_threats = await _fetch_logs(api, "threat", window_s)
        baseline_threats = await _fetch_logs(api, "threat", baseline_s)
    except (APIError, Exception) as exc:
        _log.warning("threat_logs_unavailable", error=str(exc))
        data_gaps.append("threat_logs_unavailable")

    # -- Run rules -----------------------------------------------------------
    rules: list[tuple[str, Any]] = [
        (
            "top_talker_surge",
            lambda: _rule_top_talker_surge(
                current_traffic,
                baseline_traffic,
                multiplier=thresholds.get("top_talker_multiplier", 3.0),
            ),
        ),
        (
            "port_scan",
            lambda: _rule_port_scan(
                current_traffic,
                threshold=thresholds.get("port_scan_threshold", 50),
            ),
        ),
        (
            "ddos_approx",
            lambda: _rule_ddos_approx(
                current_traffic,
                baseline_traffic,
                multiplier=thresholds.get("ddos_multiplier", 5.0),
            ),
        ),
        (
            "suspicious_outbound",
            lambda: _rule_suspicious_outbound(current_traffic, baseline_traffic),
        ),
        (
            "threat_severity_spike",
            lambda: _rule_threat_severity_spike(
                current_threats,
                baseline_threats,
                multiplier=thresholds.get("threat_spike_multiplier", 3.0),
            ),
        ),
        (
            "deny_rate_anomaly",
            lambda: _rule_deny_rate_anomaly(
                current_traffic,
                baseline_traffic,
                multiplier=thresholds.get("deny_rate_multiplier", 2.0),
            ),
        ),
    ]

    for rule_name, run in rules:
        try:
            finding = run()
            if finding is not None:
                findings.append(finding)
        except Exception:
            _log.exception("rule_failed", rule=rule_name)
            data_gaps.append(f"rule_{rule_name}_error")

    report = AnomalyReport(
        findings=findings,
        data_gaps=data_gaps,
        window=window,
        baseline=baseline,
    )

    return ToolResponse(ok=True, result=report.model_dump())
