"""
Data preprocessing module.

Responsibilities
----------------
1. Locate and load the raw ``Market_Basket_Optimisation.csv`` dataset.
2. Detect (and drop) a header row if one is present.
3. Handle missing / empty values.
4. Convert every row into a clean transaction (a list of unique items).
5. One-hot encode the transactions into a format the Apriori algorithm
   (mlxtend) understands.

The raw dataset file is only ever read, never modified.
"""

import pandas as pd

from src import DATA_DIR, DATASET_FILE

# Values that should be treated as "no item" after stripping whitespace.
_EMPTY_TOKENS = {"", "nan", "none", "null", "-", "n/a"}


def _resolve_dataset_path(csv_path=None):
    """Return the dataset path, falling back to the default location.

    If the exact default filename is missing, any ``.csv`` file placed in
    the ``data/`` folder is used instead. Raises FileNotFoundError when no
    dataset can be found.
    """
    if csv_path is not None:
        return str(csv_path)

    if DATASET_FILE.exists():
        return str(DATASET_FILE)

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if csv_files:
        return str(csv_files[0])

    raise FileNotFoundError(
        "No dataset found. Place 'Market_Basket_Optimisation.csv' inside "
        "the 'data/' folder and try again."
    )


def _looks_like_header(df):
    """Heuristically detect whether the first row is a column header.

    Product names in the market basket data are repeated across many rows.
    If the majority of the values in the first row are never seen again in
    the rest of the file, we treat that row as a header.
    """
    first_row = [str(v).strip() for v in df.iloc[0] if pd.notna(v)]
    if not first_row:
        return False

    seen = set()
    for col in df.columns:
        for value in df.iloc[1:][col].dropna():
            seen.add(str(value).strip().lower())

    column_like = sum(1 for v in first_row if v.strip().lower() not in seen)
    return column_like > len(first_row) / 2


def load_raw_dataframe(csv_path=None):
    """Load the CSV into a pandas DataFrame.

    The market basket file has no header row, so it is read with
    ``header=None``. If a header is detected (see :func:`_looks_like_header`)
    it is removed and the columns are re-labelled with integers.
    """
    path = _resolve_dataset_path(csv_path)
    raw = pd.read_csv(path, header=None)

    if _looks_like_header(raw):
        raw = raw.iloc[1:].reset_index(drop=True)
        raw.columns = list(range(raw.shape[1]))

    return raw.astype(object)


def clean_transactions(raw):
    """Convert a raw DataFrame into a list of clean transactions.

    * Empty cells and empty strings are removed.
    * Items are stripped of surrounding whitespace.
    * Duplicate items inside one basket are dropped (a product appears at
      most once per transaction).
    * Rows that end up with no items are discarded.

    Returns a list of lists, e.g. ``[["milk", "bread"], ["eggs"]]``.
    """
    transactions = []
    for _, row in raw.iterrows():
        items = []
        seen = set()
        for value in row:
            if pd.isna(value):
                continue
            item = str(value).strip()
            if item.lower() in _EMPTY_TOKENS:
                continue
            key = item.lower()
            if key not in seen:
                seen.add(key)
                items.append(item)
        if items:
            transactions.append(items)
    return transactions


def one_hot_encode(transactions):
    """One-hot encode a list of transactions into a binary DataFrame.

    Each row corresponds to one transaction and each column to one unique
    product. A value of ``1`` means the product was bought in that basket,
    ``0`` means it was not. This is the exact format required by
    ``mlxtend.frequent_patterns.apriori``. An empty list produces an empty
    DataFrame.
    """
    from mlxtend.preprocessing import TransactionEncoder

    if not transactions:
        return pd.DataFrame()

    encoder = TransactionEncoder()
    encoded = encoder.fit_transform(transactions)
    encoded_df = pd.DataFrame(encoded, columns=encoder.columns_).astype(int)
    return encoded_df


def preprocess_dataset(csv_path=None):
    """Run the whole preprocessing pipeline in one call.

    Returns a tuple ``(raw, transactions, encoded_df)`` so callers can use
    any of the three representations without re-reading the file.
    """
    raw = load_raw_dataframe(csv_path)
    transactions = clean_transactions(raw)
    encoded = one_hot_encode(transactions)
    return raw, transactions, encoded


if __name__ == "__main__":
    raw_df, tx, one_hot = preprocess_dataset()
    print(f"Dataset rows (raw):        {raw_df.shape[0]:>8,}")
    print(f"Non-empty transactions:    {len(tx):>8,}")
    print(f"Unique products:           {one_hot.shape[1]:>8,}")
