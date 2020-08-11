import typing as t
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from statistics import mean

from tabulate import tabulate


@dataclass
class Measures:
    """
    Data type for binary classification scores scores
    :ivar tp: A number of true positives
    :ivar fp: A number of false positives
    :ivar tn: A number of true negatives
    :ivar fn: A number of false negatives
    """
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    def __add__(self, other):
        tp = self.tp + other.tp
        fp = self.fp + other.fp
        tn = self.tn + other.tn
        fn = self.fn + other.fn
        return Measures(tp=tp, fp=fp, tn=tn, fn=fn)

    def __iadd__(self, other):
        self.tp += other.tp
        self.fp += other.fp
        self.tn += other.tn
        self.fn += other.fn
        return self

    def precision(self):
        """Compute Precision score."""
        try:
            return self.tp / (self.tp + self.fp)
        except ZeroDivisionError:
            return 0.0

    def recall(self):
        """Compute Recall score."""
        try:
            return self.tp / (self.tp + self.fn)
        except ZeroDivisionError:
            return 0.0

    def f_score(self, beta=1):
        """Compute F score given a custom beta"""
        if beta <= 0:
            raise ValueError("beta must be >= 0")
        prec = self.precision()
        rec = self.recall()
        num = (1 + beta ** 2) * (prec * rec)
        den = beta ** 2 * (prec + rec)
        try:
            return num / den
        except ZeroDivisionError:
            return 0.0

    def specificity(self):
        """Compute Specificity score."""
        try:
            return self.tn / (self.fp + self.tn)
        except ZeroDivisionError:
            return 0.0

    def sensitivity(self):
        """Compute Sensitivity score."""
        return self.recall()

    def auc(self):
        """Compute AUC score."""
        return (self.sensitivity() + self.specificity()) / 2

    def accuracy(self):
        try:
            return (self.tp + self.tn) / (self.tp + self.tn + self.fp + self.fn)
        except ZeroDivisionError:
            return 0.0


MeasuresDict = t.DefaultDict[str, Measures]


def merge_measures_dict(a: MeasuresDict, b: MeasuresDict) -> MeasuresDict:
    a = deepcopy(a)
    for k, v in b.items():
        a[k] += v
    return a


def format_results(measures_dict: MeasuresDict, num_dec=3, table_format='plain'):
    """
    Runs calculations on Measures objects and returns a printable table (but does not print it)
    :param measures_dict: A dictionary mapping tags (str) to Measures
    :param num_dec: number of decimal places to round to
    :param table_format: a tabulate module table format (see tabulate on PyPI)
    :return: a string of tabular data
    """
    # Alphabetize the dictionary
    measures_dict = OrderedDict(sorted(measures_dict.items()))

    table = [['Tag', 'Prec', 'Rec', 'F1']]

    for tag, m in measures_dict.items():
        table.append([
            tag,
            m.precision(),
            m.recall(),
            m.f_score()
        ])

    table.append([
        'system (macro)',
        mean(m.precision() for m in measures_dict.values()),
        mean(m.recall() for m in measures_dict.values()),
        mean(m.f_score() for m in measures_dict.values())
    ])

    combined_measures = sum(measures_dict.values(), Measures())

    table.append([
        'system (micro)',
        combined_measures.precision(),
        combined_measures.recall(),
        combined_measures.f_score()
    ])

    return tabulate(table, headers='firstrow', tablefmt=table_format, floatfmt=f".{num_dec}f")
