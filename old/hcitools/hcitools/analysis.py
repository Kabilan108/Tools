"""
This module contains functions and classes for performing statistical analysis
and machine learning
"""

# Imports
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from umap import UMAP
from rich import print

import pandas as pd
import numpy as np
import re


RANDOMSTATE = 69


def dim_reduction(
    data, method=["pca", "tsne", "umap"], pca_kws=None, tsne_kws=None, umap_kws=None
):
    """
    Perform dimensionality reduction on data

    Parameters
    ----------
    `data` : pd.DataFrame
        Data frame of features. Should only contain numeric columns.
        Metadata can be stored in the index
    `method` : str or list, optional
        Method(s) to use for dimensionality reduction,
        by default ['pca', 'tsne', 'umap']
    `{pca, tsne, umap}_kws` : dict, optional
        Arguments for the estimators, by default None

    Returns
    -------
    pd.DataFrame
        Data frame of low-dimensional projections
    np.array
        Only if 'pca' in method, list of explained variances
    """

    if isinstance(method, str):
        method = [method]
    method = [x.lower() for x in method]
    for m in method:
        assert m in ["pca", "tsne", "umap"], "method must be 'pca', 'tsne' or 'umap'"

    if pca_kws is None:
        pca_kws = dict(n_components=5, random_state=RANDOMSTATE)
    else:
        pca_kws["random_state"] = RANDOMSTATE

    if tsne_kws is None:
        tsne_kws = dict(
            n_components=3,
            perplexity=30.0,
            learning_rate="auto",
            init="random",
            random_state=RANDOMSTATE,
        )
    else:
        tsne_kws["random_state"] = RANDOMSTATE

    if umap_kws is None:
        umap_kws = dict(
            n_components=3,
            init="random",
            n_neighbors=20,
            min_dist=0.2,
            random_state=RANDOMSTATE,
        )
    else:
        umap_kws["random_state"] = RANDOMSTATE

    # Initialize estimators
    estimators = dict()
    for m in method:
        if m == "pca":
            estimators[m] = PCA(**pca_kws).fit(data)
        elif m == "tsne":
            estimators[m] = TSNE(**tsne_kws)
        elif m == "umap":
            estimators[m] = UMAP(**umap_kws)
        else:
            raise ValueError("How did you get here?")

    # Compute projections
    proj = []
    expvar = None
    for m, est in estimators.items():
        if m == "pca":
            proj.append(est.transform(data))
            expvar = est.explained_variance_ratio_ * 100
        else:
            proj.append(est.fit_transform(data))
    proj = np.concatenate(proj, axis=1)

    # Create column names for output data frame
    cols = []
    for m in method:
        n = estimators[m].n_components + 1
        cols.append([f"{m.upper()} {i}" for i in range(1, n)])
    cols = [x for sub in cols for x in sub]

    # Create data frame of projections
    proj = pd.DataFrame(proj, columns=cols, index=data.index).melt(ignore_index=False)
    proj["component"] = (
        proj["variable"].apply(lambda x: re.search(r"\d+", x)[0]).astype(int)
    )
    proj["variable"] = proj["variable"].apply(lambda x: re.search(r"^\w*", x)[0])
    proj = proj.pivot_table(
        values="value", columns="component", index=list(data.index.names) + ["variable"]
    ).reset_index()
    proj.columns = proj.columns.astype(str)

    return proj, expvar
