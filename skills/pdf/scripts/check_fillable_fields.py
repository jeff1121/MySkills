"""檢查 PDF 是否含有可填寫的表單欄位。詳見 forms.md。"""

import argparse
import sys

from pypdf import PdfReader

from common import setup_logging, validate_file_exists, add_common_args, logger


def check_fillable(pdf_path: str) -> bool:
    """檢查 PDF 是否包含可填寫欄位，回傳 True/False。"""
    real_path = validate_file_exists(pdf_path, "PDF 檔案")
    reader = PdfReader(real_path)
    return bool(reader.get_fields())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="檢查 PDF 是否含有可填寫的表單欄位",
    )
    parser.add_argument("pdf_file", help="待檢查的 PDF 檔案路徑")
    add_common_args(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        if check_fillable(args.pdf_file):
            print("This PDF has fillable form fields")
        else:
            print("This PDF does not have fillable form fields; you will need to visually determine where to enter data")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
