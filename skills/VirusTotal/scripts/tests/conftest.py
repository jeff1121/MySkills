"""pytest 共用設定：將 scripts/ 目錄加入 sys.path，讓測試可用扁平匯入（from models import ...）。"""

from __future__ import annotations

import sys
from pathlib import Path

# 將 scripts/（本檔的上層目錄）插入 sys.path，對應 skill 執行時的扁平匯入慣例。
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
