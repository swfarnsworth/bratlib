import pandas as pd
import pytest

from bratlib import data as bd
from bratlib.calculators.relation_confusion_matrix import count_file

ents = [
    bd.Entity('A', [(1, 2)], ''),
    bd.Entity('B', [(3, 4)], ''),
    bd.Entity('A', [(5, 6)], ''),
    bd.Entity('C', [(7, 8)], ''),
    bd.Entity('C', [(9, 10)], '')
]

gold = bd.BratFile.from_data(
    entities=ents,
    relations=[
        bd.Relation(arg1=ents[0], arg2=ents[1], relation='AB'),
        bd.Relation(arg1=ents[2], arg2=ents[3], relation='AC'),
        bd.Relation(arg1=ents[1], arg2=ents[4], relation='BC'),
        bd.Relation(arg1=ents[2], arg2=ents[4], relation='AC')  # NONE for gold
    ]
)

system = bd.BratFile.from_data(
    entities=ents,
    relations=[
        bd.Relation(arg1=ents[0], arg2=ents[1], relation='AB'),
        bd.Relation(arg1=ents[2], arg2=ents[3], relation='AC'),
        bd.Relation(arg1=ents[1], arg2=ents[4], relation='BC'),
        bd.Relation(arg1=ents[1], arg2=ents[3], relation='BC')  # NONE for system
    ]
)

with_none_expected = pd.DataFrame([
    [1, 0, 0, 0],
    [0, 1, 0, 1],
    [0, 0, 1, 0],
    [0, 0, 1, 0]
], index=['AB', 'AC', 'BC', 'NONE'], columns=['AB', 'AC', 'BC', 'NONE'])

without_none_expected = pd.DataFrame([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
], index=['AB', 'AC', 'BC'], columns=['AB', 'AC', 'BC'])


@pytest.mark.parametrize("expected, use_none", [(with_none_expected, True), (without_none_expected, False)])
def test_relation_confusion_matrix(expected, use_none):
    actual = count_file(gold, system, include_none=use_none)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False, check_names=False)
