"""一括取得・分析の共通設定。変更後は各ノートブックのカーネルを再起動する。"""
from pathlib import Path

# 初めて使う場合は、この年だけ変更してください（終了年も含みます）。
START_YEAR = 2000
END_YEAR = 2025

# 一括分析は HS 1〜24類・輸出・全相手国が対象です。
CHAPTERS = [f"{n:02d}" for n in range(1, 25)]
FLOW = "X"
PARTNER = None

if not (isinstance(START_YEAR, int) and isinstance(END_YEAR, int)
        and 1900 <= START_YEAR <= END_YEAR <= 2100):
    raise ValueError("START_YEAR / END_YEAR は1900〜2100の整数で、開始年 ≤ 終了年にしてください。")
YEARS = [str(y) for y in range(START_YEAR, END_YEAR + 1)]
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PERIOD_TAG = f"{START_YEAR}-{END_YEAR}" if START_YEAR != END_YEAR else str(START_YEAR)
BLOCK_DIR = DATA_DIR / f"ex_ch01-24_{PERIOD_TAG}_allp"

# 標準期間は既存ファイルの場所を利用。それ以外は混在を避けるため別フォルダ。
_suffix = "" if (START_YEAR, END_YEAR) == (2000, 2025) else f"_{PERIOD_TAG}"
YEAR_DIR = DATA_DIR / f"by_year_allp{_suffix}"
VARIABLE_DIR = DATA_DIR / f"variables{_suffix}"
WORLD_DIR = DATA_DIR / f"world_rows{_suffix}"
