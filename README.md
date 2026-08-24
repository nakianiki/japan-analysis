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

### 1. 必要な環境

| | |
|---|---|
| Python | 3.9 以上（動作確認は 3.11 / Anaconda） |
| ライブラリ | `comtradeapicall` `pandas` `python-dotenv` `jupyterlab` |
| API キー | UN Comtrade の Premium サブスクリプションキー（32文字） |

```bash
pip install comtradeapicall pandas python-dotenv jupyterlab
```

インストール済みか確認する。

```bash
python -c "import comtradeapicall, pandas, dotenv; print('OK')"
```

### 2. API キーの取得

**無料枠では動かない。** 無料の preview 系 API は1リクエスト500レコード・1期間のみという制限があり、
このリポジトリが使う `getFinalData` は 401 を返す。Premium の契約が必要。

1. https://comtradedeveloper.un.org/ でアカウントを登録（メール認証あり）
2. **Products** タブから Premium 系のプランを **Subscribe**
3. **Profile** ページに Primary key / Secondary key が表示される

Primary と Secondary は機能が同じで、ローテーション用に2本発行される。どちらを使ってもよい。

所属機関が UN Comtrade の機関契約を持っている場合は、そちら経由で無償で使えることがある。
図書館や指導教員に確認する価値がある。

> **クォータがある。** Premium でも時間あたりの呼び出し回数に上限があり、
> 使い切ると 403 が返って復活まで十数時間かかる。全期間の取得は数回に分ける前提で進めること
> （中断・再開に対応している）。

### 3. キーの登録

**キーはノートブックに直接書かない。** `.ipynb` は実行結果ごと保存されるため、
共有したりリポジトリに入れた瞬間に漏れる。ホームディレクトリの外部ファイルに置く。

ターミナルで次を実行する（コマンドをそのまま貼り付けて Enter。**キーはこのコマンドには含めない**）。

```bash
read -rs "key?Primary key を貼り付けて Enter: " \
  && printf 'export COMTRADE_KEY=%s\n' "$key" > ~/.comtrade_env \
  && chmod 600 ~/.comtrade_env && unset key && echo "保存しました"
```

実行するとプロンプトが出るので、そこでキーを貼り付けて Enter を押す。
**入力しても画面には何も表示されないが、それが正常。**

`read -rs` を使う理由は3つ。

- `-s` で入力が画面に表示されない
- 引数ではなく標準入力から受け取るため、`~/.zsh_history` に平文で残らない
- `unset` でシェル変数からも消える

### 4. 確認

```bash
source ~/.comtrade_env && echo "長さ: ${#COMTRADE_KEY} 文字"
```

`長さ: 32 文字` と出れば成功。`0 文字` なら貼り付けが効いていないのでやり直す。

ノートブックは `python-dotenv` でこのファイルを読む（`export ` 接頭辞は自動で解釈される）。

```python
load_dotenv(Path.home() / ".comtrade_env")
KEY = (os.environ.get("COMTRADE_KEY") or "").strip()
```

**JupyterLab を起動したままキーを登録した場合は、カーネルを再起動する**
（Kernel → Restart Kernel）。起動中のカーネルは古い環境を持っているため読み込まれない。

### 5. リポジトリ管理下に置く場合

`~/.comtrade_env` と `data/` が `.gitignore` に入っていることを確認する。
このリポジトリの `.gitignore` には既に含めてあるが、**ホームディレクトリ自体が
git リポジトリになっている環境では別途対応が必要**。

```bash
grep -qxF '.comtrade_env' ~/.gitignore || echo '.comtrade_env' >> ~/.gitignore
```

### セットアップでよくつまずく点

| 症状 | 対処 |
|---|---|
| `COMTRADE_KEY が未設定` | `source ~/.comtrade_env` を実行、またはカーネル再起動 |
| `401 invalid subscription key` | 無料枠のキーを使っている。Premium が必要 |
| `403 Out of call volume quota` | クォータ切れ。十数時間待って再実行すれば続きから走る |
| `長さ: 0 文字` | キーの貼り付けが効いていない。手順3をやり直す |
| 学内プロキシ環境 | 各 API 関数に `proxy_url=` 引数を渡す |

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
