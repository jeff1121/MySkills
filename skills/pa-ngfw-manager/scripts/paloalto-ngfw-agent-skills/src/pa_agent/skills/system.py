"""System resource usage monitoring skill for PAN-OS."""

from __future__ import annotations

import re

from pa_agent.errors import APIError
from pa_agent.log import get_logger
from pa_agent.models import SystemUsage, ToolResponse
from pa_agent.panos_api import PanosAPI

logger = get_logger(__name__)


def _parse_cpu(text: str) -> float | None:
    """Extract CPU usage from top-like output.

    Looks for ``%Cpu(s):`` line and computes used% as ``100 - idle``.
    """
    for line in text.splitlines():
        if "%Cpu(s):" in line:
            # Example: %Cpu(s):  1.2 us,  0.3 sy,  0.0 ni, 98.0 id, ...
            m = re.search(r"([\d.]+)\s*id", line)
            if m:
                return round(100.0 - float(m.group(1)), 1)
    return None


def _parse_memory(text: str) -> float | None:
    """Extract memory usage percentage from top-like output.

    Handles both ``MiB Mem`` and ``KiB Mem`` formats.
    """
    for line in text.splitlines():
        if "Mem" in line and ("MiB" in line or "KiB" in line):
            # Example: MiB Mem :  3936.7 total,   200.1 free,  2100.3 used, ...
            total_m = re.search(r"([\d.]+)\s*total", line)
            used_m = re.search(r"([\d.]+)\s*used", line)
            if total_m and used_m:
                total = float(total_m.group(1))
                used = float(used_m.group(1))
                if total > 0:
                    return round(used / total * 100.0, 1)
    return None


async def get_usage(api: PanosAPI) -> ToolResponse:
    """Get system resource usage from PAN-OS.

    Collects CPU, memory, session, and dataplane metrics via separate
    operational commands.  Each command is independent — a failure in one
    does not prevent the others from returning data.
    """
    cpu_percent: float | None = None
    memory_percent: float | None = None
    sessions_active: int | None = None
    sessions_max: int | None = None
    dp_load: float | None = None

    # 1. System resources (CPU / Memory)
    try:
        res = await api.op_command(
            "<show><system><resources/></system></show>"
        )
        text = res.text or ""
        cpu_percent = _parse_cpu(text)
        memory_percent = _parse_memory(text)
    except APIError as exc:
        logger.warning("system_resources_unavailable", error=str(exc))

    # 2. Session info
    try:
        res = await api.op_command(
            "<show><session><info/></session></show>"
        )
        num_active_el = res.find(".//num-active")
        num_max_el = res.find(".//num-max")
        if num_active_el is not None and num_active_el.text:
            sessions_active = int(num_active_el.text)
        if num_max_el is not None and num_max_el.text:
            sessions_max = int(num_max_el.text)
    except APIError as exc:
        logger.warning("session_info_unavailable", error=str(exc))

    # 3. Dataplane utilization (optional)
    try:
        res = await api.op_command(
            "<show><running><resource-monitor><second>"
            "<last>1</last>"
            "</second></resource-monitor></running></show>"
        )
        dp_el = res.find(".//dp-cpu-load-average")
        if dp_el is not None and dp_el.text:
            dp_load = round(float(dp_el.text), 1)
    except APIError as exc:
        logger.warning("dataplane_load_unavailable", error=str(exc))

    usage = SystemUsage(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        sessions_active=sessions_active,
        sessions_max=sessions_max,
        dp_load=dp_load,
    )
    return ToolResponse(ok=True, result=usage.model_dump())
