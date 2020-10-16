import argparse
import typing as t
from collections import Counter
from itertools import product

from tabulate import tabulate

from bratlib import data as bd
from bratlib.tools.iteration import zip_datasets

EntityConfusionMatrix = t.Counter[t.Tuple[str, str]]


def generate_entity_pairs(gold: bd.BratFile, system: bd.BratFile) -> t.Iterable[t.Tuple[str, str]]:
    """
    Generates tuples of tags for which entities of those tags were found to overlap.
    When these pairs are exhausted, it generates tuples for all unmatched entities with 'NONE'.
    The first element of the tuple is gold, the second is system.
    """
    gold_match = {g: False for g in gold.entities}
    sys_match = {s: False for s in system.entities}

    for g, s in product(gold.entities, system.entities):
        if (g.spans[0][0], g.spans[-1][-1]) == (s.spans[0][0], s.spans[-1][-1]):
            gold_match[g] = sys_match[s] = True
            yield (g.tag, s.tag)

    yield from (('NONE', s.tag) for s, b in sys_match.items() if not b)
    yield from ((g.tag, 'NONE') for g, b in gold_match.items() if not b)


def count_file(gold: bd.BratFile, system: bd.BratFile) -> EntityConfusionMatrix:
    """Creates a confusion matrix-like Counter for one file"""
    return Counter(generate_entity_pairs(gold, system))


def count_dataset(gold: bd.BratDataset, system: bd.BratDataset) -> EntityConfusionMatrix:
    """Creates a confusion matrix-like Counter for a dataset"""
    return sum((count_file(g, s) for g, s in zip_datasets(gold, system)), Counter())


def format_results(matrix_data: EntityConfusionMatrix, horizontal=False, red=False) -> str:
    ent_types = sorted(set(list(sum(matrix_data.keys(), ()))))
    joiner = ('\n' if not horizontal else '').join
    table_header = ['*'] + [joiner(e) for e in ent_types]
    table = [table_header]

    for e in ent_types:
        new_row = [e] + [matrix_data[(e, v)] for v in ent_types]
        table.append(new_row)

    result = tabulate(table)
    return result if not red else '\033[1;31;40m' + result + '\033[m'


def main():
    parser = argparse.ArgumentParser(description='Creates a confusion matrix for entities between two datasets')
    parser.add_argument('gold_directory', help='Directory containing the gold ann files')
    parser.add_argument('system_directory', help='Directory containing the system ann files')
    parser.add_argument('-r', '--red', action='store_true', help='Flag to print the results in red')
    parser.add_argument('-hl', '--horizontal', action='store_true', help='Print the entity types in the top row horizontally; this will make the table wider')
    args = parser.parse_args()

    gold_dataset = bd.BratDataset.from_directory(args.gold_directory)
    system_dataset = bd.BratDataset.from_directory(args.system_directory)

    result = count_dataset(gold_dataset, system_dataset)
    output = format_results(result, horizontal=args.horizontal, red=args.red)
    print(output)


if __name__ == '__main__':
    main()
