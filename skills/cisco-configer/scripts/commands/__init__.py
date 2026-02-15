"""
平台指令模組工廠。
"""
from types import ModuleType

__version__ = "0.1.0"

_PLATFORM_MAP: dict[str, str] = {
    "cisco_ios": "commands.ios",
    "cisco_xe": "commands.ios",
    "cisco_nxos": "commands.nxos",
    "cisco_asa": "commands.asa",
    "cisco_xr": "commands.iosxr",
}


def get_platform_module(device_type: str) -> ModuleType:
    """根據平台類型回傳對應的指令模組。"""
    import importlib

    module_path = _PLATFORM_MAP.get(device_type)
    if not module_path:
        # 預設使用 IOS 模組
        module_path = "commands.ios"

    return importlib.import_module(module_path)
