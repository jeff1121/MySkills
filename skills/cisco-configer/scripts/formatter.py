"""
Cisco 設備輸出排版美化。
"""
import re

__version__ = "0.1.0"

# show 指令對應的格式化策略
_TABLE_COMMANDS = {
    "show ip interface brief",
    "show interfaces status",
    "show vlan brief",
    "show cdp neighbors",
    "show lldp neighbors",
    "show ip bgp summary",
    "show ip ospf neighbor",
    "show port-channel summary",
    "show etherchannel summary",
    "show ip arp",
    "show mac address-table",
}

_ROUTING_COMMANDS = {
    "show ip route",
    "show ipv6 route",
    "show ip bgp",
}

_CONFIG_COMMANDS = {
    "show running-config",
    "show startup-config",
}


def format_output(raw: str, command: str) -> str:
    """主入口：根據指令類型路由到對應格式化邏輯。"""
    cleaned = strip_ansi(raw)
    cleaned = strip_command_echo(cleaned, command)

    cmd_lower = command.strip().lower()

    for table_cmd in _TABLE_COMMANDS:
        if cmd_lower.startswith(table_cmd):
            return format_table_output(cleaned)

    for route_cmd in _ROUTING_COMMANDS:
        if cmd_lower.startswith(route_cmd):
            return format_routing_output(cleaned)

    for config_cmd in _CONFIG_COMMANDS:
        if cmd_lower.startswith(config_cmd):
            return format_config_output(cleaned)

    return cleaned.strip()


def format_table_output(raw: str) -> str:
    """將空白分隔的表格輸出轉為 Markdown 表格。"""
    lines = [line for line in raw.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return raw.strip()

    header_line = lines[0]
    headers = header_line.split()
    if not headers:
        return raw.strip()

    # 嘗試根據表頭位置解析各欄位
    col_positions = _detect_column_positions(header_line)
    col_count = len(headers)

    rows: list[list[str]] = []
    for line in lines[1:]:
        # 跳過分隔線（含空格 + 連字號/等號）
        if re.match(r"^[-=\s]+$", line.strip()):
            continue
        if col_positions:
            row = _split_by_positions(line, col_positions)
        else:
            row = line.split()

        # 偵測續行（第一欄為空表示此行是上一行的延續）
        if rows and row and not row[0] and any(c for c in row):
            for i, cell in enumerate(row):
                if cell and i < len(rows[-1]):
                    prev = rows[-1][i]
                    rows[-1][i] = f"{prev}, {cell}" if prev else cell
            continue

        rows.append(row)

    if not rows:
        return raw.strip()

    # 計算各欄位寬度（最後一欄不限制）
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < col_count - 1:
                widths[i] = max(widths[i], len(cell))

    # 最後一欄寬度取表頭長度即可（不額外填充）
    last_col_width = len(headers[-1]) if headers else 0
    widths[-1] = last_col_width

    # 輸出 Markdown 表格
    result_lines: list[str] = []
    header_parts = [h.ljust(widths[i]) for i, h in enumerate(headers)]
    result_lines.append("| " + " | ".join(header_parts) + " |")
    result_lines.append("| " + " | ".join("-" * w for w in widths) + " |")

    for row in rows:
        cells = []
        for i in range(col_count):
            cell = row[i] if i < len(row) else ""
            if i < col_count - 1:
                cells.append(cell.ljust(widths[i]))
            else:
                cells.append(cell)
        result_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(result_lines)


def format_config_output(raw: str) -> str:
    """格式化設定輸出，依區塊分段並加入空行。"""
    lines = raw.strip().splitlines()
    result: list[str] = []
    prev_indent = 0

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue

        curr_indent = len(line) - len(line.lstrip())

        # 新區塊開始（頂層指令切換時加空行）
        if curr_indent == 0 and prev_indent > 0 and result:
            result.append("")

        # 區塊起始行（如 interface、router、line 等）加空行
        if curr_indent == 0 and stripped.startswith(("!", "end")):
            if result and result[-1] != "":
                result.append("")
            if stripped == "!":
                continue

        result.append(stripped)
        prev_indent = curr_indent

    return "\n".join(result)


def format_routing_output(raw: str) -> str:
    """美化路由表輸出。"""
    lines = raw.strip().splitlines()
    result: list[str] = []

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue

        # 路由條目（以協定代碼開頭，如 C、S、O、B、D 等）
        route_match = re.match(
            r"^([A-Z*]\S*)\s+(\S+)\s+(.*)$", stripped
        )
        if route_match:
            code, network, rest = route_match.groups()
            result.append(f"  {code:<6} {network:<20} {rest}")
        else:
            result.append(stripped)

    return "\n".join(result)


def strip_ansi(raw: str) -> str:
    """移除 ANSI 控制字元。"""
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", raw)


def strip_command_echo(raw: str, command: str) -> str:
    """移除指令回顯與設備提示符。"""
    lines = raw.splitlines()
    result: list[str] = []

    for line in lines:
        stripped = line.strip()
        # 跳過指令回顯
        if stripped == command.strip():
            continue
        # 跳過設備提示符（如 Router#、Switch>、ciscoasa#）
        if re.match(r"^\S+[#>]\s*$", stripped):
            continue
        result.append(line)

    return "\n".join(result)


def _detect_column_positions(header_line: str) -> list[int]:
    """偵測表頭各欄位的起始位置。"""
    positions: list[int] = []
    in_word = False
    for i, char in enumerate(header_line):
        if char != " " and not in_word:
            positions.append(i)
            in_word = True
        elif char == " ":
            in_word = False
    return positions


def _find_split_gap(line: str, pos: int, drift: int = 3) -> int:
    """在 pos 附近找到最佳欄位分割點（空白邊界）。

    資料值可能與表頭偏移 1-2 字元，此函式在 ±drift 範圍內搜尋
    最近的空格作為分割點，優先向左搜尋。
    """
    n = len(line)
    if pos >= n or line[pos] == " ":
        return pos
    for d in range(1, drift + 1):
        p = pos - d
        if p >= 0 and line[p] == " ":
            return p
    for d in range(1, drift + 1):
        p = pos + d
        if p < n and line[p] == " ":
            return p
    return pos


def _split_by_positions(line: str, positions: list[int]) -> list[str]:
    """根據欄位位置分割資料行，自動修正偏移對齊。"""
    # 預先計算各欄位的修正分割點
    adjusted = [positions[0]]
    for i in range(1, len(positions)):
        adjusted.append(_find_split_gap(line, positions[i]))

    parts: list[str] = []
    n = len(line)
    for i in range(len(adjusted)):
        start = adjusted[i]
        end = adjusted[i + 1] if i + 1 < len(adjusted) else n
        cell = line[start:end] if start < n else ""
        parts.append(cell.strip())
    return parts
