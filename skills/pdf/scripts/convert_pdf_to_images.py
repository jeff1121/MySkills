"""將 PDF 的每一頁轉換為 PNG 圖片。"""

import argparse
import os
import sys

from pdf2image import convert_from_path

from common import setup_logging, validate_file_exists, add_common_args, logger


def convert(pdf_path: str, output_dir: str, max_dim: int = 1000) -> None:
    """將 PDF 各頁轉為 PNG，自動縮放至 max_dim 以內。"""
    real_path = validate_file_exists(pdf_path, "PDF 檔案")
    # 確保輸出目錄存在，不存在則自動建立
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(real_path, dpi=200)

    for i, image in enumerate(images):
        # 若寬或高超過 max_dim 則等比縮放
        width, height = image.size
        if width > max_dim or height > max_dim:
            scale_factor = min(max_dim / width, max_dim / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height))

        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path)
        logger.info("已儲存第 %d 頁: %s (尺寸: %s)", i + 1, image_path, image.size)

    logger.info("共轉換 %d 頁為 PNG 圖片", len(images))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="將 PDF 每頁轉換為 PNG 圖片",
    )
    parser.add_argument("input_pdf", help="輸入的 PDF 檔案路徑")
    parser.add_argument("output_dir", help="輸出 PNG 圖片的目錄")
    parser.add_argument("--max-dim", type=int, default=1000,
                        help="圖片最大寬/高像素（預設: 1000）")
    add_common_args(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        convert(args.input_pdf, args.output_dir, args.max_dim)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
