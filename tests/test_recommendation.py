"""Tests for the recommendation engine."""

import pandas as pd

from src.recommendation import (get_all_products, get_top_product_combinations,
                                recommend)


def _sample_rules():
    return pd.DataFrame(
        [
            {
                "antecedents": frozenset({"milk", "bread"}),
                "consequents": frozenset({"butter"}),
                "support": 0.05,
                "confidence": 0.60,
                "lift": 2.5,
            },
            {
                "antecedents": frozenset({"milk"}),
                "consequents": frozenset({"cereal"}),
                "support": 0.03,
                "confidence": 0.40,
                "lift": 1.8,
            },
            {
                "antecedents": frozenset({"soda"}),
                "consequents": frozenset({"chips"}),
                "support": 0.02,
                "confidence": 0.90,
                "lift": 3.0,
            },
        ]
    )


def test_recommend_matches_subset_antecedents():
    rules = _sample_rules()
    results = recommend(["milk", "bread"], rules, top_n=5)

    products = [rec["product"] for rec in results]
    assert "butter" in products
    assert "cereal" in products
    assert "chips" not in products  # soda not in the basket


def test_recommend_excludes_items_already_in_basket():
    rules = _sample_rules()
    results = recommend(["milk", "bread", "butter"], rules, top_n=5)
    assert "butter" not in [rec["product"] for rec in results]


def test_recommend_ranks_by_lift():
    rules = _sample_rules()
    results = recommend(["milk", "bread"], rules, top_n=5)
    # butter (lift 2.5) ranks above cereal (lift 1.8)
    assert results[0]["product"] == "butter"


def test_recommend_empty_basket():
    rules = _sample_rules()
    assert recommend([], rules) == []
    assert recommend(None, rules) == []


def test_recommend_respects_top_n():
    rules = _sample_rules()
    results = recommend(["milk"], rules, top_n=1)
    assert len(results) == 1


def test_get_all_products_unique_and_sorted():
    rules = _sample_rules()
    products = get_all_products(rules)
    assert products == sorted(products)
    assert set(products) == {"milk", "bread", "butter", "cereal", "soda", "chips"}


def test_get_top_product_combinations_shape():
    rules = _sample_rules()
    combos = get_top_product_combinations(rules, n=2)
    assert len(combos) == 2
    assert {"antecedents", "consequents", "support", "confidence", "lift"} <= set(combos[0])
