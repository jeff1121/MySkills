"""
ASA 指令模組（Cisco ASA 防火牆）。
"""

__version__ = "0.1.0"

# 查詢意圖 → show 指令映射
_SHOW_COMMANDS: dict[str, list[str]] = {
    "interface": [
        "show interface ip brief",
        "show interface summary",
    ],
    "routing": [
        "show route",
    ],
    "route": [
        "show route",
    ],
    "acl": [
        "show access-list",
    ],
    "access-list": [
        "show access-list",
    ],
    "nat": [
        "show nat",
        "show xlate",
    ],
    "xlate": [
        "show xlate",
    ],
    "conn": [
        "show conn count",
        "show conn",
    ],
    "connection": [
        "show conn count",
        "show conn",
    ],
    "vpn": [
        "show vpn-sessiondb summary",
        "show crypto ipsec sa",
    ],
    "ipsec": [
        "show crypto ipsec sa",
    ],
    "failover": [
        "show failover",
    ],
    "context": [
        "show context",
    ],
    "logging": [
        "show logging",
    ],
    "version": [
        "show version",
    ],
    "running-config": [
        "show running-config",
    ],
    "startup-config": [
        "show startup-config",
    ],
    "arp": [
        "show arp",
    ],
    "ntp": [
        "show ntp status",
        "show ntp associations",
    ],
    "snmp": [
        "show snmp-server community",
    ],
    "object": [
        "show object",
        "show object-group",
    ],
    "service-policy": [
        "show service-policy",
    ],
}


def _config_interface(params: dict) -> list[str]:
    name = params.get("name", "")
    ip = params.get("ip", "")
    mask = params.get("mask", "")
    nameif = params.get("nameif", "")
    security_level = params.get("security_level", "")
    shutdown = params.get("shutdown", False)
    cmds = [f"interface {name}"]
    if nameif:
        cmds.append(f"nameif {nameif}")
    if security_level:
        cmds.append(f"security-level {security_level}")
    if ip and mask:
        cmds.append(f"ip address {ip} {mask}")
    if shutdown:
        cmds.append("shutdown")
    else:
        cmds.append("no shutdown")
    return cmds


def _config_acl(params: dict) -> list[str]:
    acl_name = params.get("name", "")
    entries = params.get("entries", [])
    cmds = []
    for entry in entries:
        cmds.append(f"access-list {acl_name} {entry}")
    return cmds


def _config_nat(params: dict) -> list[str]:
    source_if = params.get("source_interface", "inside")
    dest_if = params.get("destination_interface", "outside")
    source = params.get("source", "")
    translated = params.get("translated", "")
    return [
        f"nat ({source_if},{dest_if}) source static {source} {translated}"
    ]


def _config_route(params: dict) -> list[str]:
    interface = params.get("interface", "outside")
    network = params.get("network", "")
    mask = params.get("mask", "")
    next_hop = params.get("next_hop", "")
    return [f"route {interface} {network} {mask} {next_hop}"]


def _config_hostname(params: dict) -> list[str]:
    hostname = params.get("hostname", "")
    return [f"hostname {hostname}"]


def _config_ntp(params: dict) -> list[str]:
    server = params.get("server", "")
    return [f"ntp server {server}"]


def _config_logging(params: dict) -> list[str]:
    server = params.get("server", "")
    return [f"logging host {server}"]


_CONFIG_TEMPLATES: dict[str, callable] = {
    "interface": _config_interface,
    "acl": _config_acl,
    "access-list": _config_acl,
    "nat": _config_nat,
    "route": _config_route,
    "hostname": _config_hostname,
    "ntp": _config_ntp,
    "logging": _config_logging,
}


def get_info_commands(intent: str) -> list[str]:
    """根據使用者意圖回傳對應的 show 指令清單。"""
    intent_lower = intent.strip().lower()

    if intent_lower.startswith("show "):
        return [intent.strip()]

    for key, commands in _SHOW_COMMANDS.items():
        if key in intent_lower:
            return commands

    return [f"show {intent.strip()}"]


def get_config_commands(intent: str, params: dict) -> list[str]:
    """根據使用者意圖與參數回傳對應的 config 指令清單。"""
    intent_lower = intent.strip().lower()

    for key, builder in _CONFIG_TEMPLATES.items():
        if key in intent_lower:
            return builder(params)

    return [intent.strip()]
