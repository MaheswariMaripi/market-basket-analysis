# Market Basket Analysis

An end-to-end **market basket analysis** project that mines association rules
from transaction data using the Apriori algorithm and exposes the findings
through a web application.

Given the contents of a shopper's basket, the system predicts which products
they are most likely to buy next, ranked by statistical confidence and lift.
It also groups products into data-driven **segments** (clusters) so that
undiscovered product categories emerge from the data itself.

```
raw data ──► cleaning ──► EDA ──► Apriori ──► rules ──► recommendations
                                  │              │
                                  └── clustering ┴──► web app
```

## Features

- **Robust preprocessing** — handles header detection, missing values, whitespace
  and duplicate items; converts transactions to the binary matrix Apriori needs.
- **Exploratory data analysis** — basket-size distribution, product frequency
  charts and summary statistics, rendered as publication-ready PNGs.
- **Association rule mining** — frequent itemsets + rules via `mlxtend`, ranked by
  support / confidence / lift, with an adaptive support fallback for sparse data.
- **Recommendation engine** — given a basket, returns the strongest matching
  consequents with their rule metrics.
- **Product clustering** — K-means segments products by their co-occurrence
  patterns; the "right" number of segments is chosen via the silhouette score.
- **Flask web app** — interactive basket builder, live recommendations, a rule
  explorer with searchable / filterable table, and the generated plots.
- **Automated tests** — pytest suite covering every module.

## Requirements

- Python 3.10+ (developed against 3.13)
- See `requirements.txt` (pandas, numpy, matplotlib, seaborn, mlxtend, flask,
  scikit-learn, jupyter, pytest)

## Setup

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt
```

The dataset `data/Market_Basket_Optimisation.csv` is a well-known public
transaction file (7,501 baskets, ~120 products) and is included so the project
runs out of the box. You can swap in your own CSV at any time (see below).

## Usage

### 1. Run the full pipeline

```powershell
python main.py
```

This runs preprocessing → EDA → Apriori mining → strongest combinations →
recommendations → verification and writes everything into `outputs/`:

```
outputs/
├── plots/
│   ├── top_items.png
│   ├── item_frequency.png
│   ├── basket_size_distribution.png
│   ├── association_rules.png
│   └── product_clusters.png
└── results/
    ├── association_rules.csv
    ├── frequent_itemsets.csv
    └── product_clusters.csv
```

Custom dataset or custom thresholds:

```powershell
python main.py --dataset path\to\file.csv
python main.py --min-support 0.003 --min-confidence 0.2 --min-lift 1.5
```

### 2. Launch the web application

```powershell
python app/app.py
```

Then open <http://127.0.0.1:5000>. The app loads the persisted rules on startup
(and mines them on first run if they do not exist yet), so no extra steps are
needed.

### 3. Run the tests

```powershell
python -m pytest
```

### 4. Explore with notebooks

Pre-generated notebooks live in `notebooks/` and can be regenerated with:

```powershell
python tools/make_notebooks.py
```

## Pipeline phases

| Phase | Module | What happens |
|-------|--------|--------------|
| 1. Data loading & cleaning | `src/preprocessing.py` | Detect/drop headers, strip whitespace, drop empties & duplicates, one-hot encode |
| 2. Exploratory analysis | `src/eda.py` | Frequency tables, basket-size stats, plots |
| 3. Frequent itemsets & rules | `src/association_rules.py` | Apriori, confidence/lift filtering, CSV persistence |
| 4. Strongest combinations | `src/association_rules.py` | Top rules by lift |
| 5. Recommendations | `src/recommendation.py` | Match basket to rule antecedents, rank consequents |
| 6. Product segmentation | `src/clustering.py` | K-means on co-occurrence vectors, silhouette-selected `k`, PCA scatter plot |
| 7. Verification | `src/recommendation.py` | Reload persisted rules and compare |

## Project layout

```
.
├── app/                  Flask web application
│   ├── app.py            Routes + JSON API
│   ├── templates/        index.html
│   └── static/           style.css, script.js
├── data/                 Raw dataset (never modified)
├── notebooks/            Generated Jupyter notebooks
├── outputs/              Generated plots + CSV results
├── src/                  Core Python package
│   ├── preprocessing.py
│   ├── eda.py
│   ├── association_rules.py
│   ├── clustering.py
│   └── recommendation.py
├── tests/                pytest suite
├── tools/                Notebook generator
├── main.py               End-to-end pipeline runner
└── requirements.txt
```

## How the metrics work

- **Support** — fraction of transactions containing the itemset.
- **Confidence** — `P(B | A) = support(A∪B) / support(A)`. How often the
  consequent is bought when the antecedent is bought.
- **Lift** — `support(A∪B) / (support(A) · support(B))`. How many times more
  likely `B` is bought with `A` than alone. Lift `> 1` means a positive
  association; `< 1` means a negative one.

## Extending

- **New dataset** — drop a CSV into `data/` or pass `--dataset`. Any header-less
  transactional CSV works (one basket per row, one product per cell).
- **New analysis** — add a module under `src/`, hook it into `main.py`, and add
  matching tests under `tests/`.
- **New app page** — add a route in `app/app.py` and a template in
  `app/templates/`.

## License

Provided as-is for educational purposes. Dataset is the classic
"Market Basket Optimisation" transaction dataset.
