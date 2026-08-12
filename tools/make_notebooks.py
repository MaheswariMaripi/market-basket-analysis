"""
Generate the five Jupyter notebooks for the project.

This is a helper script: each notebook is written as JSON (nbformat v4)
with clean, readable cells so the notebooks can also be edited by hand
inside Jupyter later.

Usage::

    python tools/make_notebooks.py
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

BOOTSTRAP = (
    "import sys\n"
    'sys.path.insert(0, "..")\n'
    "\n"
    "import pandas as pd\n"
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "import seaborn as sns\n"
    "\n"
    "%matplotlib inline\n"
)


def _markdown(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def _code(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def _notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_notebooks():
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

    notebooks = {
        # ------------------------------------------------------------------
        "01_data_preprocessing.ipynb": [
            _markdown(
                "# 01 - Data Preprocessing\n"
                "\n"
                "In this notebook we load the raw market basket dataset, handle\n"
                "missing values and convert it into a clean transaction format\n"
                "ready for association rule mining.\n"
                "\n"
                "The reusable functions live in `src/preprocessing.py`."
            ),
            _code(BOOTSTRAP),
            _code(
                "from src.preprocessing import load_raw_dataframe\n"
                "\n"
                "raw = load_raw_dataframe()\n"
                "print('Shape of the raw dataset:', raw.shape)\n"
                "raw.head()"
            ),
            _code(
                "print('Missing values per column:')\n"
                "print(raw.isna().sum().describe().astype(int))\n"
                "print(f'Total empty cells: {raw.isna().sum().sum():,}')"
            ),
            _code(
                "from src.preprocessing import clean_transactions\n"
                "\n"
                "transactions = clean_transactions(raw)\n"
                "print(f'Number of non-empty transactions: {len(transactions):,}')\n"
                "transactions[:5]"
            ),
            _code(
                "from src.preprocessing import one_hot_encode\n"
                "\n"
                "encoded = one_hot_encode(transactions)\n"
                "print('One-hot encoded shape (transactions x products):', encoded.shape)\n"
                "encoded.head()"
            ),
            _markdown(
                "## Summary\n"
                "\n"
                "* The raw file contains sparse, ragged rows with many empty cells.\n"
                "* Empty cells, whitespace and duplicate items were removed.\n"
                "* The data is now a binary matrix: 1 means the product appears in\n"
                "  the transaction, 0 means it does not - the exact input format\n"
                "  expected by the Apriori algorithm."
            ),
        ],
        # ------------------------------------------------------------------
        "02_exploratory_analysis.ipynb": [
            _markdown(
                "# 02 - Exploratory Data Analysis\n"
                "\n"
                "We analyse shopping behaviour: which products are bought most\n"
                "often, how many items people buy per visit and how purchase\n"
                "frequency is distributed across the catalogue."
            ),
            _code(BOOTSTRAP),
            _code(
                "from src.preprocessing import preprocess_dataset\n"
                "from src.eda import item_frequencies, transaction_lengths\n"
                "\n"
                "raw, transactions, encoded = preprocess_dataset()\n"
                "frequencies = item_frequencies(transactions)\n"
                "lengths = transaction_lengths(transactions)\n"
                "print(f'Transactions: {len(transactions):,}')\n"
                "print(f'Unique products: {frequencies.shape[0]:,}')\n"
                "print(f'Average basket size: {lengths.mean():.2f}')\n"
                "print(f'Largest basket: {lengths.max()} items')"
            ),
            _code(
                "frequencies.head(10)"
            ),
            _markdown(
                "### Top products and frequency distribution\n"
                "\n"
                "The most frequently purchased products are visualised below,"
                " together with how purchase frequency is distributed."
            ),
            _code(
                "from src.eda import plot_top_items, plot_frequency_distribution, plot_basket_size_distribution\n"
                "\n"
                "plot_top_items(frequencies, top_n=20)"
            ),
            _code(
                "plot_frequency_distribution(frequencies, top_n=50)"
            ),
            _code(
                "plot_basket_size_distribution(lengths)"
            ),
            _markdown(
                "## Observations\n"
                "\n"
                "* A small group of products (e.g. mineral water, eggs, milk) is\n"
                "  bought very frequently while most products appear rarely.\n"
                "* Most baskets contain between 1 and a handful of items - the\n"
                "  long tail is typical for market basket data.\n"
                "* The right skew confirms that simple frequency ranking alone is\n"
                "  not enough; association rules are needed to find combinations."
            ),
        ],
        # ------------------------------------------------------------------
        "03_apriori_analysis.ipynb": [
            _markdown(
                "# 03 - Frequent Itemsets & Association Rules (Apriori)\n"
                "\n"
                "We apply the Apriori algorithm to find frequently co-occurring\n"
                "products and then extract association rules with support,\n"
                "confidence and lift."
            ),
            _code(BOOTSTRAP),
            _code(
                "from src.preprocessing import preprocess_dataset\n"
                "\n"
                "raw, transactions, encoded = preprocess_dataset()\n"
                "encoded.head()"
            ),
            _markdown(
                "### Mining frequent itemsets\n"
                "\n"
                "`min_support=0.003` means an itemset must appear in at least\n"
                "`0.003 * 7501 ≈ 22` transactions to be considered frequent."
            ),
            _code(
                "from src.association_rules import mine_frequent_itemsets, generate_rules\n"
                "\n"
                "itemsets = mine_frequent_itemsets(encoded, min_support=0.003, max_len=3)\n"
                "print(f'Frequent itemsets found: {len(itemsets):,}')\n"
                "itemsets.sort_values('support', ascending=False).head(10)"
            ),
            _code(
                "rules = generate_rules(itemsets, min_confidence=0.2, min_lift=1.5)\n"
                "print(f'Association rules found: {len(rules):,}')\n"
                "rules.head(10)"
            ),
            _markdown(
                "### Strongest rules by lift\n"
                "\n"
                "Lift > 1 means the products are positively associated: buying the\n"
                "antecedent makes the consequent more likely."
            ),
            _code(
                "from src.association_rules import top_rules, plot_top_rules\n"
                "\n"
                "top_rules(rules, n=10)"
            ),
            _code(
                "plot_top_rules(rules, top_n=20)"
            ),
            _markdown(
                "## Interpretation\n"
                "\n"
                "Rules with high lift reveal products that customers genuinely buy\n"
                "together - the foundation of the recommendation system in the\n"
                "next notebook."
            ),
        ],
        # ------------------------------------------------------------------
        "04_recommendation_system.ipynb": [
            _markdown(
                "# 04 - Recommendation System\n"
                "\n"
                "The mined association rules are turned into a simple but effective\n"
                "recommendation engine: pick a basket, get suggested add-on products\n"
                "with their confidence and lift."
            ),
            _code(BOOTSTRAP),
            _code(
                "from src.recommendation import ensure_rules, get_all_products, get_top_product_combinations\n"
                "\n"
                "rules = ensure_rules()\n"
                "print(f'Loaded {len(rules):,} association rules')\n"
                "get_top_product_combinations(rules, n=5)"
            ),
            _markdown(
                "### Try a recommendation\n"
                "\n"
                "Imagine a customer buying the following products..."
            ),
            _code(
                "basket = ['mineral water', 'chocolate']\n"
                "\n"
                "from src.recommendation import recommend\n"
                "\n"
                "recommendations = recommend(basket, rules, top_n=5)\n"
                "for rec in recommendations:\n"
                "    print(f\"{rec['product']:<25} confidence {rec['confidence']:.2f}  "
                "lift {rec['lift']:.2f}  (rule: {rec['rule']})\")"
            ),
            _code(
                "basket = ['whole milk', 'yogurt']\n"
                "recommend(basket, rules, top_n=5)"
            ),
            _markdown(
                "## Wrap-up\n"
                "\n"
                "The same engine powers the Flask web app in `app/`. Run\n"
                "`python app/app.py` to use it interactively in the browser."
            ),
        ],
        # ------------------------------------------------------------------
        "05_product_segmentation.ipynb": [
            _markdown(
                "# 05 - Product Segmentation\n"
                "\n"
                "Beyond association rules, we group products into data-driven\n"
                "segments by clustering their *co-occurrence patterns* with K-means."
            ),
            _code(BOOTSTRAP),
            _code(
                "from src.preprocessing import preprocess_dataset\n"
                "\n"
                "raw, transactions, encoded = preprocess_dataset()\n"
                "print(f'Transactions: {len(transactions):,}')\n"
                "print(f'Unique products: {encoded.shape[1]:,}')"
            ),
            _markdown(
                "### Co-occurrence matrix\n"
                "\n"
                "Every product is described by how often it is bought together with\n"
                "every other product. `encoded.T @ encoded` gives those counts."
            ),
            _code(
                "from src.clustering import co_occurrence_matrix\n"
                "\n"
                "cooc = co_occurrence_matrix(encoded)\n"
                "cooc.iloc[:5, :5]"
            ),
            _markdown(
                "### Run K-means clustering\n"
                "\n"
                "The number of clusters is chosen with the silhouette score.\n"
                "Products with fewer than 5 baskets are skipped to reduce noise."
            ),
            _code(
                "from src.clustering import cluster_products\n"
                "\n"
                "assignments, silhouette = cluster_products(encoded, min_frequency=5)\n"
                "print(f'Clusters found: {assignments[\"cluster\"].nunique()}')\n"
                "print(f'Silhouette score: {silhouette:.3f}')\n"
                "assignments.head(15)"
            ),
            _code(
                "from src.clustering import summarize_clusters\n"
                "\n"
                "summary = summarize_clusters(assignments)\n"
                "for cluster_id, info in summary.items():\n"
                "    print(f\"Segment {cluster_id + 1} ({info['size']} products, "
                "{info['share']:.0%}):\")\n"
                "    print('   ', ', '.join(info['top_products'][:6]))"
            ),
            _code(
                "from src.clustering import run_clustering\n"
                "\n"
                "stats = run_clustering(encoded)\n"
                "print('Plot saved to:', stats['paths']['clusters_plot'])"
            ),
            _markdown(
                "## Interpretation\n"
                "\n"
                "* Products clustered together share purchase context: they tend to\n"
                "  appear in the same baskets.\n"
                "* The segments are learned from the data, so they can reveal\n"
                "  categories a manual taxonomy would miss.\n"
                "* Combine with the association rules for a complete picture:\n"
                "  rules tell you *what goes together*, segments tell you *which\n"
                "  products form families*."
            ),
        ],
    }

    for name, cells in notebooks.items():
        path = NOTEBOOKS_DIR / name
        path.write_text(json.dumps(_notebook(cells), indent=1), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    build_notebooks()
