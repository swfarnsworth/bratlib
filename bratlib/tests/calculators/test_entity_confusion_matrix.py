import pandas as pd

from bratlib import data as bd
from bratlib.calculators.entity_confusion_matrix import count_file


def test_entity_confusion_matrix():
    gold = bd.BratFile.from_data(entities=[
        bd.Entity('A', [(1, 2)], ''),
        bd.Entity('B', [(3, 4)], ''),
        bd.Entity('A', [(5, 6)], ''),
        bd.Entity('C', [(7, 8)], ''),
        bd.Entity('C', [(9, 10)], '')
    ])

    system = bd.BratFile.from_data(entities=[
        bd.Entity('A', [(1, 2)], ''),  # AA
        bd.Entity('A', [(3, 4)], ''),  # BA
        bd.Entity('C', [(5, 6)], ''),  # AC
        bd.Entity('C', [(7, 8)], ''),  # CC
        bd.Entity('D', [(9, 10)], '')  # CD
    ])

    expected = pd.DataFrame([
        [1, 0, 1, 0],
        [1, 0, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 0]
    ], columns=['A', 'B', 'C', 'D'], index=['A', 'B', 'C', 'D'])

    actual = count_file(gold, system)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False)
