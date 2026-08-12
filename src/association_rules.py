"""
Association rule mining module.

Responsibilities
----------------
* Mine frequent itemsets with the Apriori algorithm (mlxtend).
* Generate association rules and rank them by support, confidence and lift.
* Persist results to ``outputs/results`` as CSV files.
* Load the persisted results back into memory for the web app.

The two supported metrics that drive the analysis:

* **Support**   - fraction of transactions containing the itemset.
* **Confidence**- probability that B is bought given A is bought
                  ``P(A -> B) = support(A∪B) / support(A)``.
* **Lift**      - how much more likely B is bought with A than alone
                  ``lift = support(A∪B) / (support(A) * support(B))``.
"""

import pandas as pd

from src import PLOTS_DIR, RESULTS_DIR
from mlxtend.frequent_patterns import apriori, association_rules


def mine_frequent_itemsets(encoded_df, min_support=0.003, max_len=3):
    """Mine frequent itemsets from a one-hot encoded DataFrame.

    Parameters
    ----------
    encoded_df : pd.DataFrame
        Binary matrix produced by ``preprocessing.one_hot_encode``.
    min_support : float
        Minimum support threshold (fraction of transactions).
    max_len : int
        Maximum size of a mined itemset (2 = pairs only, 3 = adds triples).

    Returns a DataFrame with columns ``support`` and ``itemsets`` where
    every itemset is a ``frozenset`` of product names.
    """
    encoded_df = encoded_df.astype(bool)
    return apriori(encoded_df, min_support=min_support, use_colnames=True,
                   max_len=max_len)


def generate_rules(frequent_itemsets, min_confidence=0.2, min_lift=1.5):
    """Turn frequent itemsets into association rules.

    Only rules whose confidence is at least ``min_confidence`` and whose
    lift is at least ``min_lift`` are kept, which removes weak or spurious
    combinations.
    """
    rules = association_rules(frequent_itemsets, metric="confidence",
                              min_threshold=min_confidence)
    rules = rules[rules["lift"] >= min_lift].copy()
    rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)
    return rules


def _items_to_str(items):
    """Render an itemset as a human friendly, sortable string."""
    if isinstance(items, str):
        return items
    return ", ".join(sorted(items))


def _str_to_items(value):
    """Parse a ``", "`` separated string back into a frozenset."""
    return frozenset(str(value).split(", "))


def save_results(frequent_itemsets, rules, results_dir=RESULTS_DIR):
    """Persist itemsets and rules to CSV files in ``outputs/results``."""
    results_dir.mkdir(parents=True, exist_ok=True)

    itemsets_csv = results_dir / "frequent_itemsets.csv"
    rules_csv = results_dir / "association_rules.csv"

    frequent_itemsets_out = frequent_itemsets.copy()
    frequent_itemsets_out["itemsets"] = frequent_itemsets_out["itemsets"].apply(_items_to_str)
    frequent_itemsets_out.to_csv(itemsets_csv, index=False)

    rules_out = rules.copy()
    rules_out["antecedents"] = rules_out["antecedents"].apply(_items_to_str)
    rules_out["consequents"] = rules_out["consequents"].apply(_items_to_str)
    rules_out.to_csv(rules_csv, index=False)

    return itemsets_csv, rules_csv


def load_frequent_itemsets(csv_path=None):
    """Load a previously saved frequent itemsets CSV."""
    path = csv_path or RESULTS_DIR / "frequent_itemsets.csv"
    df = pd.read_csv(path)
    df["itemsets"] = df["itemsets"].apply(_str_to_items)
    return df


def load_rules(csv_path=None):
    """Load a previously saved association rules CSV.

    The ``antecedents`` / ``consequents`` string columns are converted back
    into ``frozenset`` objects so the rest of the code can use them.
    """
    path = csv_path or RESULTS_DIR / "association_rules.csv"
    df = pd.read_csv(path)
    df["antecedents"] = df["antecedents"].apply(_str_to_items)
    df["consequents"] = df["consequents"].apply(_str_to_items)
    return df


