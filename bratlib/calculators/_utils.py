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


def merge_dataset_dataframes(
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


def calculate_scores(counts: pd.DataFrame, *, macro=False, micro=False) -> pd.DataFrame:
    """
    Given a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn'),
    return a new DataFrame of 'tag' -> ('precision', 'recall', 'f1').

    :param counts: pd.DataFrame, see above
    :param macro: bool to include system macro scores at index `(macro)`, defaults to False
    :param micro: bool to include system micro scores at index `(micro)`, defaults to False
    """
    precision = counts.tp / (counts.tp + counts.fp)
    recall = counts.tp / (counts.tp + counts.fn)
    f1 = 2 * (precision * recall) / (precision + recall)
    df = pd.concat([precision, recall, f1], axis=1)
    df.columns = ['precision', 'recall', 'f1']

    if macro:
        df.loc['(macro)'] = df.mean(axis=0)

    if micro:
        sums = counts.sum(axis=0)
        precision = sums.tp / (sums.tp + sums.fp)
        recall = sums.tp / (sums.tp + sums.fn)
        df.loc['(micro)'] = [precision, recall, 2 * (precision * recall) / (precision + recall)]

    return df
