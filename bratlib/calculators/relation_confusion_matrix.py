import argparse
import typing as t
from itertools import product

import numpy as np
import pandas as pd

from bratlib import data as bd
from bratlib.calculators._utils import _merge_dataset_dataframes


def _generate_relationship_pairs(gold: bd.BratFile, system: bd.BratFile) -> t.Iterable[t.Tuple[str, str]]:
    """
    Generates tuples of relationship tags for which the entities are the same.
    When these pairs are exhausted, it generates tuples for all unmatched entities with 'NONE'.
    The first element of the tuple is gold, the second is system.
    """
    gold_match = {g: False for g in gold.relations}
    sys_match = {s: False for s in system.relations}

    for g, s in product(gold.relations, system.relations):
        if (g.arg1, g.arg2) == (s.arg1, s.arg2):
            gold_match[g] = sys_match[s] = True
            yield (g.relation, s.relation)

    yield from (('NONE', s.relation) for s, b in sys_match.items() if not b)
    yield from ((g.relation, 'NONE') for g, b in gold_match.items() if not b)


def count_file(gold: bd.BratFile, system: bd.BratFile) -> pd.DataFrame:
    """Creates a relation confusion matrix DataFrame for one document, with gold indices and system columns."""
    realtions = sorted({r.relation for r in gold.relations} | {r.relation for r in system.relations}) + ['NONE']
    num_relations = len(realtions)
    table = pd.DataFrame(
        data=np.zeros((num_relations, num_relations)),
        index=realtions,
        columns=realtions
    )

    for g, s in _generate_relationship_pairs(gold, system):
        table.loc[g, s] += 1

    return table


def count_dataset(gold: bd.BratDataset, system: bd.BratDataset) -> pd.DataFrame:
    """Creates a relation confusion matrix DataFrame for a dataset with gold indices and system columns."""
    return _merge_dataset_dataframes(gold, system, count_file)


def main():
    parser = argparse.ArgumentParser(description='Creates a confusion matrix for relations between two datasets')
    parser.add_argument('gold_directory', help='Directory containing the gold ann files')
    parser.add_argument('system_directory', help='Directory containing the system ann files')
    args = parser.parse_args()

    gold_dataset = bd.BratDataset.from_directory(args.gold_directory)
    system_dataset = bd.BratDataset.from_directory(args.system_directory)

    result = count_dataset(gold_dataset, system_dataset)
    print(result.to_csv(float_format=f'%.{args.decimal}f'))


if __name__ == '__main__':
    main()
