"""
Inter-dataset agreement calculator for entity annotations
This module calculates precision, recall, and F1 scores given two parallel datasets with a strict or lenient setting.
The strict setting will only count true positives from the predicted data if they have an exact match, span for span,
with the same label in the gold dataset. Lenient results count at most one true positive per named entity in the gold
dataset, so if more than one entity in the predicted data is a lenient match to a given entity in the gold data, only
the first match counts towards the true positive score. However, subsequent lenient matches to a gold entity that has
already been paired will not count as false positives.
"""

import argparse
from copy import deepcopy
from itertools import product

import pandas as pd

from bratlib.calculators import _utils
from bratlib.data import BratDataset, BratFile
from bratlib.data.extensions.annotation_types import ContigEntity


def _ent_strict_equals(a: ContigEntity, b: ContigEntity) -> bool:
    return a.tag == b.tag and ((a.end > b.start and a.start < b.end) or (a.start < b.end and b.start < a.end))


def measure_ann_file(ann_1: BratFile, ann_2: BratFile, mode='strict') -> pd.DataFrame:
    """
    Calculates tag level measurements for two parallel ann files; it does not score them
    :param ann_1: path to the gold ann file
    :param ann_2: path to the system ann file
    :param mode: strict or lenient
    :return: a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn')
    """
    if mode not in _utils.MODES:
        raise ValueError("mode must be 'strict' or 'lenient'")

    gold_ents = list(deepcopy(ann_1.entities))
    system_ents = list(deepcopy(ann_2.entities))

    for e in (gold_ents + system_ents):
        e.__class__ = ContigEntity

    unmatched_gold = set(gold_ents)
    unmatched_system = set(system_ents)

    index = pd.Index({e.tag for e in unmatched_gold | unmatched_system}, name='tag').sort_values()

    if mode == 'strict':
        return (
            pd.concat(
                {
                    'tp': pd.Series(e.tag for e in unmatched_gold & unmatched_system).value_counts(),
                    'fp': pd.Series(e.tag for e in unmatched_system - unmatched_gold).value_counts(),
                    'tn': pd.Series(),
                    'fn': pd.Series(e.tag for e in unmatched_gold - unmatched_system).value_counts()
                },
                axis=1
            )
            .reindex(index)
            .fillna(0)
            .astype(int)
        )

    table = pd.DataFrame(columns=['tp', 'fp', 'tn', 'fn'], index=index).fillna(0)

    for s, g in product(system_ents, gold_ents):
        if not _ent_strict_equals(s, g):
            continue

        if s not in unmatched_system:
            # Don't do anything with system predictions that have already been paired
            continue

        if g in unmatched_gold:
            # Each gold entity can only be matched to one prediction and
            # can only count towards the true positive score once
            unmatched_gold.remove(g)
            unmatched_system.remove(s)
            table.loc[s.tag, 'tp'] += 1
        else:
            # The entity has been matched to a gold entity, but we have
            # already gotten the one true positive match allowed for each gold entity;
            # therefore we say that the predicted entity is now matched
            unmatched_system.remove(s)

    # All predictions that don't match any gold entity count one towards the false positive score
    table['fp'] += pd.Series(e.tag for e in unmatched_system).value_counts()

    # The number of false negatives is the number of gold entities for a tag minus the number that got
    # counted as true positives
    table['fn'] += pd.Series(e.tag for e in unmatched_gold).value_counts()

    return table.fillna(0).astype(int)


def measure_dataset(gold_dataset: BratDataset, system_dataset: BratDataset, mode='strict') -> pd.DataFrame:
    """
    Measures the true positive, false positive, and false negative counts for a directory of predictions
    :param gold_dataset: The gold version of the predicted dataset
    :param system_dataset: The predicted dataset
    :param mode: 'strict' or 'lenient'
    :return: a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn')
    """
    if mode not in _utils.MODES:
        raise ValueError("mode must be 'strict' or 'lenient'")

    return _utils.merge_dataset_dataframes(gold_dataset, system_dataset, measure_ann_file, mode)


def main():
    parser = argparse.ArgumentParser(description='Inter-dataset agreement calculator for entities')
    parser.add_argument('gold_directory', help='First data folder path (gold)')
    parser.add_argument('system_directory', help='Second data folder path (system)')
    parser.add_argument('-m', '--mode', default='strict', help='strict or lenient (defaults to strict)')
    parser.add_argument('-d', '--decimal', type=int, default=3, help='number of decimal places to round to')
    args = parser.parse_args()

    gold_dataset = BratDataset.from_directory(args.gold_directory)
    system_dataset = BratDataset.from_directory(args.system_directory)

    measures = measure_dataset(gold_dataset, system_dataset, args.mode)
    scores = _utils.calculate_scores(measures, macro=True, micro=True)
    print(scores.to_csv(float_format=f'%.{args.decimal}f'))


if __name__ == '__main__':
    main()
