"""
Market Basket Analysis - core source package.

This package contains the reusable building blocks of the project:

* :mod:`src.preprocessing`    - loading, cleaning and encoding the dataset
* :mod:`src.eda`              - exploratory data analysis and visualisations
* :mod:`src.association_rules`- Apriori frequent itemset mining and rules
* :mod:`src.recommendation`   - recommendation engine built on the rules

Every module below relies on the shared paths defined here so that the
project can be moved around without breaking anything.
"""

from pathlib import Path

# Project layout ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
PLOTS_DIR = OUTPUT_DIR / "plots"
RESULTS_DIR = OUTPUT_DIR / "results"

# Raw dataset (kept unchanged, never overwritten)
DATASET_FILE = DATA_DIR / "Market_Basket_Optimisation.csv"

__version__ = "1.0.0"
