# japan-analysis

UN Comtrade から農水産物・食品（HS 1〜24類）の貿易統計を取得し、日本の輸出に関する分析用変数を作る。

| | |
|---|---|
| 対象 | HS 1〜24類の6桁コード 1,176件 / 2012〜2025年 / 輸出 / 全報告国 × 全相手国 |
| 規模 | 12,873,073 行 |

## 構成

| ファイル | 役割 |
|---|---|
| `fetch_ch01-24.ipynb` | データ取得。API から取得し、年ごとファイルまで作る |
| `build_variables.ipynb` | 変数構築。取得データから分析用の変数を作る |
| `comtrade_start.ipynb` | 単発の確認用。品目1つを指定して中身を見る |
| `DESIGN.md` | 設計判断の理由と検証の詳細 |

取得データは容量が大きいためリポジトリに含めない。ノートブックを実行すれば再生成できる。

## セットアップ

```bash
pip install comtradeapicall pandas python-dotenv jupyterlab
```

UN Comtrade の **Premium サブスクリプションキー**が必要（無料枠では動かない)。
https://comtradedeveloper.un.org/ で登録し、Profile に表示されるキーを取得する。

キーはノートブックに書かず、外部ファイルに置く。

```bash
read -rs "key?Primary key を貼り付けて Enter: " \
  && printf 'export COMTRADE_KEY=%s\n' "$key" > ~/.comtrade_env \
  && chmod 600 ~/.comtrade_env && unset key
```

## 使い方

### 1. データ取得

`fetch_ch01-24.ipynb` を開き、設定セル（セクション2）を確認して上から順に実行する。

```python
YEARS    = [str(y) for y in range(2012, 2026)]
FLOW     = "X"                                     # 輸出
CHAPTERS = [f"{i:02d}" for i in range(1, 25)]      # 1〜24類
PARTNER  = None                                    # 全相手国
```

**中断しても、同じセルを再実行すれば続きから走る。** API のクォータ切れでも進捗を表示して止まるだけなので、
復活後に再実行すればよい。

出力：

```
data/ex_ch01-24_2012-2025_allp/ch{類}_{年}.csv.gz   336ブロック
data/by_year_allp/trade_{年}.csv.gz                 年ごと14ファイル（セクション7）
```

### 2. 変数構築

`build_variables.ipynb` を上から順に実行する。

| 変数名 | 定義 |
|---|---|
| `japancountry` | 日本から輸入国 *m* への輸出額の合計 |
| `worldcountry` | 世界各国から *m* への総輸出額（*m* の輸入市場規模） |
| `japanx` | 日本が *m* へ輸出している品目に限定した、世界各国から *m* への輸出額 |

いずれも年 × 相手国。定義上 `japancountry ≤ japanx ≤ worldcountry` が成り立ち、ノートブックが検査する。

出力は `data/variables/` に3形式（年ごと / 横持ち / 縦持ち）。

## 注意点

- **読み込みには `dtype` 指定が必須。** 省くと `0201` が `201` になり品目コードが壊れる。

  ```python
  pd.read_csv(path, dtype={"cmdCode": str, "classificationCode": str})
  ```

- **輸出額は `fobvalue` または `primaryValue` を使う。** `cifvalue` は輸出データではほぼ空。
- **直近年は報告が出揃っていない。** 報告国数は2023年165 → 2024年138 → 2025年93。時系列比較では過小評価になる。
- **`partnerDesc == "World"` は全世界合計。** 個別相手国と足すと二重計上になる。

詳細は [`DESIGN.md`](DESIGN.md) を参照。
