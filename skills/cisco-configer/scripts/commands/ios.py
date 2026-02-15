"""
IOS / IOS-XE 指令模組。
"""

__version__ = "0.1.0"

# 查詢意圖 → show 指令映射
_SHOW_COMMANDS: dict[str, list[str]] = {
    "interface": [
        "show ip interface brief",
        "show interfaces status",
    ],
    "vlan": [
        "show vlan brief",
    ],
    "routing": [
        "show ip route",
    ],
    "route": [
        "show ip route",
    ],
    "acl": [
        "show access-lists",
    ],
    "access-list": [
        "show access-lists",
    ],
    "bgp": [
        "show ip bgp summary",
        "show ip bgp",
    ],
    "ospf": [
        "show ip ospf neighbor",
        "show ip ospf interface brief",
    ],
    "eigrp": [
        "show ip eigrp neighbors",
        "show ip eigrp topology",
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
        "show ip arp",
    ],
    "mac": [
        "show mac address-table",
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
    "startup-config": [
        "show startup-config",
    ],
    "spanning-tree": [
        "show spanning-tree summary",
        "show spanning-tree",
    ],
    "stp": [
        "show spanning-tree summary",
    ],
    "etherchannel": [
        "show etherchannel summary",
    ],
    "port-channel": [
        "show etherchannel summary",
    ],
    "snmp": [
        "show snmp",
        "show snmp community",
    ],
    "dhcp": [
        "show ip dhcp binding",
        "show ip dhcp pool",
    ],
}

# 設定意圖 → config 指令映射（需搭配 params）
_CONFIG_TEMPLATES: dict[str, callable] = {}


def _config_vlan(params: dict) -> list[str]:
    vlan_id = params.get("id", "")
    name = params.get("name", "")
    cmds = [f"vlan {vlan_id}"]
    if name:
        cmds.append(f"name {name}")
    return cmds


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
        cmds.append(f"ip address {ip} {mask}")
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
    return [f"logging host {server}"]


def _config_acl(params: dict) -> list[str]:
    acl_name = params.get("name", "")
    entries = params.get("entries", [])
    cmds = [f"ip access-list extended {acl_name}"]
    for entry in entries:
        cmds.append(entry)
    return cmds


def _config_static_route(params: dict) -> list[str]:
    network = params.get("network", "")
    mask = params.get("mask", "")
    next_hop = params.get("next_hop", "")
    return [f"ip route {network} {mask} {next_hop}"]


_CONFIG_TEMPLATES = {
    "vlan": _config_vlan,
    "interface": _config_interface,
    "hostname": _config_hostname,
    "ntp": _config_ntp,
    "logging": _config_logging,
    "acl": _config_acl,
    "access-list": _config_acl,
    "static-route": _config_static_route,
    "route": _config_static_route,
}


def get_info_commands(intent: str) -> list[str]:
    """根據使用者意圖回傳對應的 show 指令清單。"""
    intent_lower = intent.strip().lower()

    # 完整 show 指令直接使用
    if intent_lower.startswith("show "):
        return [intent.strip()]

    # 在映射表中尋找匹配
    for key, commands in _SHOW_COMMANDS.items():
        if key in intent_lower:
            return commands

    # 未匹配時回傳通用指令
    return [f"show {intent.strip()}"]


def get_config_commands(intent: str, params: dict) -> list[str]:
    """根據使用者意圖與參數回傳對應的 config 指令清單。"""
    intent_lower = intent.strip().lower()

    for key, builder in _CONFIG_TEMPLATES.items():
        if key in intent_lower:
            return builder(params)

    # 未匹配時回傳原始意圖（可能是直接的 config 指令）
    return [intent.strip()]
