import pandas as pd

from bratlib import data as bd
from bratlib.calculators import entity_agreement


def test_entity_agreement():
    """
    Test that bratlib.calculators.entity_agreement.measure_ann_file accurately counts binary classification instances.
    """
    gold = bd.BratFile.from_data(entities=[
        bd.Entity('A', [(1, 2)], ''),
        bd.Entity('B', [(3, 4)], ''),
        bd.Entity('A', [(5, 6)], ''),  # fn for A
        bd.Entity('C', [(7, 8)], ''),  # fn for C
        bd.Entity('C', [(9, 10)], ''),
    ])

    system = bd.BratFile.from_data(entities=[
        bd.Entity('B', [(1, 2)], ''),    # fn for A, fp for B
        bd.Entity('B', [(3, 4)], ''),    # tp for B
        bd.Entity('C', [(9, 10)], ''),   # tp for C
        bd.Entity('D', [(11, 12)], ''),  # fp for D
        bd.Entity('A', [(13, 14)], ''),  # fp for A
    ])

    expected = pd.DataFrame(
        [
            ['A', 0, 1, 0, 2],
            ['B', 1, 1, 0, 0],
            ['C', 1, 0, 0, 1],
            ['D', 0, 1, 0, 0],
        ],
        columns=['tag', 'tp', 'fp', 'tn', 'fn'],
    ).set_index('tag')

    actual = entity_agreement.measure_ann_file(gold, system)
    pd.testing.assert_frame_equal(expected, actual)


def test_dataset_entity_agreement(monkeypatch):
    """
    Test that bratlib.calculators.entity_agreement.measure_dataset merges dataframes correctly.
    """

    def mock_generator(x, y, *args, **kwargs):
        a = pd.DataFrame(
            [
                ['A', 0, 1, 0, 2],
                ['B', 1, 1, 0, 0]
            ],
            columns=['tag', 'tp', 'fp', 'tn', 'fn'],
        ).set_index('tag')

        b = pd.DataFrame(
            [
                ['A', 0, 1, 0, 2],
                ['C', 1, 1, 0, 0]
            ],
            columns=['tag', 'tp', 'fp', 'tn', 'fn'],
        ).set_index('tag')

        c = pd.DataFrame(
            [
                ['B', 1, 1, 0, 0],
                ['C', 1, 0, 0, 3]
            ],
            columns=['tag', 'tp', 'fp', 'tn', 'fn'],
        ).set_index('tag')

        return {1: a, 2: b, 3: c}[x]

    def mock_generator_two(*args, **kwargs):
        yield from [(1, 1), (2, 2), (3, 3)]

    monkeypatch.setattr(entity_agreement, 'measure_ann_file', mock_generator)
    monkeypatch.setattr(entity_agreement, 'zip_datasets', mock_generator_two)

    actual = entity_agreement.measure_dataset(None, None)

    expected = pd.DataFrame(
        [
            ['A', 0, 2, 0, 4],
            ['B', 2, 2, 0, 0],
            ['C', 2, 1, 0, 3]
        ],
        columns=['tag', 'tp', 'fp', 'tn', 'fn'], dtype=float
    ).set_index('tag')

    pd.testing.assert_frame_equal(expected, actual)
