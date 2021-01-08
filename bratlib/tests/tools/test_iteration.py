import pytest
from random import shuffle
from types import SimpleNamespace

from bratlib.tools.iteration import zip_datasets


def test_zip_datasets():
    matching_names = [
        SimpleNamespace(name='a'),
        SimpleNamespace(name='s'),
        SimpleNamespace(name='z')
    ]

    dataset_a = matching_names + [
        SimpleNamespace(name='1'),
        SimpleNamespace(name='2'),
        SimpleNamespace(name='3')
    ]

    dataset_b = matching_names + [
        SimpleNamespace(name='4'),
        SimpleNamespace(name='5'),
        SimpleNamespace(name='6')
    ]

    dataset_c = matching_names + [
        SimpleNamespace(name='7'),
        SimpleNamespace(name='8'),
        SimpleNamespace(name='9')
    ]

    for d in [dataset_a, dataset_b, dataset_c]:
        shuffle(d)

    data_zip = zip_datasets(dataset_a, dataset_b, dataset_c)

    a, b, c = next(data_zip)
    assert a.name == b.name == c.name == 'a'

    a, b, c = next(data_zip)
    assert a.name == b.name == c.name == 's'

    a, b, c = next(data_zip)
    assert a.name == b.name == c.name == 'z'

    with pytest.raises(StopIteration):
        next(data_zip)
