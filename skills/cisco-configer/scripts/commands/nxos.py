"""
NX-OS 指令模組（Nexus 資料中心交換機）。
"""

__version__ = "0.1.0"

# 查詢意圖 → show 指令映射
_SHOW_COMMANDS: dict[str, list[str]] = {
    "interface": [
        "show ip interface brief",
        "show interface status",
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
        "show ip ospf neighbors",
        "show ip ospf interface brief",
    ],
    "eigrp": [
        "show ip eigrp neighbors",
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
        "show ntp peer-status",
    ],
    "logging": [
        "show logging last 50",
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
    "port-channel": [
        "show port-channel summary",
    ],
    "vpc": [
        "show vpc",
        "show vpc brief",
    ],
    "feature": [
        "show feature",
    ],
    "spanning-tree": [
        "show spanning-tree summary",
    ],
    "stp": [
        "show spanning-tree summary",
    ],
    "hsrp": [
        "show hsrp brief",
    ],
    "vrrp": [
        "show vrrp brief",
    ],
    "snmp": [
        "show snmp community",
    ],
}


def _config_feature(params: dict) -> list[str]:
    feature_name = params.get("name", "")
    return [f"feature {feature_name}"]


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
        cmds.append("no switchport")
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
    return [f"logging server {server}"]


def _config_vpc(params: dict) -> list[str]:
    domain_id = params.get("domain_id", "")
    peer_ip = params.get("peer_ip", "")
    cmds = [
        "feature vpc",
        f"vpc domain {domain_id}",
    ]
    if peer_ip:
        cmds.append(f"peer-keepalive destination {peer_ip}")
    return cmds


_CONFIG_TEMPLATES: dict[str, callable] = {
    "feature": _config_feature,
    "vlan": _config_vlan,
    "interface": _config_interface,
    "hostname": _config_hostname,
    "ntp": _config_ntp,
    "logging": _config_logging,
    "vpc": _config_vpc,
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
