import argparse
from collections import defaultdict
from copy import deepcopy
from itertools import product

from bratlib.calculators import Measures, MeasuresDict, format_results
from bratlib.calculators.entity_agreement import ent_equals
from bratlib.data import BratFile
from bratlib.data.extensions.file import StatsDataset
from bratlib.data.extensions.instance import ContigEntity
from bratlib.tools.iteration import zip_datasets


def measure_ann_file(ann_1: BratFile, ann_2: BratFile) -> MeasuresDict:
    """
    Calculates tag level measurements for two parallel ann files; it does not score them
    :param ann_1: path to the gold ann file
    :param ann_2: path to the system ann file
    :return: a dictionary mapping tags (str) to measurements (Measures)
    """
    gold_rels = list(deepcopy(ann_1.relations))
    system_rels = list(deepcopy(ann_2.relations))

    for r in (gold_rels + system_rels):
        r.arg1.__class__ = ContigEntity
        r.arg2.__class__ = ContigEntity

    measures = defaultdict(Measures)

    gold_are_matched = {r: False for r in gold_rels}
    sys_are_matched = {r: False for r in system_rels}

    for g, s in product(gold_rels, system_rels):

        if not (ent_equals(g.arg1, s.arg1, mode='strict') and ent_equals(g.arg2, s.arg2, mode='strict')):
            continue

        if g.relation != s.relation:
            continue

        if not gold_are_matched[g]:
            measures[g.relation].tp += 1

        gold_are_matched[g] = sys_are_matched[s] = True

    for r, b in gold_are_matched.items():
        # Every gold relationship that doesn't have a match means there's a missing match--a false negative
        measures[r.relation].fn += 1 if not b else 0

    for r, b in sys_are_matched.items():
        # Every system relationship that doesn't have a match was incorrect--a false positive
        measures[r.relation].fp += 1 if not b else 0

    return measures


def measure_dataset(gold_dataset: StatsDataset, system_dataset: StatsDataset) -> MeasuresDict:
    """
    Measures the true positive, false positive, and false negative counts for a directory of predictions
    :param gold_dataset: The gold version of the predicted dataset
    :param system_dataset: The predicted dataset
    :return: a dictionary of tag-level Measures objects
    """

    all_file_measures = [measure_ann_file(gold, system)
                         for gold, system in zip_datasets(gold_dataset, system_dataset)]

    # Combine the Measures objects for each tag from each file together
    return sum(all_file_measures, Measures())


def main():
    parser = argparse.ArgumentParser(description='Inter-dataset agreement calculator for relations')
    parser.add_argument('gold_directory', help='First data folder path (gold)')
    parser.add_argument('system_directory', help='Second data folder path (system)')
    parser.add_argument('-f', '--format', default='plain', help='format to print the table (options include grid, github, and latex)')
    parser.add_argument('-d', '--decimal', type=int, default=3, help='number of decimal places to round to')
    args = parser.parse_args()

    gold_dataset = StatsDataset.from_directory(args.gold_directory)
    system_dataset = StatsDataset.from_directory(args.system_directory)

    result = measure_dataset(gold_dataset, system_dataset)
    output = format_results(result, num_dec=args.decimal, table_format=args.format)
    print(output)


if __name__ == '__main__':
    main()
