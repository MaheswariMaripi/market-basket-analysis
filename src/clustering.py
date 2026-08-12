"""
Product segmentation (clustering) module.

Responsibilities
----------------
* Represent every product by its *co-occurrence vector*: how often it is
  bought together with every other product (``encoded.T @ encoded``).
* Cluster those vectors with K-means so that products which tend to appear
  in the same baskets end up in the same data-driven segment.
* Choose the number of clusters with the silhouette score (falling back
  to a safe default when the score is weak).
* Persist the assignment (``outputs/results/product_clusters.csv``) and a
  PCA scatter plot (``outputs/plots/product_clusters.png``).

Why product clustering?
-----------------------
Association rules answer "what goes with what?". Clustering answers a
broader question: "which products naturally form groups?". The groups are
learned from the data itself, so they can reveal categories a manual
taxonomy would miss (e.g. "organic snack" or "weekend party" segments).

scikit-learn is imported lazily inside the functions so the web app keeps
working even on machines where it is not installed.
"""

from pathlib import Path

import pandas as pd

from src import PLOTS_DIR, RESULTS_DIR


def co_occurrence_matrix(encoded_df):
    """Pairwise co-occurrence counts between products.

    Given a binary matrix where rows are transactions and columns are
    products, the entry ``[i, j]`` of ``encoded.T @ encoded`` is the number
    of baskets that contain both product *i* and product *j*.

    Returns a symmetric DataFrame indexed and labelled by product name.
    """
    matrix = encoded_df.T @ encoded_df
    return matrix.astype(int)


def _eligible_products(encoded_df, min_frequency=5):
    """Products bought in at least ``min_frequency`` baskets.

    Rare products produce noisy, near-empty co-occurrence vectors and are
    excluded from the segmentation so they do not distort the clusters.
    """
    frequencies = encoded_df.sum(axis=0)
    return sorted(frequencies[frequencies >= min_frequency].index.tolist())


