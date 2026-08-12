"""
Recommendation engine module.

Responsibilities
----------------
* Load (or lazily recompute) the association rules.
* Given the products a user already picked, find the rules whose
  antecedent matches and recommend the consequents.
* Rank the recommendations so the most confident / highest-lift products
  appear first.
* Expose helpers for the Flask web UI (product list, top combinations).

Recommendation logic
--------------------
For a basket ``{bread, milk}`` we look for every rule
``{bread} -> X`` or ``{milk} -> X`` where the rule's antecedent is a subset
of the basket and its consequent is *not* already in the basket. Each such
consequent is a candidate recommendation, and we keep the strongest rule
(best lift, then best confidence) that produced it.
"""

import os
from collections import Counter

from src import RESULTS_DIR
from src.association_rules import load_rules, run_association_mining
from src.preprocessing import preprocess_dataset


def ensure_rules(rules_path=None, **mining_kwargs):
    """Return the mined rules, recomputing them if necessary.

    Prefer loading the persisted ``association_rules.csv``. If it does not
    exist yet, run the full mining pipeline (preprocessing + Apriori) so
    the web app works out of the box.
    """
    csv_path = rules_path or (RESULTS_DIR / "association_rules.csv")
    if os.path.exists(csv_path):
        return load_rules(csv_path)

    _, _, encoded = preprocess_dataset()
    _, rules = run_association_mining(encoded, **mining_kwargs)
    return rules


def get_all_products(rules):
    """All products that appear in any rule, sorted alphabetically."""
    products = set()
    for rule in rules.itertuples():
        products.update(rule.antecedents)
        products.update(rule.consequents)
    return sorted(products)


def get_top_product_combinations(rules, n=10):
    """The strongest *n* rules overall, formatted for display."""
    combinations = []
    for rule in rules.sort_values("lift", ascending=False).head(n).itertuples():
        combinations.append({
            "antecedents": sorted(rule.antecedents),
            "consequents": sorted(rule.consequents),
            "support": round(float(rule.support), 4),
            "confidence": round(float(rule.confidence), 4),
            "lift": round(float(rule.lift), 2),
        })
    return combinations


def recommend(selected_products, rules, top_n=5):
    """Recommend products based on the items in the user's basket.

    Parameters
    ----------
    selected_products : list[str]
        Products the user has already chosen.
    rules : pd.DataFrame
        Association rules (see :func:`ensure_rules`).
    top_n : int
        Maximum number of recommendations to return.

    Returns a list of dicts::

        [
            {"product": "whole milk",
             "confidence": 0.41, "lift": 2.1,
             "rule": "butter, yogurt"},
            ...
        ]
    """
    selected_products = selected_products or []
    selected = {str(item).strip().lower() for item in selected_products}
    if not selected:
        return []

    # Sort by lift first, then confidence, so the first hit per product is
    # the strongest rule for that product.
    ranked = rules.sort_values(["lift", "confidence"], ascending=False)

    recommendations = {}
    for rule in ranked.itertuples():
        antecedents = {str(a).strip().lower() for a in rule.antecedents}
        consequents = {str(c).strip().lower() for c in rule.consequents}

        if not antecedents or not antecedents.issubset(selected):
            continue

        new_products = consequents - selected
        for product in new_products:
            if product in recommendations:
                continue
            recommendations[product] = {
                "product": product,
                "confidence": round(float(rule.confidence), 3),
                "lift": round(float(rule.lift), 2),
                "rule": ", ".join(sorted(antecedents)),
            }
            if len(recommendations) >= top_n:
                return list(recommendations.values())

    return list(recommendations.values())


def demo_recommendations(rules, n=5):
    """Pick the single most frequent product and recommend for it."""
    if rules.empty:
        return None, []

    antecedent_counts = Counter()
    for rule in rules.itertuples():
        for product in rule.antecedents:
            antecedent_counts[product.lower()] += 1

    if not antecedent_counts:
        return None, []

    top_product = max(antecedent_counts, key=antecedent_counts.get)
    return top_product, recommend([top_product], rules, top_n=n)
