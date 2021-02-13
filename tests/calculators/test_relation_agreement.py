import pandas as pd

from bratlib import data as bd
from bratlib.calculators.relation_agreement import measure_ann_file

entities = [
    bd.Entity('A', [(1, 2)], ''),
    bd.Entity('B', [(3, 4)], ''),
    bd.Entity('A', [(5, 6)], ''),
    bd.Entity('C', [(7, 8)], ''),
    bd.Entity('C', [(9, 10)], ''),
    bd.Entity('C', [(11, 12)], ''),
    bd.Entity('C', [(13, 14)], ''),
]

gold = bd.BratFile.from_data(
    entities=entities,
    relations=[
        bd.Relation('A', entities[0], entities[1]),
        bd.Relation('B', entities[2], entities[3]),  # fn for B
        bd.Relation('B', entities[4], entities[5]),  # fn for B
        bd.Relation('C', entities[5], entities[6]),
    ]
)

system = bd.BratFile.from_data(
    entities=entities,
    relations=[
        bd.Relation('A', entities[0], entities[1]),  # tp for A
        bd.Relation('B', entities[4], entities[3]),  # fp for B
        bd.Relation('C', entities[5], entities[6]),  # tp for C
    ]
)


def test_relation_agreement():
    """
    Test that bratlib.calculators.relation_agreement.measure_ann_file accurately counts binary classification instances.
    """
    expected = pd.DataFrame(
        [
            ['A', 1, 0, 0, 0],
            ['B', 0, 1, 0, 2],
            ['C', 1, 0, 0, 0],
        ],
        columns=['tag', 'tp', 'fp', 'tn', 'fn'],
    ).set_index('tag')

    actual = measure_ann_file(gold, system)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False)
