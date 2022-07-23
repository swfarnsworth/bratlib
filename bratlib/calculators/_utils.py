import typing as t
from functools import reduce

import pandas as pd

from bratlib import data as bd
from bratlib.tools.iteration import zip_datasets

NONE = 'NONE'
MODES = ('strict', 'lenient')

CountsDataFrame = t.NewType('CountsDataFrame', pd.DataFrame)
ScoresDataFrame = t.NewType('ScoresDataFrame', pd.DataFrame)
ConfusionMatrixDataFrame = t.NewType('ConfusionMatrixDataFrame', pd.DataFrame)


def merge_dataset_dataframes(
    gold: bd.BratDataset,
    system: bd.BratDataset,
    function: t.Callable[[bd.BratFile, bd.BratFile], t.Union[CountsDataFrame, ConfusionMatrixDataFrame]],
    *args, **kwargs
) -> t.Union[CountsDataFrame, ConfusionMatrixDataFrame]:
    """
    For any calculator function that ultimately aggregates dataframes from file-level comparisons, this function
    performs that aggregation.
    """
    return reduce(
        lambda x, y: x.add(y, fill_value=0).fillna(0),
        (function(gold, system, *args, **kwargs)
         for gold, system in zip_datasets(gold, system))
    )


def calculate_scores(counts: CountsDataFrame, *, macro=False, micro=False) -> ScoresDataFrame:
    """
    Given a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn'),
    return a new DataFrame of 'tag' -> ('precision', 'recall', 'f1').

    :param counts: pd.DataFrame, see above
    :param macro: bool to include system macro scores at index `(macro)`, defaults to False
    :param micro: bool to include system micro scores at index `(micro)`, defaults to False
    """
    tp, fp, fn = counts['tp'], counts['fp'], counts['fn']
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)

    # noinspection PyTypeChecker
    df: ScoresDataFrame = pd.concat(
        {
            'precision': precision,
            'recall': recall,
            'f1': 2 * (precision * recall) / (precision + recall)
        }, axis=1
    )

    if macro:
        df.loc['(macro)'] = df.mean(axis=0)

    if micro:
        sums = counts.sum(axis=0)
        precision = sums['tp'] / (sums['tp'] + sums['fp'])
        recall = sums['tp'] / (sums['tp'] + sums['fn'])
        df.loc['(micro)'] = [precision, recall, 2 * (precision * recall) / (precision + recall)]

    return df


def matrix_dataframe(labels: t.Iterable[str]) -> ConfusionMatrixDataFrame:
    index = pd.Index(labels).drop_duplicates().sort_values()
    return (
        pd.DataFrame(
            index=index.rename('actual'),
            columns=index.rename('predicted')
        )
        .fillna(0)
    )
