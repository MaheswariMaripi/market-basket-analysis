"""Tests for the association rule mining module."""

import pandas as pd
import pytest

from src.association_rules import (generate_rules, load_rules,
                                   mine_frequent_itemsets, save_results,
                                   top_rules)


def _sample_encoded():
    """Small one-hot matrix with a clear A/B co-occurrence pattern."""
    rows = []
    for _ in range(8):
        rows.append({"milk": 1, "bread": 1, "eggs": 1})
    for _ in range(2):
        rows.append({"milk": 1, "bread": 1})
    for _ in range(10):
        rows.append({"soda": 1})
    return pd.DataFrame(rows)


def test_mine_frequent_itemsets_finds_known_pair():
    encoded = _sample_encoded()
    itemsets = mine_frequent_itemsets(encoded, min_support=0.5, max_len=2)

    supports = dict(zip(itemsets["itemsets"], itemsets["support"]))
    pair = frozenset({"milk", "bread"})
    assert pair in supports
    assert supports[pair] == pytest.approx(1.0)


def test_generate_rules_keeps_confident_rules():
    encoded = _sample_encoded()
    itemsets = mine_frequent_itemsets(encoded, min_support=0.3, max_len=2)
    rules = generate_rules(itemsets, min_confidence=0.5, min_lift=1.0)

    assert not rules.empty
    for rule in rules.itertuples():
        assert rule.confidence >= 0.5
        assert rule.lift >= 1.0


def test_top_rules_ranks_by_lift():
    encoded = _sample_encoded()
    itemsets = mine_frequent_itemsets(encoded, min_support=0.3, max_len=2)
    rules = generate_rules(itemsets, min_confidence=0.1, min_lift=0.1)

    top = top_rules(rules, n=3)
    assert len(top) == min(3, len(rules))
    lifts = top["lift"].tolist()
    assert lifts == sorted(lifts, reverse=True)


def test_save_and_load_rules_roundtrip(tmp_path):
    encoded = _sample_encoded()
    itemsets = mine_frequent_itemsets(encoded, min_support=0.3, max_len=2)
    rules = generate_rules(itemsets, min_confidence=0.1, min_lift=0.1)

    save_results(itemsets, rules, results_dir=tmp_path)
    loaded = load_rules(tmp_path / "association_rules.csv")

    assert len(loaded) == len(rules)
    assert all(isinstance(a, frozenset) for a in loaded["antecedents"])
    assert all(isinstance(c, frozenset) for c in loaded["consequents"])


def test_load_rules_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_rules(tmp_path / "does_not_exist.csv")
