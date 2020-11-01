import argparse
import typing as t
from collections import UserDict
from itertools import combinations

import pandas as pd
import numpy as np

from bratlib import data as bd
from bratlib.tools.iteration import zip_datasets

NO_RELATION = 'NO_RELATION'


class RelationLookupDict(UserDict, t.Dict[t.Tuple[bd.Entity, bd.Entity], str]):
    """
    Dictionary type mapping pairs of Entities to the name of the relationship they share in a given document.
    Relations are treated as reflexive so a KeyError raised with (a, b) will be resolved with (b, a).
    Non-relationships need not be stored as NO_RELATION will be returned if the key can't be resolved by reversing it.
    """

    @classmethod
    def from_bratfile(cls, bratfile: bd.BratFile):
        return cls({(r.arg1, r.arg2): r.relation for r in bratfile.relations})

    def __missing__(self, key):
        """Tries (b, a) if (a, b) is not a key, otherwise returns NO_RELATION"""
        opposite = (key[1], key[0])
        return self[opposite] if opposite in self else NO_RELATION


def create_relationship_table_for_file(gold: bd.BratFile, system_a: bd.BratFile, system_b: bd.BratFile) -> pd.DataFrame:
    """
    Constructs a DataFrame of three columns, one for gold, system a, and system b. Each row represents what each of
    the three datasets said the relationship between two entities are, unless it was NO_RELATION for all three. The
    entity pair each row represents is unstated, as the purpose of the DataFrame is to see agreement between datasets.
    """
    # BratFile.from_ann_file will sort the entities anyway, but instances created manually might not be sorted.
    gold_ents = sorted(gold.entities)
    sys_a_ents = sorted(system_a.entities)
    sys_b_ents = sorted(system_b.entities)

    if gold_ents != sys_a_ents != sys_b_ents:
        raise RuntimeError(f'These files don\'t have exactly the same set of entities: {gold}, {system_a}, {system_b}')

    lookup_tables = [RelationLookupDict.from_bratfile(b) for b in (gold, system_a, system_b)]

    rows: t.List[t.Tuple[str, str, str]] = []

    for ent_one, ent_two in combinations(gold_ents, 2):
        new_row = tuple(lookup[ent_one, ent_two] for lookup in lookup_tables)
        if all(cell == NO_RELATION for cell in new_row):
            continue
        rows.append(new_row)

    return pd.DataFrame(rows, columns=['GOLD', 'SYSTEM A', 'SYSTEM B'])


def create_relationship_table_for_dataset(gold: bd.BratDataset, system_a: bd.BratDataset, system_b: bd.BratDataset) -> pd.DataFrame:
    dataframes = [create_relationship_table_for_file(g, a, b) for g, a, b in zip_datasets(gold, system_a, system_b)]
    return pd.concat(dataframes)


def create_pseduo_relationship_table(real_table: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe of three columns and returns a dataframe of two columns where
    the first column is always the same, and the second column is a random selection
    from the other two columns for each row.
    """
    two_systems = real_table.iloc[:, 1:3]
    pseudo_system = two_systems.values[np.arange(len(two_systems)), np.random.randint(-2, 0, size=len(two_systems))]
    pseudo_system = pd.DataFrame(pseudo_system, columns=['PSEUDO SYSTEM'])
    new_table = real_table.iloc[:, 0:1].join(pseudo_system.iloc[:, 0:1])
    return new_table.loc[(new_table != NO_RELATION).any(axis=1)]


def count_pseudo_system(table: pd.DataFrame) -> float:
    fp = len(table[table['GOLD'] == NO_RELATION].count(1))
    tp = len(table[table['GOLD'] == table['PSEUDO SYSTEM']].count(1))
    fn = len(table[(table['GOLD'] != table['PSEUDO SYSTEM']) & (table['GOLD'] != NO_RELATION)].count(1))

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * (precision * recall) / (precision + recall)
