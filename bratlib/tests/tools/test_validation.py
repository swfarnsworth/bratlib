import pytest
import pandas as pd

from bratlib import data as bd
from bratlib.tools.validation import validate_bratfile_entities


def _mock_ann_file(ann: bd.BratFile, text: str, name: str, directory) -> None:
    txt_path = directory / (name + '.txt')
    ann_path = directory / (name + '.ann')
    txt_path.write_text(text)
    ann_path.write_text(str(ann))
    ann.ann_path, ann._txt_path = ann_path, txt_path


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
    _mock_ann_file(a_file, "The quick brown fox jumped over the lazy dog.", 'a', dataset_path)

    return bd.BratDataset(dataset_path, [a_file])


def test_validate_bratfile_entities(brat_dataset):
    ann = brat_dataset.brat_files[0]
    expected = pd.DataFrame.from_dict(
        dict(zip(ann.entities, [True, True, False, False])),
        orient='index', columns=['match']
    )
    actual = validate_bratfile_entities(ann)
    pd.testing.assert_frame_equal(expected, actual, check_names=False)
