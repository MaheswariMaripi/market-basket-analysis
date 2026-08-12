"""
Exploratory Data Analysis (EDA) module.

Responsibilities
----------------
* Compute per-product frequencies.
* Summarise transaction statistics (basket sizes, unique products, ...).
* Produce publication-ready plots and store them in ``outputs/plots``.

All plotting functions accept an explicit output path so they can be used
both from scripts (``main.py``) and from Jupyter notebooks.
"""

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
from matplotlib import pyplot as plt
from collections import Counter
from pathlib import Path

from src import PLOTS_DIR


def _display(plt_handle):
    """Show the figure with an interactive backend, else just close it."""
    if "agg" in matplotlib.get_backend().lower():
        plt_handle.close()
    else:
        plt_handle.show()


def item_frequencies(transactions):
    """Count how many transactions contain each product.

    Returns a Series indexed by product name, sorted descending by count.
    """
    counter = Counter()
    for items in transactions:
        counter.update(items)
    series = pd.Series(counter).sort_values(ascending=False)
    series.name = "frequency"
    return series


def transaction_lengths(transactions):
    """Number of items in every basket, as a numpy array."""
    return np.array([len(basket) for basket in transactions], dtype=int)


def plot_top_items(frequencies, top_n=20, output_path=None):
    """Horizontal bar chart of the *top_n* most frequent products."""
    top = frequencies.head(top_n).iloc[::-1]

    plt.figure(figsize=(10, 8))
    sns.barplot(x=top.values, y=top.index, hue=top.index, palette="viridis",
                legend=False)
    plt.title(f"Top {top_n} Most Frequently Purchased Products")
    plt.xlabel("Number of Transactions")
    plt.ylabel("Product")
    plt.tight_layout()
    _save(plt, output_path)
    return output_path


def plot_frequency_distribution(frequencies, top_n=50, output_path=None):
    """Histogram showing how item frequency is spread across products."""
    plt.figure(figsize=(10, 6))
    sns.histplot(frequencies.head(top_n), bins=20, kde=True, color="steelblue")
    plt.title("Distribution of Product Purchase Frequency")
    plt.xlabel("Purchase Frequency (transactions)")
    plt.ylabel("Number of Products")
    plt.tight_layout()
    _save(plt, output_path)
    return output_path


def plot_basket_size_distribution(lengths, output_path=None):
    """Histogram of how many items customers buy per visit."""
    plt.figure(figsize=(10, 6))
    sns.histplot(lengths, bins=range(1, lengths.max() + 2), discrete=True,
                 color="mediumseagreen")
    plt.title("Basket Size Distribution (Items per Transaction)")
    plt.xlabel("Items per Basket")
    plt.ylabel("Number of Transactions")
    plt.tight_layout()
    _save(plt, output_path)
    return output_path


def _save(plt_handle, output_path):
    """Save the current figure to disk (if a path is given) and close it."""
    if output_path is not None:
        output_path = Path(output_path)
        if output_path.suffix == "":
            output_path = PLOTS_DIR / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt_handle.savefig(output_path, dpi=150, bbox_inches="tight")
    _display(plt_handle)
    plt_handle.close()


def run_eda(transactions, plots_dir=PLOTS_DIR):
    """Run the full EDA pipeline and return summary statistics.

    Generates three plots:

    * ``top_items.png``                 - most frequent products
    * ``item_frequency.png``            - distribution of frequencies
    * ``basket_size_distribution.png``  - items per transaction

    Returns a dictionary of summary numbers useful for reports and the
    console summary printed by ``main.py``.
    """
    plots_dir.mkdir(parents=True, exist_ok=True)

    frequencies = item_frequencies(transactions)
    lengths = transaction_lengths(transactions)

    top_items_path = plot_top_items(frequencies, top_n=20,
                                    output_path=plots_dir / "top_items.png")
    freq_dist_path = plot_frequency_distribution(frequencies, top_n=50,
                                                 output_path=plots_dir / "item_frequency.png")
    basket_dist_path = plot_basket_size_distribution(lengths,
                                                     output_path=plots_dir / "basket_size_distribution.png")

    stats = {
        "n_transactions": len(transactions),
        "n_unique_products": int(frequencies.shape[0]),
        "avg_basket_size": float(np.mean(lengths)),
        "max_basket_size": int(np.max(lengths)),
        "most_frequent_product": str(frequencies.index[0]),
        "most_frequent_count": int(frequencies.iloc[0]),
        "top_items_path": str(top_items_path),
        "item_frequency_path": str(freq_dist_path),
        "basket_size_path": str(basket_dist_path),
    }
    return stats
