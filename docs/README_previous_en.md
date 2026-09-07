# japan-analysis

Retrieves agri-food trade statistics (HS chapters 1–24) from UN Comtrade and builds
analytical variables on Japan's exports.

| | |
|---|---|
| Scope | 1,176 six-digit HS codes in chapters 1–24 / 2012–2025 / exports / all reporters × all partners |
| Size | 12,873,073 rows |

## Contents

| File | Purpose |
|---|---|
| `fetch_ch01-24.ipynb` | Data retrieval. Downloads from the API and produces per-year files |
| `build_variables.ipynb` | Variable construction. Builds analytical variables from the retrieved data |
| `comtrade_start.ipynb` | Ad-hoc inspection. Query a single commodity and look at the raw rows |
| `DESIGN.md` | Design rationale and verification details |

The retrieved data is large and is **not** committed to this repository. Run the notebooks
to regenerate it.

## Setup

### 1. Requirements

| | |
|---|---|
| Python | 3.9 or later (tested on 3.11 / Anaconda) |
| Libraries | `comtradeapicall` `pandas` `python-dotenv` `jupyterlab` |
| API key | A UN Comtrade **Premium** subscription key (32 characters) |

```bash
pip install comtradeapicall pandas python-dotenv jupyterlab
```

Verify the installation:

```bash
python -c "import comtradeapicall, pandas, dotenv; print('OK')"
```

### 2. Obtaining an API key

**The free tier will not work.** The free preview endpoints are capped at 500 records and a
single period per request, and `getFinalData` — which this repository relies on — returns 401.
A Premium subscription is required.

1. Register an account at https://comtradedeveloper.un.org/ (email verification required)
2. Under the **Products** tab, subscribe to a Premium plan
3. Your Primary key and Secondary key appear on the **Profile** page

The two keys are functionally identical; they exist so you can rotate them. Either one works.

If your institution holds a UN Comtrade institutional subscription, you may be able to use it
at no cost — worth asking your library or advisor before paying.

> **There is a call quota.** Even on Premium, the number of calls per time window is limited.
> Once exhausted, the API returns 403 and the quota takes on the order of a dozen hours to
> replenish. Plan on retrieving the full period across several sessions; the notebook supports
> stopping and resuming.

### 3. Registering the key

**Do not put the key in a notebook.** A `.ipynb` file is saved together with its cell outputs,
so the key leaks the moment you share the file or commit it. Keep it in a separate file in your
home directory.

Run the following in a terminal. Paste the command as-is — **the key itself is not part of the
command**:

```bash
read -rs "key?Paste your Primary key and press Enter: " \
  && printf 'export COMTRADE_KEY=%s\n' "$key" > ~/.comtrade_env \
  && chmod 600 ~/.comtrade_env && unset key && echo "saved"
```

A prompt appears; paste the key there and press Enter. **Nothing is echoed to the screen while
you type — that is expected.**

Three reasons for `read -rs`:

- `-s` keeps the input from being displayed
- the value arrives on stdin rather than as an argument, so it is not written to `~/.zsh_history`
- `unset` clears it from the shell variable afterwards

### 4. Verifying

```bash
source ~/.comtrade_env && echo "length: ${#COMTRADE_KEY} characters"
```

`length: 32 characters` means it worked. `0 characters` means the paste did not take effect —
repeat step 3.

The notebooks read this file via `python-dotenv` (the `export ` prefix is handled automatically):

```python
load_dotenv(Path.home() / ".comtrade_env")
KEY = (os.environ.get("COMTRADE_KEY") or "").strip()
```

**If JupyterLab was already running when you registered the key, restart the kernel**
(Kernel → Restart Kernel). A running kernel holds the old environment and will not see the
new variable.

### 5. If you keep this under version control

Make sure `~/.comtrade_env` and `data/` are ignored. This repository's `.gitignore` already
covers them, but **if your home directory is itself a git repository, you need to handle that
separately**:

```bash
grep -qxF '.comtrade_env' ~/.gitignore || echo '.comtrade_env' >> ~/.gitignore
```

### Common setup problems

| Symptom | What to do |
|---|---|
| `COMTRADE_KEY is not set` | Run `source ~/.comtrade_env`, or restart the kernel |
| `401 invalid subscription key` | You are using a free-tier key. Premium is required |
| `403 Out of call volume quota` | Quota exhausted. Wait for it to replenish, then re-run — it resumes where it stopped |
| `length: 0 characters` | The key was not pasted. Repeat step 3 |
| Behind an institutional proxy | Pass `proxy_url=` to the API functions |

## Usage

### 1. Retrieve the data

Open `fetch_ch01-24.ipynb`, check the configuration cell (section 2), and run the cells in order.

```python
YEARS    = [str(y) for y in range(2012, 2026)]
FLOW     = "X"                                     # exports
CHAPTERS = [f"{i:02d}" for i in range(1, 25)]      # chapters 1–24
PARTNER  = None                                    # all partners
```

**If it stops partway, just re-run the same cell — it continues from where it left off.**
Running out of API quota is not an error either: the notebook prints the progress and halts,
so you re-run it once the quota is back.

Output:

```
data/ex_ch01-24_2012-2025_allp/ch{chapter}_{year}.csv.gz   336 blocks
data/by_year_allp/trade_{year}.csv.gz                      14 per-year files (section 7)
```

### 2. Build the variables

Run `build_variables.ipynb` from the top.

| Variable | Definition |
|---|---|
| `japancountry` | Total value of Japan's exports to importing country *m* |
| `worldcountry` | Total value of exports from all countries to *m* (the size of *m*'s import market) |
| `japanx` | Exports from all countries to *m*, restricted to the commodities Japan actually ships to *m* |

All three are indexed by year × partner country. By construction
`japancountry ≤ japanx ≤ worldcountry` must hold, and the notebook checks it.

Output goes to `data/variables/` in three shapes (per-year, wide, long).

## Notes

- **`dtype` must be specified when reading.** Without it `0201` becomes `201` and the commodity
  codes are corrupted.

  ```python
  pd.read_csv(path, dtype={"cmdCode": str, "classificationCode": str})
  ```

- **Use `fobvalue` or `primaryValue` for export values.** `cifvalue` is almost entirely empty in
  export data.
- **Recent years are incomplete.** The number of reporting countries falls from 165 in 2023 to
  138 in 2024 and 93 in 2025, so year-over-year comparisons understate the latest figures.
- **`partnerDesc == "World"` is an aggregate row.** Adding it to individual partners double-counts.

See [`DESIGN.md`](DESIGN.md) for details.
