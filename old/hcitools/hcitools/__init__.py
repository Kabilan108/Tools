"""
.. include:: ../README.md

# Examples
.. include:: ../docs/heatmaps.md
.. include:: ../docs/clustering.md
"""

import os

__all__ = ["preprocess", "analysis", "plot", "datasets"]

location = os.path.dirname(os.path.realpath(__file__))


class datasets:
    """
    Class for loading built-in datasets
    """

    _avail = {
        "caer": os.path.join(location, "datasets", "caer-timecourse.tsv"),
        "covid": os.path.join(location, "datasets", "covid-cohort.tsv"),
        "ros-mito": os.path.join(location, "datasets", "ros-mito-timecourse.tsv"),
    }

    def list_datasets():
        """
        List available built-in datasets
        """

        print("Available Datasets:", *datasets._avail.keys(), sep="\n")

    def load_dataset(dataset):
        """
        Load a built-in dataset

        Parameters
        ----------
        `dataset` : str
            One of 'covid', 'caer' or 'ros-mito'

        Returns
        -------
        pd.DataFrame
            Desired dataset
        """

        assert dataset in [
            "caer",
            "covid",
            "ros-mito",
        ], "Unknown dataset. See datasets.list_datasets()"
        from pandas import read_csv

        return read_csv(datasets._avail[dataset], sep="\t")