def _pick_k(vectors, k_range):
    """Best number of clusters by silhouette score (>=2 and <= n-1)."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    best_k, best_score = None, -1.0
    upper = min(len(vectors) - 1, max(k_range))
    for k in range(max(2, min(k_range)), upper + 1):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(vectors)
        score = silhouette_score(vectors, labels)
        if score > best_score:
            best_k, best_score = k, score

    # A weak silhouette means the structure is soft; a conservative 2-segment
    # split is still informative and always safe.
    return best_k or 2, best_score


def cluster_products(encoded_df, min_frequency=5, k_range=(2, 8),
                     random_state=42):
    """Segment products by their co-occurrence pattern using K-means.

    Parameters
    ----------
    encoded_df : pd.DataFrame
        Binary transaction matrix from ``preprocessing.one_hot_encode``.
    min_frequency : int
        Products appearing in fewer baskets than this are skipped.
    k_range : tuple[int, int]
        Inclusive range of cluster counts to evaluate.

    Returns
    -------
    tuple[DataFrame, float]
        A DataFrame with columns ``product``, ``frequency`` and ``cluster``
        (one row per eligible product) plus the chosen silhouette score.
        An empty DataFrame is returned when there is nothing to cluster.
    """
    if encoded_df.empty or encoded_df.shape[1] < 2:
        return pd.DataFrame(columns=["product", "frequency", "cluster"]), 0.0

    products = _eligible_products(encoded_df, min_frequency=min_frequency)
    if len(products) < 2:
        return pd.DataFrame(columns=["product", "frequency", "cluster"]), 0.0

    vectors = co_occurrence_matrix(encoded_df).loc[products, products].values.astype(float)

    # Standardise each column so high-volume products do not dominate the
    # geometry; this keeps the clustering pattern-driven.
    from sklearn.preprocessing import StandardScaler
    vectors = StandardScaler().fit_transform(vectors)

    from sklearn.cluster import KMeans
    k, silhouette = _pick_k(vectors, k_range)

    labels = KMeans(n_clusters=k, n_init=10,
                    random_state=random_state).fit_predict(vectors)

    frequencies = encoded_df[products].sum(axis=0)
    result = pd.DataFrame({
        "product": products,
        "frequency": frequencies.values.astype(int),
        "cluster": labels,
    })
    result = result.sort_values(["cluster", "frequency"],
                                ascending=[True, False]).reset_index(drop=True)
    return result, float(silhouette)


def summarize_clusters(assignments, top_n=5):
    """Per-cluster summary: size and the most frequent products."""
    if assignments.empty:
        return {}

    summary = {}
    for cluster_id, group in assignments.groupby("cluster"):
        summary[int(cluster_id)] = {
            "size": int(len(group)),
            "top_products": group.head(top_n)["product"].tolist(),
            "share": round(float(len(group) / len(assignments)), 3),
        }
    return summary


def run_clustering(encoded_df, transactions=None, min_frequency=5,
                   results_dir=RESULTS_DIR, plots_dir=PLOTS_DIR):
    """Run the full segmentation pipeline and persist its outputs.

    Writes ``product_clusters.csv`` and ``product_clusters.png`` and returns
    a dictionary of summary numbers for reports and the console output of
    ``main.py``.
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    assignments, silhouette = cluster_products(encoded_df,
                                               min_frequency=min_frequency)
    if assignments.empty:
        return {"n_clusters": 0, "n_products": 0, "silhouette": 0.0,
                "clusters": {}, "paths": {}}

    products = assignments["product"].tolist()
    matrix = co_occurrence_matrix(encoded_df).loc[products, products].values.astype(float)
    from sklearn.preprocessing import StandardScaler
    matrix = StandardScaler().fit_transform(matrix)

    assignments.to_csv(results_dir / "product_clusters.csv", index=False)
    plot_path = _plot_pca_scatter(matrix, assignments, plots_dir)

    summary = summarize_clusters(assignments)
    return {
        "n_clusters": len(summary),
        "n_products": int(len(assignments)),
        "silhouette": silhouette,
        "clusters": summary,
        "paths": {
            "clusters_csv": str(results_dir / "product_clusters.csv"),
            "clusters_plot": str(plot_path),
        },
    }


def _plot_pca_scatter(matrix, assignments, plots_dir):
    """Render the PCA scatter using the real standardised vectors."""
    from matplotlib import pyplot as plt
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2, random_state=42)
    points = pca.fit_transform(matrix)

    plt.figure(figsize=(11, 8))
    clusters = sorted(assignments["cluster"].unique())
    cmap = plt.get_cmap("tab10")

    for cluster_id in clusters:
        mask = assignments["cluster"] == cluster_id
        plt.scatter(points[mask, 0], points[mask, 1],
                    c=[cmap(cluster_id % 10)], s=90, alpha=0.85,
                    edgecolors="black", linewidths=0.4,
                    label=f"Segment {cluster_id + 1}")

    idx = {product: i for i, product in enumerate(assignments["product"])}
    for _, row in assignments.head(12).iterrows():
        if row["product"] in idx:
            i = idx[row["product"]]
            plt.annotate(row["product"], (points[i, 0], points[i, 1]),
                         fontsize=8, alpha=0.8,
                         xytext=(4, 4), textcoords="offset points")

    plt.title("Product Segments (K-means on Co-occurrence Patterns)")
    plt.xlabel("Principal component 1")
    plt.ylabel("Principal component 2")
    plt.legend(loc="upper right", title="Cluster")
    plt.tight_layout()

    output_path = plots_dir / "product_clusters.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    if "agg" not in __import__("matplotlib").get_backend().lower():
        plt.show()
    plt.close()
    return output_path


def demo_segment(assignments):
    """Return the largest segment and its headline products."""
    if assignments.empty:
        return None, {}
    largest = int(assignments["cluster"].value_counts().idxmax())
    summary = summarize_clusters(assignments, top_n=5)
    return largest, summary.get(largest, {})
