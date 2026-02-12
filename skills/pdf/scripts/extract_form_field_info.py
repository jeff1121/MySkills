"""提取 PDF 中可填寫表單欄位的資訊並輸出 JSON。

解析 PDF 的表單欄位定義與頁面註解，產生包含欄位 ID、類型、
頁碼、座標等資訊的 JSON 檔案。詳見 forms.md。
"""

import argparse
import json
import sys

from pypdf import PdfReader

from common import (
    setup_logging, validate_file_exists, validate_output_path,
    add_common_args, add_force_arg, logger,
)


def get_full_annotation_field_id(annotation) -> str | None:
    """取得註解的完整欄位 ID（以 '.' 串接父子層級）。

    此格式與 PdfReader 的 get_fields() 和
    update_page_form_field_values() 方法一致。
    """
    components = []
    while annotation:
        field_name = annotation.get('/T')
        if field_name:
            components.append(field_name)
        annotation = annotation.get('/Parent')
    return ".".join(reversed(components)) if components else None


def make_field_dict(field, field_id: str) -> dict:
    """將 PDF 欄位物件轉為結構化字典。"""
    field_dict = {"field_id": field_id}
    ft = field.get('/FT')
    if ft == "/Tx":
        field_dict["type"] = "text"
    elif ft == "/Btn":
        field_dict["type"] = "checkbox"  # radio group 另外處理
        states = field.get("/_States_", [])
        if len(states) == 2:
            # "/Off" 通常代表未勾選狀態
            # 參考: PDF32000_2008.pdf#page=448
            if "/Off" in states:
                field_dict["checked_value"] = states[0] if states[0] != "/Off" else states[1]
                field_dict["unchecked_value"] = "/Off"
            else:
                logger.warning(
                    "checkbox `%s` 的狀態值不符預期，勾選/取消勾選值可能不正確，請視覺驗證結果",
                    field_id,
                )
                field_dict["checked_value"] = states[0]
                field_dict["unchecked_value"] = states[1]
    elif ft == "/Ch":
        field_dict["type"] = "choice"
        states = field.get("/_States_", [])
        field_dict["choice_options"] = [{
            "value": state[0],
            "text": state[1],
        } for state in states]
    else:
        field_dict["type"] = f"unknown ({ft})"
    return field_dict


def _extract_fields(reader: PdfReader) -> tuple[dict, set]:
    """從 PdfReader 提取所有欄位定義，回傳 (欄位字典, 可能的 radio group 名稱集合)。"""
    fields = reader.get_fields()
    field_info_by_id = {}
    possible_radio_names = set()

    for field_id, field in fields.items():
        # 跳過包含子元素的容器欄位，除非它是 radio button 的父群組
        if field.get("/Kids"):
            if field.get("/FT") == "/Btn":
                possible_radio_names.add(field_id)
            continue
        field_info_by_id[field_id] = make_field_dict(field, field_id)

    return field_info_by_id, possible_radio_names


def _process_annotations(
    reader: PdfReader,
    field_info_by_id: dict,
    possible_radio_names: set,
) -> dict:
    """掃描頁面註解，為欄位補充頁碼/座標，並收集 radio button 選項。

    Radio button 的每個選項有獨立的註解，共用同一欄位名稱。
    參考: https://westhealth.github.io/exploring-fillable-forms-with-pdfrw.html
    """
    radio_fields_by_id = {}

    for page_index, page in enumerate(reader.pages):
        annotations = page.get('/Annots', [])
        for ann in annotations:
            field_id = get_full_annotation_field_id(ann)
            if field_id in field_info_by_id:
                field_info_by_id[field_id]["page"] = page_index + 1
                field_info_by_id[field_id]["rect"] = ann.get('/Rect')
            elif field_id in possible_radio_names:
                try:
                    # ann['/AP']['/N'] 應含兩個項目：'/Off' 與選中值
                    on_values = [v for v in ann["/AP"]["/N"] if v != "/Off"]
                except KeyError:
                    continue
                if len(on_values) == 1:
                    rect = ann.get("/Rect")
                    if field_id not in radio_fields_by_id:
                        radio_fields_by_id[field_id] = {
                            "field_id": field_id,
                            "type": "radio_group",
                            "page": page_index + 1,
                            "radio_options": [],
                        }
                    # 注意: macOS Preview.app 可能無法正確顯示選中的 radio button
                    radio_fields_by_id[field_id]["radio_options"].append({
                        "value": on_values[0],
                        "rect": rect,
                    })

    return radio_fields_by_id


def _filter_and_sort(field_info_by_id: dict, radio_fields_by_id: dict) -> list[dict]:
    """過濾出有位置資訊的欄位，並按頁碼/Y/X 排序。"""
    # 部分 PDF 有欄位定義但無對應註解，無法確定位置，暫時忽略
    fields_with_location = []
    for field_info in field_info_by_id.values():
        if "page" in field_info:
            fields_with_location.append(field_info)
        else:
            logger.warning("無法取得欄位 '%s' 的位置資訊，已略過", field_info.get("field_id"))

    # 按頁碼排序，同頁內按 Y 座標（PDF 座標系翻轉）再按 X 座標
    def sort_key(f):
        if "radio_options" in f:
            rect = f["radio_options"][0]["rect"] or [0, 0, 0, 0]
        else:
            rect = f.get("rect") or [0, 0, 0, 0]
        return [f.get("page"), -rect[1], rect[0]]

    sorted_fields = fields_with_location + list(radio_fields_by_id.values())
    sorted_fields.sort(key=sort_key)
    return sorted_fields


def get_field_info(reader: PdfReader) -> list[dict]:
    """取得 PDF 中所有可填寫欄位的完整資訊。

    回傳格式:
    [
      {
        "field_id": "name",
        "page": 1,
        "type": ("text", "checkbox", "radio_group", 或 "choice"),
        // 各類型的額外欄位詳見 forms.md
      },
    ]
    """
    field_info_by_id, possible_radio_names = _extract_fields(reader)
    radio_fields_by_id = _process_annotations(reader, field_info_by_id, possible_radio_names)
    return _filter_and_sort(field_info_by_id, radio_fields_by_id)


def write_field_info(pdf_path: str, json_output_path: str, force: bool = False) -> None:
    """讀取 PDF 並將欄位資訊寫入 JSON 檔案。"""
    real_pdf = validate_file_exists(pdf_path, "PDF 檔案")
    validate_output_path(json_output_path, force)

    reader = PdfReader(real_pdf)
    field_info = get_field_info(reader)
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(field_info, f, indent=2)
    logger.info("已寫入 %d 個欄位至 %s", len(field_info), json_output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="提取 PDF 可填寫表單欄位資訊並輸出 JSON",
    )
    parser.add_argument("input_pdf", help="輸入的 PDF 檔案路徑")
    parser.add_argument("output_json", help="輸出的 JSON 檔案路徑")
    add_common_args(parser)
    add_force_arg(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        write_field_info(args.input_pdf, args.output_json, args.force)
    except (FileNotFoundError, FileExistsError) as e:
        logger.error(str(e))
        sys.exit(1)
