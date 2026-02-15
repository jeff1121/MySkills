"""
IOS-XR 指令模組（電信級路由器）。
"""

__version__ = "0.1.0"

# 查詢意圖 → show 指令映射
_SHOW_COMMANDS: dict[str, list[str]] = {
    "interface": [
        "show ip interface brief",
        "show interfaces summary",
    ],
    "routing": [
        "show route",
    ],
    "route": [
        "show route",
    ],
    "acl": [
        "show access-lists",
    ],
    "access-list": [
        "show access-lists",
    ],
    "bgp": [
        "show bgp summary",
        "show bgp ipv4 unicast",
    ],
    "ospf": [
        "show ospf neighbor",
        "show ospf interface brief",
    ],
    "isis": [
        "show isis neighbors",
        "show isis interface brief",
    ],
    "mpls": [
        "show mpls interfaces",
        "show mpls forwarding",
        "show mpls ldp neighbor brief",
    ],
    "segment-routing": [
        "show segment-routing local-block",
        "show isis segment-routing label table",
    ],
    "cdp": [
        "show cdp neighbors detail",
    ],
    "lldp": [
        "show lldp neighbors detail",
    ],
    "neighbor": [
        "show cdp neighbors detail",
        "show lldp neighbors detail",
    ],
    "arp": [
        "show arp",
    ],
    "ntp": [
        "show ntp status",
        "show ntp associations",
    ],
    "logging": [
        "show logging",
    ],
    "version": [
        "show version",
    ],
    "inventory": [
        "show inventory",
    ],
    "running-config": [
        "show running-config",
    ],
    "platform": [
        "show platform",
    ],
    "snmp": [
        "show snmp",
    ],
    "bfd": [
        "show bfd session",
    ],
    "bundle": [
        "show bundle",
    ],
}


def _config_interface(params: dict) -> list[str]:
    name = params.get("name", "")
    ip = params.get("ip", "")
    mask = params.get("mask", "")
    shutdown = params.get("shutdown", False)
    description = params.get("description", "")
    cmds = [f"interface {name}"]
    if description:
        cmds.append(f"description {description}")
    if ip and mask:
        cmds.append(f"ipv4 address {ip} {mask}")
    if shutdown:
        cmds.append("shutdown")
    else:
        cmds.append("no shutdown")
    return cmds


def _config_hostname(params: dict) -> list[str]:
    hostname = params.get("hostname", "")
    return [f"hostname {hostname}"]


def _config_ntp(params: dict) -> list[str]:
    server = params.get("server", "")
    return [f"ntp server {server}"]


def _config_logging(params: dict) -> list[str]:
    server = params.get("server", "")
    return [f"logging {server}"]


def _config_static_route(params: dict) -> list[str]:
    network = params.get("network", "")
    mask = params.get("mask", "")
    next_hop = params.get("next_hop", "")
    return [f"router static address-family ipv4 unicast {network}/{mask} {next_hop}"]


def _config_acl(params: dict) -> list[str]:
    acl_name = params.get("name", "")
    entries = params.get("entries", [])
    cmds = [f"ipv4 access-list {acl_name}"]
    for entry in entries:
        cmds.append(f" {entry}")
    return cmds


_CONFIG_TEMPLATES: dict[str, callable] = {
    "interface": _config_interface,
    "hostname": _config_hostname,
    "ntp": _config_ntp,
    "logging": _config_logging,
    "static-route": _config_static_route,
    "route": _config_static_route,
    "acl": _config_acl,
    "access-list": _config_acl,
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
