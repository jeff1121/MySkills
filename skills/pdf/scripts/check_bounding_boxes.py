"""檢查 fields.json 的 bounding box 是否有重疊或高度不足問題。

驗證所有標籤與輸入區域的矩形不互相交疊，且輸入區域高度足以容納字型大小。
詳見 forms.md。
"""

from dataclasses import dataclass
import argparse
import json
import sys
from typing import IO

from common import (
    setup_logging, validate_file_exists, add_common_args, logger,
    MAX_FORM_FIELDS,
)


@dataclass
class RectAndField:
    rect: list[float]
    rect_type: str
    field: dict


def get_bounding_box_messages(fields_json_stream: IO[str]) -> list[str]:
    """驗證 bounding box 並回傳訊息清單（供呼叫端列印）。"""
    messages = []
    fields = json.load(fields_json_stream)

    form_fields = fields.get("form_fields", [])
    if len(form_fields) > MAX_FORM_FIELDS:
        messages.append(
            f"ERROR: form_fields 數量 ({len(form_fields)}) 超過上限 ({MAX_FORM_FIELDS})，中止檢查"
        )
        return messages

    messages.append(f"Read {len(form_fields)} fields")

    def rects_intersect(r1, r2):
        disjoint_horizontal = r1[0] >= r2[2] or r1[2] <= r2[0]
        disjoint_vertical = r1[1] >= r2[3] or r1[3] <= r2[1]
        return not (disjoint_horizontal or disjoint_vertical)

    rects_and_fields = []
    for f in form_fields:
        rects_and_fields.append(RectAndField(f["label_bounding_box"], "label", f))
        rects_and_fields.append(RectAndField(f["entry_bounding_box"], "entry", f))

    has_error = False
    for i, ri in enumerate(rects_and_fields):
        # O(N²) 碰撞檢測；欄位數量已受 MAX_FORM_FIELDS 限制
        for j in range(i + 1, len(rects_and_fields)):
            rj = rects_and_fields[j]
            if ri.field["page_number"] == rj.field["page_number"] and rects_intersect(ri.rect, rj.rect):
                has_error = True
                if ri.field is rj.field:
                    messages.append(f"FAILURE: intersection between label and entry bounding boxes for `{ri.field['description']}` ({ri.rect}, {rj.rect})")
                else:
                    messages.append(f"FAILURE: intersection between {ri.rect_type} bounding box for `{ri.field['description']}` ({ri.rect}) and {rj.rect_type} bounding box for `{rj.field['description']}` ({rj.rect})")
                if len(messages) >= 20:
                    messages.append("Aborting further checks; fix bounding boxes and try again")
                    return messages
        if ri.rect_type == "entry":
            if "entry_text" in ri.field:
                font_size = ri.field["entry_text"].get("font_size", 14)
                entry_height = ri.rect[3] - ri.rect[1]
                if entry_height < font_size:
                    has_error = True
                    messages.append(f"FAILURE: entry bounding box height ({entry_height}) for `{ri.field['description']}` is too short for the text content (font size: {font_size}). Increase the box height or decrease the font size.")
                    if len(messages) >= 20:
                        messages.append("Aborting further checks; fix bounding boxes and try again")
                        return messages

    if not has_error:
        messages.append("SUCCESS: All bounding boxes are valid")
    return messages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="檢查 fields.json 的 bounding box 是否有效",
    )
    parser.add_argument("fields_json", help="fields.json 檔案路徑")
    add_common_args(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        real_path = validate_file_exists(args.fields_json, "fields.json")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    with open(real_path) as f:
        messages = get_bounding_box_messages(f)
    for msg in messages:
        print(msg)
