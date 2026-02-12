"""以文字註解方式填入 PDF 表單。

針對不具可填寫欄位的 PDF，讀取 fields.json 中定義的
bounding box 座標與文字內容，以 FreeText 註解加入 PDF。
詳見 forms.md。
"""

import argparse
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText

from common import (
    setup_logging, validate_file_exists, validate_output_path,
    load_json, validate_fields_json,
    add_common_args, add_force_arg, logger,
)


def transform_coordinates(
    bbox: list[float],
    image_width: float,
    image_height: float,
    pdf_width: float,
    pdf_height: float,
) -> tuple[float, float, float, float]:
    """將 bounding box 從圖片座標轉換為 PDF 座標。

    圖片座標：原點在左上角，Y 軸向下遞增。
    PDF 座標：原點在左下角，Y 軸向上遞增。
    """
    x_scale = pdf_width / image_width
    y_scale = pdf_height / image_height

    left = bbox[0] * x_scale
    right = bbox[2] * x_scale
    # 翻轉 Y 座標
    top = pdf_height - (bbox[1] * y_scale)
    bottom = pdf_height - (bbox[3] * y_scale)

    return left, bottom, right, top


def fill_pdf_form(
    input_pdf_path: str,
    fields_json_path: str,
    output_pdf_path: str,
    force: bool = False,
) -> None:
    """讀取 fields.json 並以文字註解填入 PDF。"""
    real_pdf = validate_file_exists(input_pdf_path, "PDF 檔案")
    fields_data = load_json(fields_json_path, "fields.json")
    validate_fields_json(fields_data)
    validate_output_path(output_pdf_path, force)

    reader = PdfReader(real_pdf)
    writer = PdfWriter()
    writer.append(reader)

    # 取得各頁的 PDF 尺寸
    pdf_dimensions: dict[int, tuple[float, float]] = {}
    for i, page in enumerate(reader.pages):
        mediabox = page.mediabox
        pdf_dimensions[i + 1] = (mediabox.width, mediabox.height)

    annotation_count = 0
    for field in fields_data["form_fields"]:
        page_num = field["page_number"]

        # 取得頁面尺寸並轉換座標
        page_info = next((p for p in fields_data["pages"] if p["page_number"] == page_num), None)
        if page_info is None:
            logger.warning("在 pages 中找不到第 %d 頁的資訊，跳過此欄位", page_num)
            continue
        image_width = page_info["image_width"]
        image_height = page_info["image_height"]
        pdf_width, pdf_height = pdf_dimensions[page_num]

        transformed_entry_box = transform_coordinates(
            field["entry_bounding_box"],
            image_width, image_height,
            pdf_width, pdf_height,
        )

        # 跳過空白欄位
        if "entry_text" not in field or "text" not in field["entry_text"]:
            continue
        entry_text = field["entry_text"]
        text = entry_text["text"]
        if not text:
            continue

        font_name = entry_text.get("font", "Arial")
        font_size = str(entry_text.get("font_size", 14)) + "pt"
        font_color = entry_text.get("font_color", "000000")

        # 注意: font size/color 在不同閱讀器的顯示可能不一致
        # 參考: https://github.com/py-pdf/pypdf/issues/2084
        annotation = FreeText(
            text=text,
            rect=transformed_entry_box,
            font=font_name,
            font_size=font_size,
            font_color=font_color,
            border_color=None,
            background_color=None,
        )
        # pypdf 的 page_number 為 0-based
        writer.add_annotation(page_number=page_num - 1, annotation=annotation)
        annotation_count += 1

    with open(output_pdf_path, "wb") as output:
        writer.write(output)

    logger.info("已填入表單並儲存至 %s", output_pdf_path)
    logger.info("共新增 %d 個文字註解", annotation_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="以文字註解方式填入 PDF 表單（非可填寫欄位用）",
    )
    parser.add_argument("input_pdf", help="輸入的 PDF 檔案路徑")
    parser.add_argument("fields_json", help="fields.json 檔案路徑")
    parser.add_argument("output_pdf", help="輸出的 PDF 檔案路徑")
    add_common_args(parser)
    add_force_arg(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        fill_pdf_form(args.input_pdf, args.fields_json, args.output_pdf, args.force)
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)