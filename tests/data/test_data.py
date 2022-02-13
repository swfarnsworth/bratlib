import pathlib

import pytest

from bratlib import data as bd

sample_doc = """T1\tA 1 2\tlorem
T2\tB 3 5;5 6\tipsum
E1\tA:T1 Org1:T1 Org2:T2
E2\tEggs:T1 Spam:T2
E3\tFoo:T1
R1\tC Arg1:T1 Arg2:T2
*\tEquiv T1 T2
A1\tF E1
N1\tReference T1 C:1\tlorem
"""


@pytest.fixture
def ann_file(tmp_path) -> pathlib.Path:
    ann_path = tmp_path / 'sample.ann'
    ann_path.write_text(sample_doc)
    return ann_path


@pytest.fixture
def ann_sample(ann_file) -> bd.BratFile:
    return bd.BratFile.from_ann_path(ann_file)


ents_expected = [
    bd.Entity('A', [(1, 2)], 'lorem'),
    bd.Entity('B', [(3, 5), (5, 6)], 'ipsum'),
]

event_expected = [
    bd.Event('A', ents_expected[0], {'Org1': ents_expected[0], 'Org2': ents_expected[1]}),
    bd.Event('Eggs', ents_expected[0], {'Spam': ents_expected[1]}),
    bd.Event('Foo', ents_expected[0], {})
]


def test_entities(ann_sample):
    assert ann_sample.entities == ents_expected


def test_events(ann_sample):
    assert ann_sample.events == event_expected


def test_relations(ann_sample):
    rel_expected = [
        bd.Relation('C', ents_expected[0], ents_expected[1])
    ]
    assert ann_sample.relations == rel_expected
    assert ann_sample.relations[0].arg1 is ann_sample.entities[0]


def test_equivalences(ann_sample):
    equiv_expected = [
        bd.Equivalence(ents_expected[0:2])
    ]
    assert ann_sample.equivalences == equiv_expected


def test_attributes(ann_sample):
    attribute_expected = [
        bd.Attribute('F', [event_expected[0]])
    ]
    assert ann_sample.attributes == attribute_expected


def test_normalizations(ann_sample):
    norm_expected = [
        bd.Normalization(ents_expected[0], 'C', '1')
    ]
    assert ann_sample.normalizations == norm_expected


def test_bratfile_str(ann_sample):
    assert str(ann_sample) == sample_doc


def test_brat_parse_error(tmp_path):
    bad_ann = """T1\tA 1 2\tlorem
    T2\tB 3 5;5 6\tipsum
    E1\tA:T1 Org1:T1 Org2:T2
    R1\tC Arg1:T99 Arg2:T10000
    *\tEquiv T1 T2
    A1\tF E1
    N1\tReference T1 C:1\tlorem
    """
    ann_path = tmp_path / 'bad.ann'
    ann_path.write_text(bad_ann)

    with pytest.raises(bd.BratParseError):
        bd.BratFile.from_ann_path(ann_path).entities
