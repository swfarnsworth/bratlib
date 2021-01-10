import pandas as pd

from bratlib import data as bd
from bratlib.calculators.relation_confusion_matrix import count_file


def test_relation_confusion_matrix():
    entities = ents = [
        bd.Entity('A', [(1, 2)], ''),
        bd.Entity('B', [(3, 4)], ''),
        bd.Entity('A', [(5, 6)], ''),
        bd.Entity('C', [(7, 8)], ''),
        bd.Entity('C', [(9, 10)], '')
    ]

    gold = bd.BratFile.from_data(
        entities=entities,
        relations=[
            bd.Relation(arg1=ents[0], arg2=ents[1], relation='AB'),
            bd.Relation(arg1=ents[2], arg2=ents[3], relation='AC'),
            bd.Relation(arg1=ents[1], arg2=ents[4], relation='BC'),
        ]
    )

    system = bd.BratFile.from_data(
        entities=entities,
        relations=[
            bd.Relation(arg1=ents[0], arg2=ents[1], relation='AB'),
            bd.Relation(arg1=ents[2], arg2=ents[3], relation='AC'),
            bd.Relation(arg1=ents[1], arg2=ents[4], relation='BC'),
        ]
    )
    order = ['AB', 'AC', 'BC', 'NONE']

    expected = pd.DataFrame([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 0]
    ], index=order, columns=order)

    actual = count_file(gold, system)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False)
