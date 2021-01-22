import pandas as pd
import pytest

from bratlib import data as bd
from bratlib.tools.validation import validate_bratfile_entities, validate_bratdataset_entities


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

    b_file = bd.BratFile.from_data(entities=[
        bd.Entity('A', [(4, 9)], 'happy'),
        bd.Entity('A', [(4, 9), (20, 26)], 'happy jumped'),
        bd.Entity('A', [(4, 9)], 'not happy'),
        bd.Entity('A', [(4, 9), (20, 26)], 'not quick jumped'),
    ])
    _mock_ann_file(b_file, "The happy brown fox jumped over the lazy dog.", 'b', dataset_path)

    return bd.BratDataset(dataset_path, [a_file, b_file])


def test_validate_bratfile_entities(brat_dataset):
    ann = brat_dataset.brat_files[0]
    expected = pd.DataFrame.from_dict(
        dict(zip(ann.entities, [True, True, False, False])),
        orient='index', columns=['match']
    )
    actual = validate_bratfile_entities(ann)
    pd.testing.assert_frame_equal(expected, actual, check_names=False)


def test_validate_bratdataset_entities(brat_dataset):
    ann_a, ann_b = brat_dataset.brat_files

    # Test for all rows
    rows = [('a', e, b) for e, b in zip(ann_a.entities, [True, True, False, False])]
    rows += [('b', e, b) for e, b in zip(ann_b.entities, [True, True, False, False])]
    expected = pd.DataFrame(rows, columns=['file', 'entity', 'match'])
    expected.set_index(['entity', 'file'], inplace=True)

    actual = validate_bratdataset_entities(brat_dataset, invalid_only=False)
    pd.testing.assert_frame_equal(expected, actual)

    # Test for only invalid rows
    rows = [('a', e, False) for e in ann_a.entities[2:]]
    rows += [('b', e, False) for e in ann_b.entities[2:]]
    expected = pd.DataFrame(rows, columns=['file', 'entity', 'match'])
    expected.set_index(['entity', 'file'], inplace=True)

    actual = validate_bratdataset_entities(brat_dataset, invalid_only=True)
    pd.testing.assert_frame_equal(expected, actual)

    # Test using pathlib.Path as `file` type
    rows = [(ann_a.ann_path, e, b) for e, b in zip(ann_a.entities, [True, True, False, False])]
    rows += [(ann_b.ann_path, e, b) for e, b in zip(ann_b.entities, [True, True, False, False])]
    expected = pd.DataFrame(rows, columns=['file', 'entity', 'match'])
    expected.set_index(['entity', 'file'], inplace=True)

    actual = validate_bratdataset_entities(brat_dataset, invalid_only=False, index_by_path=True)
    pd.testing.assert_frame_equal(expected, actual)
