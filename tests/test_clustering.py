"""Tests for the product clustering / segmentation module."""

import pandas as pd
import pytest

from src.clustering import (co_occurrence_matrix, cluster_products,
                            run_clustering, summarize_clusters)
from src.preprocessing import one_hot_encode


def _sample_transactions():
    """Two clear groups: dairy-ish products vs snacks/drinks."""
    dairy = ["milk", "yogurt", "cheese", "butter"]
    snacks = ["chips", "soda", "chocolate", "candy"]
    transactions = []
    for _ in range(12):
        transactions.append(dairy)
    for _ in range(12):
        transactions.append(snacks)
    for _ in range(3):
        transactions.append(["milk", "chips"])
    return transactions


def test_co_occurrence_matrix_is_symmetric_and_counts_pairs():
    encoded = one_hot_encode([["milk", "bread"], ["milk", "eggs"], ["bread", "eggs"]])
    matrix = co_occurrence_matrix(encoded)

    assert list(matrix.columns) == list(matrix.index)
    assert matrix.loc["milk", "bread"] == 1
    assert matrix.loc["milk", "eggs"] == 1
    assert matrix.loc["bread", "eggs"] == 1
    assert matrix.loc["milk", "milk"] == 2  # appears in two baskets


def test_cluster_products_recovers_two_groups():
    encoded = one_hot_encode(_sample_transactions())
    assignments, silhouette = cluster_products(encoded, min_frequency=1, k_range=(2, 4))

    assert silhouette > 0.2
    assert {"product", "frequency", "cluster"} <= set(assignments.columns)
    assert set(assignments["product"]) == {
        "milk", "yogurt", "cheese", "butter", "chips", "soda", "chocolate", "candy"}


def test_cluster_products_single_product_returns_empty():
    encoded = one_hot_encode([["milk"], ["milk"], ["milk"]])
    assignments, silhouette = cluster_products(encoded)
    assert assignments.empty
    assert silhouette == 0.0


def test_cluster_products_empty_encoded_returns_empty():
    assignments, _ = cluster_products(pd.DataFrame())
    assert assignments.empty


def test_cluster_products_respects_min_frequency():
    transactions = [["milk", "bread"]] * 10 + [["rare", "milk"]]
    encoded = one_hot_encode(transactions)
    assignments, _ = cluster_products(encoded, min_frequency=5, k_range=(2, 3))

    assert "rare" not in assignments["product"].tolist()


def test_summarize_clusters_shape():
    assignments = pd.DataFrame({
        "product": ["a", "b", "c", "d"],
        "frequency": [10, 8, 6, 4],
        "cluster": [0, 0, 1, 1],
    })
    summary = summarize_clusters(assignments, top_n=1)

    assert set(summary.keys()) == {0, 1}
    assert summary[0]["top_products"] == ["a"]
    assert summary[1]["size"] == 2
    assert summary[0]["share"] == pytest.approx(0.5)


def test_run_clustering_writes_outputs(tmp_path):
    encoded = one_hot_encode(_sample_transactions())
    results_dir = tmp_path / "results"
    plots_dir = tmp_path / "plots"

    stats = run_clustering(encoded, results_dir=results_dir, plots_dir=plots_dir)

    assert stats["n_clusters"] >= 2
    assert stats["n_products"] == 8
    assert (results_dir / "product_clusters.csv").exists()
    assert (plots_dir / "product_clusters.png").exists()
    assert "clusters" in stats and "paths" in stats
