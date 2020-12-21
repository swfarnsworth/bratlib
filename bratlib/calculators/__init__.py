from dataclasses import dataclass

import pandas as pd


@dataclass
class Measures:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0


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
