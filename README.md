# japan-analysis — 日本の農水産物・食品輸出の分析

UN Comtradeのデータから、日本の輸出額と外延・内延マージン（EM・IM）を計算します。
標準設定は **2000〜2025年、HS 1〜24類の6桁品目、輸出、全報告国・全相手国**です。

## 実行するのは2本

| 順番 | ノートブック | 内容 | 主な出力（標準設定） |
|---|---|---|---|
| 1 | `01_prepare_data.ipynb` | API取得（必要な場合）→ 年別結合 | `data/by_year_allp/trade_2000.csv.gz` など |
| 2 | `02_analyze_trade.ipynb` | 3変数作成 → EM/IM計算 → 検算・保存 | `data/variables/margins.csv` など |

補足：次のノートブックは必要な場合だけ使用します。

| ノートブック | 内容 |
|---|---|
| `extract_world.ipynb` | 任意：取得済みブロックからWorld行を抽出 |

年別CSVがすでにあれば、2だけで分析できます。
データ本体とAPIキーはGitに含めていません。GitHubからコードを取得しただけではデータはありません。

## 環境の準備（macOS / Windows）

Python 3.11以降を想定しています。OSに合った手順で、プロジェクトのフォルダから実行します。
`cd` のパスは自分の保存先に読み替えてください。Windows実機での動作確認は未実施です。

### macOS（ターミナル）

```bash
cd /Users/nakasukadaiki/projects/comtrade
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab
```

ターミナルを開き直したら、同じフォルダで `source .venv/bin/activate` を実行します。
### Windows（PowerShell）

Python 3.11以降をインストールし、PowerShellを開きます。
次の例では `C:\Users\YourName\projects\comtrade` にコードがあるものとします。

```powershell
cd "C:\Users\YourName\projects\comtrade"
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab
```

`py` が見つからない場合は、`python --version` で3.11以降と確認できれば、
最初の2つの `py -3` を `python` に置き換えられます。

仮想環境内のPythonを直接指定しているため、`Activate.ps1` の実行や実行ポリシーの変更は不要です。
この使い方は [Python公式のvenv説明](https://docs.python.org/3/library/venv.html#how-venvs-work) に沿っています。
次回からは同じフォルダで次を実行するだけで起動できます。

```powershell
.\.venv\Scripts\python.exe -m jupyterlab
```

macOSの `.venv` はWindowsへコピーせず、Windows側で作成してください。

### 共通：ノートブックを開く

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

Windowsで入力フォルダを指定する場合、ノートブック内では `/` を使うと書きやすくなります。

```python
SOURCE_DIR = Path("C:/Users/YourName/projects/comtrade/data/blocks")
```

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

空の設定テンプレート [.comtrade_env.example](.comtrade_env.example) を用意しています。
このファイルをホームフォルダへコピーし、名前を `.comtrade_env` に変更して、
`COMTRADE_KEY=` の右側に自分のキーを入力してください。
すでに `.comtrade_env` がある場合は、そのファイルを使い、空のテンプレートで上書きしないでください。

GitHub上のテンプレートは空のままにし、実際のキーはコピー先にだけ保存します。
実際のキーをノートブックへ書き込まないでください。

```text
COMTRADE_KEY=ここを自分のキーに置き換える
```

**macOS**：保存先は `~/.comtrade_env` です。保存後に `chmod 600 ~/.comtrade_env` を実行します。

**Windows**：保存先はユーザーフォルダの `.comtrade_env`（通常は `C:\Users\YourName\.comtrade_env`）です。
PowerShellで次を実行すると、Pythonが参照する保存先を確認できます。

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; print(Path.home() / '.comtrade_env')"
```

メモ帳で「名前を付けて保存」を選び、ファイルの種類を「すべてのファイル」、
文字コードを「UTF-8」（BOMなし）にして保存してください。
ファイル名が `.comtrade_env.txt` にならないようにします。Windowsでは `chmod` は使いません。
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

## 困ったとき

| 状況 | 対応 |
|---|---|
| ライブラリが見つからない | macOSは `python -m pip install -r requirements.txt`、Windowsは `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` を実行 |
| `settings` / `lib` が見つからない | プロジェクトのフォルダからJupyterLabを起動し、ノートブックを移動しない |
| ブロックが不足している | 設定した年・展開先・`SOURCE_DIR` を確認 |
| 年別ファイルがない | 01を完了してから02を実行 |
| APIが401 / 403を返す | キー・利用権限・利用枠をエラー本文と開発者サイトで確認 |
| メモリ不足 | 共通処理は分割読み込み。分析では全期間の日本明細と集約済み市場を保持するため、対象年を減らすことも検討 |

Worldは個別相手国と足すと二重計上になります。HSコードは先頭ゼロを保つため文字列で読みます。
分類は各国の報告時点のHS版なので、年をまたぐ比較では改訂の影響にも注意してください。
