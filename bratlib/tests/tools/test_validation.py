import pytest
import pandas as pd

from bratlib import data as bd
from bratlib.tools.validation import validate_bratfile_entities


@pytest.fixture
def brat_dataset(tmp_path):
    dataset_path = tmp_path / 'data'
    dataset_path.mkdir()

    a_file = bd.BratFile.from_data(entities=[
        bd.Entity('A', [(4, 9)], 'quick'),
        bd.Entity('A', [(4, 9), (20, 26)], 'quick jumped'),
        bd.Entity('A', [(4, 9)], 'not quick'),
        bd.Entity('A', [(4, 9), (20, 26)], 'not quick jumped'),
    ])

    a_ann, a_txt = (dataset_path / 'a.ann'), (dataset_path / 'a.txt')
    a_txt.write_text("The quick brown fox jumped over the lazy dog.")
    a_ann.write_text(str(a_file))
    a_file.ann_path, a_file._txt_path = a_ann, a_txt

    return bd.BratDataset(dataset_path, [a_file])


def test_validate_bratfile_entities(brat_dataset):
    ann = brat_dataset.brat_files[0]
    expected = pd.DataFrame.from_dict(
        dict(zip(ann.entities, [True, True, False, False])),
        orient='index', columns=['match']
    )
    actual = validate_bratfile_entities(ann)
    pd.testing.assert_frame_equal(expected, actual, check_names=False)
