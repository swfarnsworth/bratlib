import typing as t
from collections import Counter
from functools import reduce
from operator import or_

from bratlib.data import BratDataset


class StatsDataset(BratDataset):

    def get_labels(self) -> t.Set[str]:
        return reduce(or_, ({e.mention for e in a.entities} for a in self))

    def count_entities(self):
        return sum((Counter(ent.tag for ent in f.entities) for f in self), Counter())

    def count_relations(self):
        return sum((Counter(rel.relation for rel in f.relations) for f in self), Counter())
