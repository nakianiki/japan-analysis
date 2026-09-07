# japan-analysis — 日本の農水産物・食品輸出の分析

UN Comtradeのデータから、日本の輸出額と外延・内延マージン（EM・IM）を計算します。
標準設定は **2000〜2025年、HS 1〜24類の6桁品目、輸出、全報告国・全相手国**です。

## 実行するのは2本

| 順番 | ノートブック | 内容 | 主な出力（標準設定） |
|---|---|---|---|
| 1 | `01_prepare_data.ipynb` | API取得（必要な場合）→ 年別結合 | `data/by_year_allp/trade_2000.csv.gz` など |
| 2 | `02_analyze_trade.ipynb` | 3変数作成 → EM/IM計算 → 検算・保存 | `data/variables/margins.csv` など |

年別CSVがすでにあれば、2だけで分析できます。
データ本体とAPIキーはGitに含めていません。GitHubからコードを取得しただけではデータはありません。

## 環境の準備（macOS）

Python 3.11以降を想定しています。ターミナルでプロジェクトのフォルダへ移動して実行します。
別のPCでは `cd` のパスを保存先に読み替えてください。

```bash
cd /Users/nakasukadaiki/projects/comtrade
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab
```

ターミナルを開き直したら、同じフォルダで `source .venv/bin/activate` を実行します。
既存のAnaconda環境を利用する場合は、その環境に必要なライブラリをインストールできます。
ライブラリのバージョンはまだ固定していません。

ブラウザのJupyterLabでノートブックを開きます。
ノートブックはコードと説明が並んだファイルで、セルを選び **Shift + Enter** で順に実行します。
設定を確認した後は、各ノートブックを上から順に実行してください。

## 対象年の設定

`settings.py` の2行を変更します。終了年も含みます。

```python
START_YEAR = 2000
END_YEAR = 2025
```

変更後は各ノートブックで **Kernel → Restart Kernel** を選び、上から実行し直してください。
標準期間以外では年別・分析・World出力に期間の接尾辞が付き、標準期間の結果と分かれます。
この一括分析はHS 1〜24類・輸出・全相手国が対象です。

## 1. データ取得・年別結合

`01_prepare_data.ipynb` の最初の設定セルを確認します。

```python
DOWNLOAD_MISSING = False
SOURCE_DIR = BLOCK_DIR
```

- 取得済みブロックがある：`False` のまま実行します。APIキーは不要です。
- APIから取得する：`True` にして実行します。保存済みブロックはスキップします。
- ブロックの保存先が異なる：`SOURCE_DIR = Path("保存場所")` に変更します。

標準のブロック保存先は `data/ex_ch01-24_2000-2025_allp/` です。
その直下に `ch01_2000.csv.gz` などの624ファイル（24類×26年）が必要です。
ZIPの場合は先に展開してください。ZIPを置くだけでは読み込みません。

全ブロックが揃うと1類ずつ年別に結合します。全期間のデータを一度にメモリへ載せません。
年別ファイルは再実行時に再作成し、完成したファイルで置き換えます。
API利用枠で中断した場合は、枠の回復後に不足ブロックを取得し、その後で結合してください。

### APIキーを使う場合だけ行う準備

`getFinalData` を利用できるAPIキーと利用枠が必要です。
契約内容は [UN Comtrade開発者サイト](https://comtradedeveloper.un.org/) で確認してください。
以前の環境ではPremiumキーを使用しています。

ホームフォルダの `.comtrade_env` というテキストファイルに次の形式で保存します。
実際のキーをノートブックへ書き込まないでください。

```text
COMTRADE_KEY=ここを自分のキーに置き換える
```

保存後に `chmod 600 ~/.comtrade_env` を実行してください。
既存の `export COMTRADE_KEY=...` 形式も利用できます。変更後はカーネルを再起動します。

## 2. 変数作成・EM/IM分析

`02_analyze_trade.ipynb` を上から実行します。
前半Aで3変数を作成し、後半Bでその結果を引き継いでEM・IMを計算します。
途中で別のプログラムを実行する必要はありません。

| 列名 | 意味 |
|---|---|
| `japancountry` | 日本から相手国への輸出額 |
| `worldcountry` | 全報告国から相手国への輸出額 |
| `japanx` | 日本がその相手国に輸出する品目に限った、全報告国からの輸出額 |
| `EM` | `japanx / worldcountry`：扱う品目が市場に占める割合 |
| `IM` | `japancountry / japanx`：その品目群で日本が占める割合 |

金額は `primaryValue`（USD）です。大小関係と `EM × IM = japancountry / worldcountry` を検算します。

最初に見る結果は `data/variables/margins.csv`（年×相手国）です。
全期間を国ごとにまとめた値は `margins_all_years.csv`、横持ち表は `EM_wide.csv` / `IM_wide.csv` です。
**`margins_by_year.csv` のEM・IMだけは百分率（%）、その他は比率（0〜1）です。**
全期間の比率は分子と分母をそれぞれ合計してから割ります。年別比率の単純平均ではありません。
再実行すると対象の集計ファイルを上書きします。

## 補助機能と内部処理

通常の分析で利用者が開くのは上の2本だけです。

| 場所 | 役割 |
|---|---|
| `extract_world.ipynb` | 任意：取得済みブロックからWorld行を抽出 |
| `lib/` | ノートブックが呼ぶ読み込み・結合処理。直接実行は不要 |
| `docs/code_guide.md` | コードの読み方 |
| `docs/optimization.md` | 最適化の検証記録 |

テストと統合前のバックアップはローカルにのみ保持し、Git対象から除外しています。

## 困ったとき

| 状況 | 対応 |
|---|---|
| ライブラリが見つからない | 利用中の環境で `python -m pip install -r requirements.txt` を実行 |
| `settings` / `lib` が見つからない | プロジェクトのフォルダからJupyterLabを起動し、ノートブックを移動しない |
| ブロックが不足している | 設定した年・展開先・`SOURCE_DIR` を確認 |
| 年別ファイルがない | 01を完了してから02を実行 |
| APIが401 / 403を返す | キー・利用権限・利用枠をエラー本文と開発者サイトで確認 |
| メモリ不足 | 共通処理は分割読み込み。分析では全期間の日本明細と集約済み市場を保持するため、対象年を減らすことも検討 |

Worldは個別相手国と足すと二重計上になります。HSコードは先頭ゼロを保つため文字列で読みます。
分類は各国の報告時点のHS版なので、年をまたぐ比較では改訂の影響にも注意してください。

`DESIGN.md` の件数・実測値、`docs/README_previous_en.md`、`README.pdf` は以前の記録です。
現在の手順はこのREADME、対象年・保存先は `settings.py` が基準です。
