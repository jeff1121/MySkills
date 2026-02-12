"""PDF Skill 共用工具模組。

提供路徑驗證、JSON 載入、日誌設定、CLI 參數等共用函式，
供所有 PDF 處理腳本統一使用。
"""

import argparse
import json
import logging
import os
import sys
from typing import Any


# 欄位數量上限，防止 O(N²) 碰撞檢測造成效能問題
MAX_FORM_FIELDS = 500

logger = logging.getLogger("pdf-skill")


def setup_logging(verbose: bool = False) -> None:
    """設定日誌等級。verbose=True 時使用 DEBUG，否則使用 INFO。"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def validate_file_exists(path: str, label: str = "檔案") -> str:
    """驗證檔案存在且為一般檔案，回傳正規化後的絕對路徑。

    Args:
        path: 待驗證的檔案路徑。
        label: 錯誤訊息中使用的描述文字。

    Raises:
        FileNotFoundError: 檔案不存在或不是一般檔案。
    """
    real_path = os.path.realpath(path)
    if not os.path.isfile(real_path):
        raise FileNotFoundError(f"{label}不存在或不是檔案: {path}")
    return real_path


def validate_output_path(path: str, force: bool = False) -> str:
    """驗證輸出路徑。若檔案已存在且未指定 force 則拒絕覆寫。

    同時確保輸出目錄存在（自動建立）。

    Args:
        path: 輸出檔案路徑。
        force: 是否允許覆寫已存在的檔案。

    Raises:
        FileExistsError: 檔案已存在且 force=False。
    """
    real_path = os.path.realpath(path)
    if os.path.exists(real_path) and not force:
        raise FileExistsError(
            f"輸出檔案已存在: {path}（使用 --force 允許覆寫）"
        )
    # 確保輸出目錄存在
    output_dir = os.path.dirname(real_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    return real_path


def load_json(path: str, label: str = "JSON 檔案") -> Any:
    """載入 JSON 檔案並回傳解析後的資料。

    Args:
        path: JSON 檔案路徑。
        label: 錯誤訊息中使用的描述文字。

    Raises:
        FileNotFoundError: 檔案不存在。
        json.JSONDecodeError: JSON 格式錯誤。
    """
    real_path = validate_file_exists(path, label)
    with open(real_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_fields_json(data: dict) -> None:
    """驗證 fields.json 結構（非可填寫表單用）。

    檢查 pages、form_fields 陣列是否存在、欄位數量是否超過上限、
    以及每個項目是否包含必要欄位。

    Raises:
        ValueError: 結構不符合預期。
    """
    if "pages" not in data or not isinstance(data["pages"], list):
        raise ValueError("fields.json 缺少 'pages' 陣列")
    if "form_fields" not in data or not isinstance(data["form_fields"], list):
        raise ValueError("fields.json 缺少 'form_fields' 陣列")
    if len(data["form_fields"]) > MAX_FORM_FIELDS:
        raise ValueError(
            f"form_fields 數量 ({len(data['form_fields'])}) 超過上限 ({MAX_FORM_FIELDS})"
        )
    for i, page in enumerate(data["pages"]):
        for key in ("page_number", "image_width", "image_height"):
            if key not in page:
                raise ValueError(f"pages[{i}] 缺少必要欄位 '{key}'")
    for i, field in enumerate(data["form_fields"]):
        for key in ("page_number", "entry_bounding_box", "label_bounding_box"):
            if key not in field:
                raise ValueError(f"form_fields[{i}] 缺少必要欄位 '{key}'")


def validate_field_values_json(data: list) -> None:
    """驗證 field_values.json 結構（可填寫表單用）。

    Raises:
        ValueError: 結構不符合預期。
    """
    if not isinstance(data, list):
        raise ValueError("field_values.json 應為 JSON 陣列")
    for i, field in enumerate(data):
        for key in ("field_id", "page"):
            if key not in field:
                raise ValueError(f"field_values[{i}] 缺少必要欄位 '{key}'")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """加入所有腳本共用的 CLI 參數（--verbose）。"""
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="顯示詳細日誌輸出",
    )


def add_force_arg(parser: argparse.ArgumentParser) -> None:
    """加入 --force 參數，允許覆寫已存在的輸出檔案。"""
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="允許覆寫已存在的輸出檔案",
    )
