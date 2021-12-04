import argparse
import typing as t
from itertools import product

import pandas as pd

from bratlib import data as bd
from bratlib.calculators import _utils



def _generate_entity_pairs(gold: bd.BratFile, system: bd.BratFile) -> t.Iterable[t.Tuple[str, str]]:
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

    yield from ((_utils.NONE, s.tag) for s, b in sys_match.items() if not b)
    yield from ((g.tag, _utils.NONE) for g, b in gold_match.items() if not b)


def count_file(gold: bd.BratFile, system: bd.BratFile, *, include_none=False) -> pd.DataFrame:
    """Creates an entity confusion matrix DataFrame for one document, with gold indices and system columns."""
    entities = sorted({e.tag for e in gold.entities} | {e.tag for e in system.entities})

    if include_none:
        entities.append(_utils.NONE)

    table = pd.DataFrame(index=entities, columns=entities).fillna(0)

    for g, s in _generate_entity_pairs(gold, system):
        if not include_none and _utils.NONE in {g, s}:
            break
        table.loc[g, s] += 1

    return table


def count_dataset(gold: bd.BratDataset, system: bd.BratDataset) -> pd.DataFrame:
    """Creates an entity confusion matrix DataFrame for a dataset with gold indices and system columns."""
    return _utils.merge_dataset_dataframes(gold, system, count_file)


def main():
    parser = argparse.ArgumentParser(description='Creates a confusion matrix for entities between two datasets')
    parser.add_argument('gold_directory', help='Directory containing the gold ann files')
    parser.add_argument('system_directory', help='Directory containing the system ann files')
    parser.add_argument('-r', '--red', action='store_true', help='Flag to print the results in red')
    args = parser.parse_args()

    gold_dataset = bd.BratDataset.from_directory(args.gold_directory)
    system_dataset = bd.BratDataset.from_directory(args.system_directory)

    result = count_dataset(gold_dataset, system_dataset).to_csv()

    if args.red:
        result = f'\033[1;31;40m{result}\033[m'

    print(result)


if __name__ == '__main__':
    main()
