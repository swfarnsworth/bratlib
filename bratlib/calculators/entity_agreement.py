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
from collections import defaultdict
from copy import deepcopy
from itertools import product

from bratlib.calculators import Measures, MeasuresDict, format_results, merge_measures_dict
from bratlib.data import BratFile
from bratlib.data.extensions.file import StatsDataset
from bratlib.data.extensions.instance import ContigEntity
from bratlib.tools.iteration import zip_datasets


def _ent_equals(a: ContigEntity, b: ContigEntity, mode='strict') -> bool:
    if mode == 'lenient':
        return a.tag == b.tag and ((a.end > b.start and a.start < b.end) or (a.start < b.end and b.start < a.end))
    return (a.tag, a.spans) == (b.tag, b.spans)


def measure_ann_file(ann_1: BratFile, ann_2: BratFile, mode='strict') -> MeasuresDict:
    """
    Calculates tag level measurements for two parallel ann files; it does not score them
    :param ann_1: path to the gold ann file
    :param ann_2: path to the system ann file
    :param mode: strict or lenient
    :return: a dictionary mapping tags (str) to measurements (Measures)
    """
    if mode not in ('strict', 'lenient'):
        raise ValueError("mode must be 'strict' or 'lenient'")

    gold_ents = list(deepcopy(ann_1.entities))
    system_ents = list(deepcopy(ann_2.entities))

    for e in (gold_ents + system_ents):
        e.__class__ = ContigEntity

    unmatched_gold = gold_ents.copy()
    unmatched_system = system_ents.copy()
    measures = defaultdict(Measures)

    for s, g in product(system_ents, gold_ents):
        if _ent_equals(s, g, mode=mode):
            if s not in unmatched_system:
                # Don't do anything with system predictions that have already been paired
                continue

            if g in unmatched_gold:
                # Each gold entity can only be matched to one prediction and
                # can only count towards the true positive score once
                unmatched_gold.remove(g)
                unmatched_system.remove(s)
                measures[s.tag].tp += 1
            else:
                # The entity has been matched to a gold entity, but we have
                # already gotten the one true positive match allowed for each gold entity;
                # therefore we say that the predicted entity is now matched
                unmatched_system.remove(s)

    for s in unmatched_system:
        # All predictions that don't match any gold entity count one towards the false positive score
        measures[s.tag].fp += 1

    for tag, measure in measures.items():
        # The number of false negatives is the number of gold entities for a tag minus the number that got
        # counted as true positives
        measures[tag].fn = [e.tag == tag for e in gold_ents].count(True) - measure.tp

    return measures


def measure_dataset(gold_dataset: StatsDataset, system_dataset: StatsDataset, mode='strict') -> MeasuresDict:
    """
    Measures the true positive, false positive, and false negative counts for a directory of predictions
    :param gold_dataset: The gold version of the predicted dataset
    :param system_dataset: The predicted dataset
    :param mode: 'strict' or 'lenient'
    :return: a dictionary of tag-level Measures objects
    """
    if mode not in ['strict', 'lenient']:
        raise ValueError("mode must be 'strict' or 'lenient'")

    all_file_measures = []
    tag_measures = defaultdict(Measures)

    for gold, system in zip_datasets(gold_dataset, system_dataset):
        all_file_measures.append(measure_ann_file(gold, system, mode=mode))

    # Combine the Measures objects for each tag from each file together
    for file_measures in all_file_measures:
        tag_measures = merge_measures_dict(tag_measures, file_measures)

    return tag_measures


def main():
    parser = argparse.ArgumentParser(description='Inter-dataset agreement calculator')
    parser.add_argument('gold_directory', help='First data folder path (gold)')
    parser.add_argument('system_directory', help='Second data folder path (system)')
    parser.add_argument('-m', '--mode', default='strict', help='strict or lenient (defaults to strict)')
    parser.add_argument('-f', '--format', default='plain', help='format to print the table (options include grid, github, and latex)')
    parser.add_argument('-d', '--decimal', type=int, default=3, help='number of decimal places to round to')
    args = parser.parse_args()

    gold_dataset = StatsDataset.from_directory(args.gold_directory)
    system_dataset = StatsDataset.from_directory(args.system_directory)

    result = measure_dataset(gold_dataset, system_dataset, args.mode)
    output = format_results(result, num_dec=args.decimal, table_format=args.format)
    print(output)


if __name__ == '__main__':
    main()