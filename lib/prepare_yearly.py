"""取得済みブロックを年別CSVに結合する。APIキー・ネット接続は不要。"""
import gzip
import os
from pathlib import Path
import tempfile

import pandas as pd

from settings import BLOCK_DIR, CHAPTERS, YEAR_DIR, YEARS


def prepare_yearly(source=BLOCK_DIR, destination=YEAR_DIR, years=YEARS, chapters=CHAPTERS):
    """全ブロックを確認してから、年別CSVを再作成する。

    source: ch{類}_{年}.csv.gz が直接入っているフォルダ。
    destination: trade_{年}.csv.gz を保存するフォルダ。
    years / chapters: 処理する年と2桁の類コード。標準値は settings.py から読む。
    """
    source = Path(source)
    destination = Path(destination)
    chapters = sorted(set(chapters))
    if not chapters or any(len(ch) != 2 or not ch.isdigit() for ch in chapters):
        raise ValueError("chapters は2桁の類コードを1つ以上指定してください。")
    # 全入力を先に確認し、不足があれば出力する前に止める。
    missing = []
    for year in years:
        for chapter in chapters:
            block_path = source / f"ch{chapter}_{year}.csv.gz"
            if not block_path.is_file():
                missing.append(block_path)
    if missing:
        raise FileNotFoundError(
            f"取得済みブロックが {len(missing)} 個不足しています。例: {missing[0]}\n"
            "ZIPは展開し、ch01_2000.csv.gz などが直接入ったフォルダを\n"
            "01_prepare_data.ipynb の SOURCE_DIR で指定してください。未取得なら DOWNLOAD_MISSING = True にしてください。")
    destination.mkdir(parents=True, exist_ok=True)
    for year in years:
        row_count = _write_year(source, destination, year, chapters)
        output_path = destination / f"trade_{year}.csv.gz"
        print(f"{year}: {row_count:,} 行 → {output_path}")


def _write_year(source, destination, year, chapters):
    """1年分を1類ずつ書き、完成後に出力を置き換える。保存行数を返す。"""
    output = destination / f"trade_{year}.csv.gz"
    # 再実行時も元ブロックから再作成。書き込み完了後に既存ファイルを置き換える。
    fd, temporary = tempfile.mkstemp(dir=destination, suffix=".csv.gz")
    os.close(fd)
    try:
        count = 0
        columns = None
        with gzip.open(temporary, "wt", encoding="utf-8-sig", newline="") as stream:
            for chapter in chapters:
                table = pd.read_csv(source / f"ch{chapter}_{year}.csv.gz",
                                    dtype={"cmdCode": str, "classificationCode": str})
                if not table["cmdCode"].str.startswith(chapter).fillna(False).all():
                    raise ValueError(f"{year}年 第{chapter}類のファイルに別の類または欠損コードがあります。")
                if columns is not None and list(table.columns) != columns:
                    raise ValueError(f"{year}年 第{chapter}類の列構成が他のブロックと異なります。")
                table = table.sort_values(["cmdCode", "reporterCode", "partnerCode"], kind="stable")
                # 類の昇順に書けば、全年をソートした場合と同じ順序になる。
                table.to_csv(stream, index=False, header=columns is None)
                columns = list(table.columns)
                count += len(table)
                del table
        os.replace(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return count
