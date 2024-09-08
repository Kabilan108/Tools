"""
This module contains functions for data preprocessing
"""

# Imports
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold
from rich import print

import pandas as pd
import numpy as np
import re


def drop_high_corr(data, thresh=0.95, method="pearson"):
    """
    Remove features with correaltions above a threshold from a data frame.

    Parameters
    ----------
    `data` : pd.DataFrame
        Original data frame
    `thresh` : float, optional
        Correlation threshold, by default 0.95
    `method` : str, optional
        Either 'pearson' or 'spearman', by default 'pearson'

    Returns
    -------
    pd.DataFrame
        Data frame without highly correlated features
    dict
        Keys = features still in data frame
        Values = list of highly correlated features
    """

    assert 0 < thresh <= 1, "thresh must be between 0 and 1"
    assert method in ["pearson", "spearman"], "Only 'pearson' or 'spearman' allowed"

    # Compute correlations
    corr = data.corr(method).abs()
    corr = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

    # Create dictionary of features to drop
    dropped = dict()
    for col in corr.columns:
        I = corr[col] > thresh
        if any(I):
            dropped[col] = corr.columns[I].tolist()

    dropping = [x for sub in dropped.values() for x in sub if x not in dropped]

    return data.drop(dropping, axis=1), dropped


def drop_low_variance(data, thresh=0.0, na_replacement=-999):
    """
    Remove low-variance features from a data frame

    Parameters
    ----------
    `data` : pd.DataFrame
        Original data frame
    `thresh` : float, optional
        Variance threshold, by default 0.0
    `na_replacement` : int, optional
        Replacement value for NAs, by default -999

    Returns
    -------
    pd.DataFrame
        Data frame without low-variance features
    """

    df = data.copy()
    selector = VarianceThreshold(thresh)
    selector.fit(df.fillna(na_replacement))

    return df.loc[:, selector.get_support(indices=False)]


def _printif(cond, *args, **kwargs):
    """
    Print if cond is true
    """

    if cond:
        print(*args, **kwargs)


def _intersperse(array, item):
    """
    Insert item between each item in an array
    """

    result = [item] * (len(array) * 2 - 1)
    result[0::2] = array
    return result


def clean_data(
    data,
    metacols,
    dropna=False,
    drop_low_var=None,
    corr_thresh=None,
    corr_method="pearson",
    intens_norm=False,
    intens_rgx=r"Intensity",
    num_objs="number of objects",
    verbose=False,
):
    """
    Perform preprocessing steps on a high-content imaging data

    Parameters
    ----------
    `data` : pd.DataFrame
        Original data frame
    `metacols` : list
        List of non-numeric columns in data frame
    `dropna` : bool, optional
        Drop NA-only columns and any rows with NAs, by default False
    `drop_low_var` : float, optional
        Threshold for dropping low variance features, by default None
    `corr_thresh` : float, optional
        Threshold for dropping highly correlated features, by default None
    `corr_method` : str, optional
        Correlation method, by default 'spearman'
    `intens_norm` : bool, optional
        Should intensity-based features be normalized, by default False
    `intens_rgx` : str, optional
        Regular expression for identifying intensity based features,
        by default `r'Intensity'`
    `num_objs` : str, optional
        Feature definining object counts, by default 'number of objects'
    `verbose` : bool, optional
        Should a log of processing steps be returned, by default False

    Returns
    -------
    pd.DataFrame
        Preprocessed data
    list
        Only if `verbose == True`, preprocessing log
    """

    for col in metacols:
        assert col in data.columns, "Items in metacols must be columns of data"
    if intens_norm:
        assert num_objs in data.columns, "num_objs must be aa column of data"

    # Create log
    if verbose:
        LOG = [f"Original data shape: {data.shape}"]
    else:
        LOG = None

    # Store non-numeric data in index
    data = data.set_index(metacols)

    # Track dropped features
    og_features = set(data.columns)
    dropped = dict()

    if dropna:
        data = data.dropna(axis=1, how="all").dropna(  # NA-only columns
            axis=0, how="any"
        )  # Rows with NAs
        dropped["dropna"] = list(og_features.difference(data.columns))

        if verbose:
            LOG.append(f"After removing missing data, data shape: {data.shape}")

    if drop_low_var is not None:
        data = drop_low_variance(data, thresh=drop_low_var)
        dropped["low_var"] = list(og_features.difference(data.columns))

        if verbose:
            LOG.append(
                f"After removing low-variance features, data shape: {data.shape}"
            )

    if corr_thresh is not None:
        data, dropped["high_corr"] = drop_high_corr(data, corr_thresh, corr_method)

        if verbose:
            LOG.append(
                f"After removing highly correlated features, data.shape: {data.shape}"
            )

    if intens_norm:
        intens_features = [x for x in data.columns if re.search(intens_rgx, x)]
        data[intens_features] = data[intens_features].div(data[num_objs], axis=0)

        if verbose:
            LOG.append(f"Intensity-based features were normalized by '{num_objs}'")

    # Store additional metadata
    data = data.reset_index()
    data.attrs["metacols"] = metacols
    data.attrs["features"] = list(set(data.columns).difference(metacols))

    return data, dropped, LOG


def normalize(df, method="minmax"):
    """
    Normalize a data frame

    Parameters
    ----------
    df : pd.DataFrame
        Original data frame
    method : str, optional
        Either 'minmax' or 'z', by default 'minmax'

    Returns
    -------
    pd.DataFrame
        Normalized data frame

    Raises
    ------
    NotImplementedError
        If method isn't 'minmax' or 'z'
    """

    if method == "minmax":
        X = MinMaxScaler().fit_transform(df.values)
    elif method == "z":
        X = StandardScaler().fit_transform(df.values)
    else:
        raise NotImplementedError("Can't do that yet.")

    return pd.DataFrame(X, columns=df.columns, index=df.index)
