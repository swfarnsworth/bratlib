import typing as t
from dataclasses import dataclass
from functools import reduce

import pandas as pd

from bratlib import data as bd
from bratlib.tools.iteration import zip_datasets


@dataclass
class Measures:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0


def _merge_dataset_dataframes(
        gold: bd.BratDataset,
        system: bd.BratDataset,
        function: t.Callable[[bd.BratFile, bd.BratFile], pd.DataFrame],
        *args, **kwargs
):
    """
    For any calculator function that ultimately aggregates dataframes from file-level comparisons, this function
    performs that aggregation.
    """
    return reduce(
        lambda x, y: x.add(y, fill_value=0),
        (function(gold, system, *args, **kwargs)
         for gold, system in zip_datasets(gold, system))
    )


def calculate_scores(counts: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn'),
    return a new DataFrame of 'tag' -> ('precision', 'recall', 'f1').
    """
    precision = counts.tp / (counts.tp + counts.fp)
    recall = counts.tp / (counts.tp + counts.fn)
    f1 = 2 * (precision * recall) / (precision + recall)
    df = pd.concat([precision, recall, f1], axis=1)
    df.columns = ['precision', 'recall', 'f1']
    return df
