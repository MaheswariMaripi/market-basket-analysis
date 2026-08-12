"""
Market Basket Analysis - end-to-end pipeline runner.

Run the complete project from raw data to recommendations::

    python main.py

Optional arguments
------------------
    --dataset PATH       Path to a custom CSV file.
    --min-support 0.003  Support threshold for Apriori.
    --min-confidence 0.2 Confidence threshold for rules.
    --min-lift 1.5       Lift threshold for rules.

Everything produced (plots, CSVs) is written into the ``outputs/`` folder.
"""

import argparse
import os
import time

os.environ.setdefault("MPLBACKEND", "Agg")

from src import PLOTS_DIR, RESULTS_DIR
from src.preprocessing import preprocess_dataset
from src.eda import run_eda
from src.association_rules import run_association_mining
from src.clustering import run_clustering
from src.recommendation import demo_recommendations, ensure_rules


def _section(title):
    print("\n" + "=" * 62)
    print(f"  {title}")
    print("=" * 62)


def main():
    parser = argparse.ArgumentParser(description="Market Basket Analysis pipeline")
    parser.add_argument("--dataset", default=None,
                        help="Path to a custom CSV dataset (default: data folder)")
    parser.add_argument("--min-support", type=float, default=0.003,
                        help="Minimum support for Apriori (default: 0.003)")
    parser.add_argument("--min-confidence", type=float, default=0.20,
                        help="Minimum confidence for rules (default: 0.20)")
    parser.add_argument("--min-lift", type=float, default=1.5,
                        help="Minimum lift for rules (default: 1.5)")
    args = parser.parse_args()

    start = time.time()

    # ------------------------------------------------------------------
    # Phase 2 & 3 - Data loading and preprocessing
    # ------------------------------------------------------------------
    _section("PHASE 1 | Data loading & preprocessing")
    raw_df, transactions, encoded = preprocess_dataset(args.dataset)
    print(f"  Raw rows loaded:           {raw_df.shape[0]:>8,}")
    print(f"  Non-empty transactions:    {len(transactions):>8,}")
    print(f"  Unique products:           {encoded.shape[1]:>8,}")

    # ------------------------------------------------------------------
    # Phase 4 - Exploratory Data Analysis
    # ------------------------------------------------------------------
    _section("PHASE 2 | Exploratory data analysis")
    stats = run_eda(transactions)
    print(f"  Transactions analysed:     {stats['n_transactions']:>8,}")
    print(f"  Unique products:           {stats['n_unique_products']:>8,}")
    print(f"  Average basket size:       {stats['avg_basket_size']:.2f}")
    print(f"  Largest basket size:       {stats['max_basket_size']:>8,}")
    print(f"  Most frequent product:     {stats['most_frequent_product']}"
          f"  ({stats['most_frequent_count']:,} baskets)")
    print(f"  Plots written to:          {PLOTS_DIR}")

    # ------------------------------------------------------------------
    # Phase 5 & 6 - Frequent itemset mining and association rules
    # ------------------------------------------------------------------
    _section("PHASE 3 | Frequent itemsets & association rules")
    itemsets, rules = run_association_mining(
        encoded,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
    )
    print(f"  Frequent itemsets found:   {len(itemsets):>8,}")
    print(f"  Association rules found:   {len(rules):>8,}")
    print(f"  Results written to:        {RESULTS_DIR}")

    # ------------------------------------------------------------------
    # Phase 7 - Rule analysis (strongest combinations)
    # ------------------------------------------------------------------
    _section("PHASE 4 | Strongest product combinations")
    strongest = rules.sort_values("lift", ascending=False).head(10)
    print(f"  {'Antecedent':<28} {'Consequent':<28} {'Supp.':>6} {'Conf.':>7} {'Lift':>6}")
    print("  " + "-" * 78)
    for rule in strongest.itertuples():
        ante = ", ".join(sorted(rule.antecedents))[:27]
        conseq = ", ".join(sorted(rule.consequents))[:27]
        print(f"  {ante:<28} {conseq:<28} {rule.support:6.3f} {rule.confidence:7.3f} {rule.lift:6.2f}")

    # ------------------------------------------------------------------
    # Phase 8 - Product segmentation (data-driven categories)
    # ------------------------------------------------------------------
    _section("PHASE 5 | Product segmentation")
    seg_stats = run_clustering(encoded)
    if seg_stats["n_clusters"]:
        print(f"  Products segmented:        {seg_stats['n_products']:>8,}")
        print(f"  Segments found:            {seg_stats['n_clusters']:>8,}")
        print(f"  Silhouette score:          {seg_stats['silhouette']:.3f}")
        print(f"  Results written to:        {seg_stats['paths']['clusters_csv']}")
        for cluster_id, info in seg_stats["clusters"].items():
            headline = ", ".join(info["top_products"][:4])
            print(f"    Segment {cluster_id + 1} "
                  f"({info['size']} products, {info['share']:.0%}): {headline}")
    else:
        print("  No meaningful segments could be derived from this dataset.")

    # ------------------------------------------------------------------
    # Phase 9 - Recommendation engine demo
    # ------------------------------------------------------------------
    _section("PHASE 6 | Sample recommendation")
    product, recommendations = demo_recommendations(rules, n=5)
    if product:
        print(f"  Basket selected:           {product}")
        for rec in recommendations:
            print(f"  -> {rec['product']:<24} "
                  f"confidence {rec['confidence']:.2f}   lift {rec['lift']:.2f}")

    # ------------------------------------------------------------------
    # Phase 10 - Sanity checks
    # ------------------------------------------------------------------
    _section("PHASE 7 | Verification")
    rules_reloaded = ensure_rules()
    print(f"  Rules loaded from disk:    {len(rules_reloaded):>8,}")
    print(f"  Recomputed rules match:    {len(rules) == len(rules_reloaded)}")

    print(f"\nPipeline finished in {time.time() - start:.1f} seconds.")
    print("Run 'python app/app.py' to launch the web application.")


if __name__ == "__main__":
    main()
