"""Tests for the data preprocessing module."""

import pandas as pd

from src.preprocessing import clean_transactions, one_hot_encode


def _sample_raw():
    """A tiny raw DataFrame resembling the market basket file."""
    return pd.DataFrame(
        {
            0: ["shrimp", "milk", " bread ", None, None],
            1: ["almonds", None, "eggs", "bread", None],
            2: [None, None, "bread", "milk", None],
        }
    )


def test_clean_transactions_drops_empty_and_duplicates():
    raw = _sample_raw()
    transactions = clean_transactions(raw)

    assert isinstance(transactions, list)
    assert len(transactions) == 4  # the all-empty row is removed
    assert transactions[0] == ["shrimp", "almonds"]
    assert transactions[1] == ["milk"]
    assert "bread" in transactions[2]


def test_clean_transactions_strips_whitespace():
    raw = _sample_raw()
    transactions = clean_transactions(raw)
    assert "bread" in transactions[3]
    assert not any(" bread " in item for item in transactions[3])


def test_clean_transactions_deduplicates_items():
    raw = pd.DataFrame({0: ["milk", "milk"], 1: ["milk", "eggs"]})
    transactions = clean_transactions(raw)
    assert transactions[0] == ["milk"]


def test_one_hot_encode_shape_and_values():
    transactions = [["milk", "bread"], ["bread"], ["eggs", "milk"]]
    encoded = one_hot_encode(transactions)

    assert isinstance(encoded, pd.DataFrame)
    assert encoded.shape == (3, 3)
    assert set(encoded.columns) == {"milk", "bread", "eggs"}
    assert encoded.loc[0, "milk"] == 1
    assert encoded.loc[0, "eggs"] == 0
    assert encoded.loc[1, "bread"] == 1


def test_one_hot_encode_empty_transactions():
    encoded = one_hot_encode([])
    assert encoded.empty
