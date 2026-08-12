"""
Market Basket Analysis - Flask web application.

Provides an interactive interface where a user selects products they have
bought and instantly gets recommendations mined from the association rules.

Run it with::

    python app/app.py

then open http://127.0.0.1:5000 in your browser.
"""

import os
import sys

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

# Make sure the project root is importable regardless of where the app is
# launched from.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import PLOTS_DIR, RESULTS_DIR
from src.association_rules import filter_rules
from src.recommendation import (ensure_rules, get_all_products,
                                get_top_product_combinations, recommend)

app = Flask(__name__)

# ----------------------------------------------------------------------
# Load (or compute) the association rules once at startup.
# ----------------------------------------------------------------------
RULES = ensure_rules()
PRODUCTS = get_all_products(RULES)
TOP_COMBINATIONS = get_top_product_combinations(RULES, n=10)

app.logger.info("Loaded %d association rules for %d products.",
                len(RULES), len(PRODUCTS))


def build_aisles():
    """Group products into storefront 'aisles' using the learned segments.

    Falls back to a single flat list when the segmentation has not been
    computed yet (e.g. before ``python main.py`` has been run).
    """
    clusters = {}
    clusters_csv = RESULTS_DIR / "product_clusters.csv"
    if clusters_csv.exists():
        df = pd.read_csv(clusters_csv)
        for row in df.itertuples():
            clusters.setdefault(int(row.cluster), []).append(row.product)

    assigned = {p for items in clusters.values() for p in items}
    leftover = [p for p in PRODUCTS if p not in assigned]
    if leftover:
        clusters.setdefault(-1, []).extend(leftover)

    aisles = []
    for cluster_id in sorted(clusters):
        name = "Other products" if cluster_id == -1 else f"Aisle {cluster_id + 1}"
        aisles.append({"id": cluster_id, "name": name,
                       "products": sorted(clusters[cluster_id])})
    return aisles


AISLES = build_aisles()


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html",
                           products=PRODUCTS,
                           aisles=AISLES,
                           rules_count=len(RULES),
                           top_combinations=TOP_COMBINATIONS)


# ----------------------------------------------------------------------
# JSON API used by the frontend
# ----------------------------------------------------------------------
@app.route("/api/products", methods=["GET"])
def api_products():
    return jsonify({"products": PRODUCTS})


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    payload = request.get_json(silent=True) or {}
    selected = payload.get("products", [])

    if not isinstance(selected, list) or not selected:
        return jsonify({"error": "Please select at least one product.",
                        "recommendations": []}), 400

    recommendations = recommend(selected, RULES, top_n=5)
    if not recommendations:
        return jsonify({
            "message": "No strong associations found for this basket yet.",
            "recommendations": [],
        })

    return jsonify({"recommendations": recommendations})


@app.route("/api/top_rules", methods=["GET"])
def api_top_rules():
    return jsonify({"top_combinations": TOP_COMBINATIONS})


@app.route("/api/rules", methods=["GET"])
def api_rules():
    """Searchable / filterable rule explorer.

    Query params: product, min_confidence, min_lift, sort_by, limit.
    """
    product = request.args.get("product", "").strip()
    min_confidence = request.args.get("min_confidence", default=0.0, type=float)
    min_lift = request.args.get("min_lift", default=0.0, type=float)
    sort_by = request.args.get("sort_by", "lift")
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 500))

    rules = filter_rules(
        RULES,
        product=product,
        min_confidence=min_confidence,
        min_lift=min_lift,
        sort_by=sort_by,
        limit=limit,
    )
    payload = [
        {
            "antecedents": sorted(rule.antecedents),
            "consequents": sorted(rule.consequents),
            "support": round(float(rule.support), 4),
            "confidence": round(float(rule.confidence), 4),
            "lift": round(float(rule.lift), 2),
        }
        for rule in rules.itertuples()
    ]
    return jsonify({"rules": payload, "count": len(payload)})


# ----------------------------------------------------------------------
# Generated plots (static gallery)
# ----------------------------------------------------------------------
@app.route("/plots/<path:filename>")
def plots(filename):
    return send_from_directory(PLOTS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
