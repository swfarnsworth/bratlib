import pandas as pd

from bratlib import data as bd
from bratlib.calculators.entity_agreement import measure_ann_file


gold = bd.BratFile.from_data(entities=[
    bd.Entity('A', [(1, 2)], ''),
    bd.Entity('B', [(3, 4)], ''),
    bd.Entity('A', [(5, 6)], ''),   # fn for A
    bd.Entity('C', [(7, 8)], ''),   # fn for C
    bd.Entity('C', [(9, 10)], ''),
])

system = bd.BratFile.from_data(entities=[
    bd.Entity('B', [(1, 2)], ''),    # fn for A, fp for B
    bd.Entity('B', [(3, 4)], ''),    # tp for B
    bd.Entity('C', [(9, 10)], ''),   # tp for C
    bd.Entity('D', [(11, 12)], ''),  # fp for D
    bd.Entity('A', [(13, 14)], ''),  # fp for A
])


def test_entity_agreement():
    """
    Test that bratlib.calculators.entity_agreement.measure_ann_file accurately counts binary classification instances.
    """
    expected = pd.DataFrame(
        [
            ['A', 0, 1, 0, 2],
            ['B', 1, 1, 0, 0],
            ['C', 1, 0, 0, 1],
            ['D', 0, 1, 0, 0],
        ],
        columns=['tag', 'tp', 'fp', 'tn', 'fn'],
    ).set_index('tag')

    actual = measure_ann_file(gold, system)
    pd.testing.assert_frame_equal(expected, actual)
