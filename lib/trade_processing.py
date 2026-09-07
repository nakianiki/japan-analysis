"""年別CSVを読み、分析に必要な明細・市場規模・品目数を作る。

CSV全体を一度に保持せず、10万行ずつ処理する。
「報告国」は輸出元、「相手国」は輸出先、「品目」はHSコードを指す。
"""
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

# チャンク = 一度に読み込む行のまとまり。分析期間の設定とは別です。
CHUNK_SIZE = 100_000
TRADE_COLUMNS = [
    "refYear", "reporterCode", "reporterDesc", "flowDesc",
    "partnerCode", "partnerDesc", "cmdCode", "primaryValue",
]
TEXT_COLUMNS = {
    "cmdCode": str,       # HSコードの先頭ゼロを保つ
    "reporterDesc": str,
    "partnerDesc": str,
    "flowDesc": str,
}
MARKET_KEYS = ["refYear", "partnerCode", "partnerDesc", "cmdCode"]
PARTNER_COMMODITY_KEYS = ["partnerCode", "cmdCode"]


def _read_chunks(path, columns, chunksize):
    """必要な列だけを、共通の型指定で分割して返す。"""
    with pd.read_csv(
        path, dtype=TEXT_COLUMNS, usecols=columns, chunksize=chunksize
    ) as reader:
        yield from reader


def _sum_market_values(rows):
    """年×相手国×品目ごとに輸出額を合計する。"""
    # 欠損のあるグループもここでは残し、後続の集計で従来どおり扱う。
    return rows.groupby(
        MARKET_KEYS, as_index=False, dropna=False
    )["primaryValue"].sum()


def read_reporter(
    files: Mapping[str, Path], reporter_code: int, chunksize: int = CHUNK_SIZE
) -> pd.DataFrame:
    """年→CSVパスの辞書から、指定報告国の明細を返す。World行も含む。"""
    reporter_rows = []
    for path in files.values():
        for chunk in _read_chunks(path, TRADE_COLUMNS, chunksize):
            is_reporter = chunk["reporterCode"] == reporter_code
            reporter_rows.append(chunk.loc[is_reporter].copy())
    return pd.concat(reporter_rows, ignore_index=True)


def summarize_trade(
    files: Mapping[str, Path],
    reporter_code: int = 392,
    exclude_reporter: int | None = None,
    chunksize: int = CHUNK_SIZE,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """CSVを1回ずつ読み、指定報告国の明細と年別市場集計を返す。

    files: 年（文字列）をキー、年別CSVパスを値とする辞書。
    戻り値の1つ目: 指定報告国の明細。World行も保持する。
    戻り値の2つ目: 年をキーとする市場集計。各表は年×相手国×品目の輸出額。
    exclude_reporter: 市場集計から除外する報告国。明細の抽出には影響しない。
    """
    reporter_rows = []
    markets_by_year = {}

    for year, path in files.items():
        year_market = None
        for chunk in _read_chunks(path, TRADE_COLUMNS, chunksize):
            # 1. 分析対象の報告国だけは、後で品目集合を作れるよう明細を残す。
            is_reporter = chunk["reporterCode"] == reporter_code
            reporter_rows.append(chunk.loc[is_reporter].copy())

            # 2. Worldと個別相手国の二重計上を避けて、市場規模を集計する。
            market_rows = chunk.loc[chunk["partnerDesc"] != "World"]
            if exclude_reporter is not None:
                market_rows = market_rows.loc[
                    market_rows["reporterCode"] != exclude_reporter
                ]
            chunk_market = _sum_market_values(market_rows)

            # 3. チャンク境界に同じ品目が現れるので、前回までの合計と足し直す。
            if year_market is None:
                year_market = chunk_market
            else:
                combined_market = pd.concat(
                    [year_market, chunk_market], ignore_index=True
                )
                year_market = _sum_market_values(combined_market)

        markets_by_year[year] = year_market

    reporter_details = pd.concat(reporter_rows, ignore_index=True)
    return reporter_details, markets_by_year


def pooled_commodity_counts(
    paths: Iterable[Path], reporter_code: int = 392, chunksize: int = CHUNK_SIZE
) -> pd.DataFrame:
    """全期間で一度でも輸出した品目数を相手国別に返す。

    出力列は partnerCode と n_cmd_pooled。年別品目数の合計ではなく、
    相手国×品目の重複を除いて数える。
    """
    unique_pairs = set()
    columns = ["reporterCode", "partnerCode", "partnerDesc", "cmdCode"]

    for path in paths:
        for chunk in _read_chunks(path, columns, chunksize):
            is_reporter = chunk["reporterCode"] == reporter_code
            is_individual_partner = chunk["partnerDesc"] != "World"
            partner_commodities = chunk.loc[
                is_reporter & is_individual_partner, PARTNER_COMMODITY_KEYS
            ]
            unique_pairs.update(
                partner_commodities.drop_duplicates().itertuples(index=False, name=None)
            )

    # 欠損値を含む組も、pandas側で従来と同じ重複判定を行う。
    pairs_table = pd.DataFrame(list(unique_pairs), columns=PARTNER_COMMODITY_KEYS)
    counts = pairs_table.drop_duplicates().groupby("partnerCode", as_index=False).size()
    return counts.rename(columns={"size": "n_cmd_pooled"})
