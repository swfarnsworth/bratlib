import pandas as pd

from bratlib import data as bd
from bratlib.tools.validation import validate_bratfile_entities


def test_validate_bratfile(tmp_path):
    text_path = tmp_path / 'a.txt'
    text_path.write_text("The quick brown fox jumped over the lazy dog.")
    ann_path = tmp_path / 'a.ann'

    entities = [
        bd.Entity('A', [(4, 9)], 'quick'),
        bd.Entity('A', [(4, 9), (20, 26)], 'quick jumped'),
        bd.Entity('A', [(4, 9)], 'not quick'),
        bd.Entity('A', [(4, 9), (20, 26)], 'not quick jumped'),
    ]

    ann = bd.BratFile.from_data(entities=entities)
    ann.ann_path, ann._txt_path = ann_path, text_path

    expected = pd.DataFrame.from_dict(
        {e: b for e, b in zip(entities, [True, True, False, False])},
        orient='index', columns=['match']
    )
    actual = validate_bratfile_entities(ann)
    pd.testing.assert_frame_equal(expected, actual, check_names=False)
