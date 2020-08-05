from collections import Counter

from bratlib.data import BratDataset


class StatsDataset(BratDataset):

    def count_entities(self):
        return sum((Counter(ent.tag for ent in f.entities) for f in self), Counter())

    def count_relations(self):
        return sum((Counter(rel.relation for rel in f.relations) for f in self), Counter())
