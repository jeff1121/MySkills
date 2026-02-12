"""建立驗證圖片，在圖片上標示 bounding box 位置。

以紅色矩形標示文字輸入區域，藍色矩形標示標籤位置，
用於視覺確認 fields.json 中定義的座標精準度。詳見 forms.md。
"""

import argparse
import sys

from PIL import Image, ImageDraw

from common import (
    setup_logging, validate_file_exists, validate_output_path,
    load_json, validate_fields_json, add_common_args, add_force_arg, logger,
)


def create_validation_image(
    page_number: int,
    fields_json_path: str,
    input_path: str,
    output_path: str,
    force: bool = False,
) -> None:
    """在指定頁面的圖片上繪製 bounding box 矩形。"""
    data = load_json(fields_json_path, "fields.json")
    validate_fields_json(data)
    validate_file_exists(input_path, "輸入圖片")
    validate_output_path(output_path, force)

    img = Image.open(input_path)
    draw = ImageDraw.Draw(img)
    num_boxes = 0

    for field in data["form_fields"]:
        if field["page_number"] == page_number:
            entry_box = field["entry_bounding_box"]
            label_box = field["label_bounding_box"]
            # 紅色矩形：文字輸入區域；藍色矩形：標籤區域
            draw.rectangle(entry_box, outline="red", width=2)
            draw.rectangle(label_box, outline="blue", width=2)
            num_boxes += 2

    img.save(output_path)
    logger.info(
        "已建立驗證圖片: %s（共 %d 個 bounding box）", output_path, num_boxes
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="建立 bounding box 驗證圖片",
    )
    parser.add_argument("page_number", type=int, help="頁碼（1-based）")
    parser.add_argument("fields_json", help="fields.json 檔案路徑")
    parser.add_argument("input_image", help="輸入圖片路徑")
    parser.add_argument("output_image", help="輸出驗證圖片路徑")
    add_common_args(parser)
    add_force_arg(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        create_validation_image(
            args.page_number, args.fields_json,
            args.input_image, args.output_image, args.force,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)
