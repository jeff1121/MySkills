"""填入 PDF 可填寫表單欄位的值。

讀取 field_values.json 中定義的欄位 ID 與值，驗證後寫入 PDF。
詳見 forms.md。
"""

import argparse
import json
import sys

from pypdf import PdfReader, PdfWriter

from extract_form_field_info import get_field_info
from common import (
    setup_logging, validate_file_exists, validate_output_path,
    load_json, validate_field_values_json,
    add_common_args, add_force_arg, logger,
)


def fill_pdf_fields(input_pdf_path: str, fields_json_path: str, output_pdf_path: str, force: bool = False) -> None:
    """驗證欄位值後填入 PDF。"""
    real_pdf = validate_file_exists(input_pdf_path, "PDF 檔案")
    fields = load_json(fields_json_path, "field_values.json")
    validate_field_values_json(fields)
    validate_output_path(output_pdf_path, force)

    # 依頁碼分組
    fields_by_page: dict[int, dict] = {}
    for field in fields:
        if "value" in field:
            field_id = field["field_id"]
            page = field["page"]
            if page not in fields_by_page:
                fields_by_page[page] = {}
            fields_by_page[page][field_id] = field["value"]

    reader = PdfReader(real_pdf)

    # 驗證欄位 ID、頁碼、值
    has_error = False
    field_info = get_field_info(reader)
    fields_by_ids = {f["field_id"]: f for f in field_info}
    for field in fields:
        existing_field = fields_by_ids.get(field["field_id"])
        if not existing_field:
            has_error = True
            logger.error("'%s' 不是有效的欄位 ID", field["field_id"])
        elif field["page"] != existing_field["page"]:
            has_error = True
            logger.error(
                "'%s' 的頁碼不正確（輸入: %s, 預期: %s）",
                field["field_id"], field["page"], existing_field["page"],
            )
        else:
            if "value" in field:
                err = validation_error_for_field_value(existing_field, field["value"])
                if err:
                    logger.error(err)
                    has_error = True
    if has_error:
        sys.exit(1)

    writer = PdfWriter(clone_from=reader)
    for page, field_values in fields_by_page.items():
        writer.update_page_form_field_values(writer.pages[page - 1], field_values, auto_regenerate=False)

    # 許多 PDF 閱讀器需要此設定才能正確渲染表單值
    # 可能導致閱讀器顯示「儲存變更」對話框
    writer.set_need_appearances_writer(True)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)
    logger.info("已填入表單並儲存至 %s", output_pdf_path)


def validation_error_for_field_value(field_info: dict, field_value: str) -> str | None:
    """驗證欄位值是否符合該欄位類型的允許值。不合法時回傳錯誤訊息。"""
    field_type = field_info["type"]
    field_id = field_info["field_id"]
    if field_type == "checkbox":
        checked_val = field_info["checked_value"]
        unchecked_val = field_info["unchecked_value"]
        if field_value != checked_val and field_value != unchecked_val:
            return f'checkbox 欄位 "{field_id}" 的值 "{field_value}" 無效。勾選值: "{checked_val}"，取消勾選值: "{unchecked_val}"'
    elif field_type == "radio_group":
        option_values = [opt["value"] for opt in field_info["radio_options"]]
        if field_value not in option_values:
            return f'radio group 欄位 "{field_id}" 的值 "{field_value}" 無效。有效值: {option_values}'
    elif field_type == "choice":
        choice_values = [opt["value"] for opt in field_info["choice_options"]]
        if field_value not in choice_values:
            return f'choice 欄位 "{field_id}" 的值 "{field_value}" 無效。有效值: {choice_values}'
    return None


def _monkeypatch_pypdf_selection_list():
    """修補 pypdf（至少 5.7.0 版）處理選擇清單時的 bug。

    問題: pypdf _writer.py 中 get_inherited(FA.Opt) 回傳二元素列表的列表，
    導致 str.join() 拋出 TypeError。
    此修補在 get_inherited 回傳值為 [[value, text], ...] 格式時，
    將其轉為 [value, ...] 格式。

    TODO: 追蹤上游修復進度，升級後移除此 workaround。
    """
    from pypdf.generic import DictionaryObject
    from pypdf.constants import FieldDictionaryAttributes

    original_get_inherited = DictionaryObject.get_inherited

    def patched_get_inherited(self, key: str, default=None):
        result = original_get_inherited(self, key, default)
        if key == FieldDictionaryAttributes.Opt:
            if isinstance(result, list) and all(isinstance(v, list) and len(v) == 2 for v in result):
                result = [r[0] for r in result]
        return result

    DictionaryObject.get_inherited = patched_get_inherited


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="填入 PDF 可填寫表單欄位的值",
    )
    parser.add_argument("input_pdf", help="輸入的 PDF 檔案路徑")
    parser.add_argument("field_values_json", help="field_values.json 檔案路徑")
    parser.add_argument("output_pdf", help="輸出的 PDF 檔案路徑")
    add_common_args(parser)
    add_force_arg(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    _monkeypatch_pypdf_selection_list()

    try:
        fill_pdf_fields(args.input_pdf, args.field_values_json, args.output_pdf, args.force)
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)
