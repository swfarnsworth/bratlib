from operator import and_, attrgetter
from functools import reduce
import typing as t

from bratlib.data import BratDataset


def zip_datasets(*datasets: BratDataset) -> t.Iterable[t.Tuple[BratDataset]]:
    matching_anns = reduce(and_, ({a.name for a in ds} for ds in datasets))
    iterators = (filter(lambda a: a.name in matching_anns, sorted(ds, key=attrgetter('name'))) for ds in datasets)
    yield from iterators