def top_rules(rules, n=20):
    """Return the *n* strongest rules, ranked by lift."""
    return rules.sort_values("lift", ascending=False).head(n).reset_index(drop=True)


def filter_rules(rules, product=None, min_confidence=0.0, min_lift=0.0,
                 sort_by="lift", ascending=False, limit=None):
    """Filter and sort rules for interactive exploration.

    Parameters
    ----------
    rules : pd.DataFrame
        Rules with frozenset ``antecedents`` / ``consequents`` columns.
    product : str, optional
        Keep only rules mentioning this product on either side (substring
        match, case-insensitive).
    min_confidence, min_lift : float
        Lower bounds on the respective metric.
    sort_by : str
        Column to sort by (any rule column, e.g. ``lift``, ``confidence``).
    ascending : bool
        Sort direction.
    limit : int, optional
        Maximum number of rules to return.

    Returns a filtered, optionally sorted copy of the rules.
    """
    result = rules.copy()
    if product:
        needle = str(product).strip().lower()
        if needle:
            def _mentions(items):
                return any(needle in str(item).strip().lower() for item in items)
            mask = result["antecedents"].apply(_mentions) | \
                   result["consequents"].apply(_mentions)
            result = result[mask]
    if min_confidence:
        result = result[result["confidence"] >= min_confidence]
    if min_lift:
        result = result[result["lift"] >= min_lift]
    if sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=ascending)
    if limit:
        result = result.head(limit)
    return result.reset_index(drop=True)


def plot_top_rules(rules, top_n=20, output_path=None):
    """Scatter plot of the strongest rules (lift drives the colour scale)."""
    from matplotlib import pyplot as plt
    from matplotlib import get_backend
    from pathlib import Path

    strongest = top_rules(rules, n=top_n)
    plt.figure(figsize=(11, 7))
    sc = plt.scatter(strongest["support"], strongest["confidence"],
                     c=strongest["lift"], cmap="viridis", s=120,
                     edgecolors="black", linewidths=0.5)
    plt.colorbar(sc, label="Lift")
    plt.title(f"Top {top_n} Association Rules - Support vs Confidence")
    plt.xlabel("Support")
    plt.ylabel("Confidence")
    plt.tight_layout()

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.suffix == "":
            output_path = PLOTS_DIR / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
    if "agg" not in get_backend().lower():
        plt.show()
    plt.close()


def run_association_mining(encoded_df, min_support=0.003, min_confidence=0.2,
                           min_lift=1.5, max_len=3, results_dir=RESULTS_DIR,
                           plots_dir=PLOTS_DIR):
    """End-to-end frequent itemset mining + rule generation.

    The support threshold is progressively lowered if the initial run does
    not produce any rules, which keeps the pipeline robust on small or
    sparse datasets.

    Returns ``(frequent_itemsets, rules)`` and writes the following files:

    * ``outputs/results/frequent_itemsets.csv``
    * ``outputs/results/association_rules.csv``
    * ``outputs/plots/association_rules.png``
    """
    itemsets = mine_frequent_itemsets(encoded_df, min_support=min_support,
                                      max_len=max_len)
    rules = generate_rules(itemsets, min_confidence=min_confidence,
                           min_lift=min_lift)

    # Adaptive fallback: relax the support threshold until rules appear.
    if rules.empty and min_support > 0.0005:
        for support in (0.002, 0.001, 0.0005):
            itemsets = mine_frequent_itemsets(encoded_df, min_support=support,
                                              max_len=max_len)
            rules = generate_rules(itemsets, min_confidence=min_confidence,
                                   min_lift=min_lift)
            if not rules.empty:
                break

    save_results(itemsets, rules, results_dir=results_dir)
    plot_top_rules(rules, top_n=20,
                   output_path=plots_dir / "association_rules.png")
    return itemsets, rules
