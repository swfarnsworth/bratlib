import typing as t
from functools import reduce
from operator import and_, attrgetter

from bratlib.data import BratDataset


def zip_datasets(*datasets: BratDataset) -> t.Iterable[t.Tuple[BratDataset, ...]]:
    """
    This function is a wrapper around the `zip` builtin that allows parallel iteration over BratDatasets in
    terms of the BratFile instances they contain. For all BratFile names that appear in all BratDatasets passed
    to this function, each iteration will yield the BratFiles with that name from all datasets.
    """
    matching_anns = reduce(and_, ({a.name for a in ds} for ds in datasets))
    iterators = [filter(lambda a: a.name in matching_anns, sorted(ds, key=attrgetter('name'))) for ds in datasets]
    yield from zip(*iterators)
