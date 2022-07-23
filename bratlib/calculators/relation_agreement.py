import argparse
from copy import deepcopy
from itertools import product

import pandas as pd

from bratlib.calculators import _utils
from bratlib.data import BratDataset, BratFile
from bratlib.data.extensions.annotation_types import ContigEntity


def _ent_equals(a: ContigEntity, b: ContigEntity):
    return (a.tag, a.start, a.end) == (b.tag, b.start, b.end)


def measure_ann_file(ann_1: BratFile, ann_2: BratFile) -> _utils.CountsDataFrame:
    """
    Calculates tag level measurements for two parallel ann files; it does not score them
    :param ann_1: path to the gold ann file
    :param ann_2: path to the system ann file
    :return: a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn')
    """
    gold_rels = list(deepcopy(ann_1.relations))
    system_rels = list(deepcopy(ann_2.relations))

    for r in (gold_rels + system_rels):
        r.arg1.__class__ = ContigEntity
        r.arg2.__class__ = ContigEntity

    table = pd.DataFrame(
        columns=['tp', 'fp', 'tn', 'fn'],
        index=pd.Index({r.relation for r in gold_rels} | {r.relation for r in system_rels}, name='tag').sort_values()
    ).fillna(0)

    gold_are_matched = {r: False for r in gold_rels}
    sys_are_matched = {r: False for r in system_rels}

    for g, s in product(gold_rels, system_rels):

        if not (_ent_equals(g.arg1, s.arg1) and _ent_equals(g.arg2, s.arg2)):
            continue

        if g.relation != s.relation:
            continue

        if not gold_are_matched[g]:
            table.loc[g.relation, 'tp'] += 1

        gold_are_matched[g] = sys_are_matched[s] = True

    # Every gold relationship that doesn't have a match means there's a missing match--a false negative
    table['fn'] += pd.Series(r.relation for r, b in gold_are_matched.items() if not b).value_counts()

    # Every system relationship that doesn't have a match was incorrect--a false positive
    table['fp'] += pd.Series(r.relation for r, b in sys_are_matched.items() if not b).value_counts()

    return table.fillna(0).astype(int)


def measure_dataset(gold_dataset: BratDataset, system_dataset: BratDataset) -> _utils.CountsDataFrame:
    """
    Measures the true positive, false positive, and false negative counts for a directory of predictions
    :param gold_dataset: The gold version of the predicted dataset
    :param system_dataset: The predicted dataset
    :return: a DataFrame of 'tag' -> ('tp', 'fp', 'tn', 'fn')
    """
    return _utils.merge_dataset_dataframes(gold_dataset, system_dataset, measure_ann_file)


def main():
    parser = argparse.ArgumentParser(description='Inter-dataset agreement calculator for relations')
    parser.add_argument('gold_directory', help='First data folder path (gold)')
    parser.add_argument('system_directory', help='Second data folder path (system)')
    parser.add_argument('-d', '--decimal', type=int, default=3, help='number of decimal places to round to')
    args = parser.parse_args()

    gold_dataset = BratDataset.from_directory(args.gold_directory)
    system_dataset = BratDataset.from_directory(args.system_directory)

    measures = measure_dataset(gold_dataset, system_dataset)
    scores = _utils.calculate_scores(measures, macro=True, micro=True)
    print(scores.to_csv(float_format=f'%.{args.decimal}f'))


if __name__ == '__main__':
    main()
