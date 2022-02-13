import re
import typing as t
from dataclasses import dataclass, field

from bratlib.data import _utils


class AnnData:
    pass


@dataclass
class Entity(AnnData):
    tag: str
    spans: t.List[t.Tuple[int, int]]
    mention: str = field(compare=False)

    @classmethod
    def _from_re(cls, match: t.Match):
        tag = match[2]

        # Create list of tuples for every pair of spans
        spans = [int(m[0]) for m in re.finditer(r'\d+', match[3])]
        span_iter = iter(spans)
        spans = list(zip(span_iter, span_iter))

        mention = match[4]

        return cls(tag, spans, mention)

    @_utils.return_not_implemented
    def __lt__(self, other):
        return (self.spans[0], self.spans[-1], self.tag) < (other.spans[0], other.spans[-1], other.tag)

    def __hash__(self):
        return hash((self.tag, tuple(self.spans), self.mention))

    @_utils.return_not_implemented
    def __eq__(self, other):
        return (self.tag, self.spans, self.mention) == (other.tag, other.spans, other.mention)


@dataclass
class Event(AnnData):
    event_type: str
    trigger: Entity
    arguments: t.Dict[str, Entity]

    @_utils.return_not_implemented
    def __lt__(self, other):
        return (self.trigger, self.event_type) < (other.trigger, other.event_type)

    def __hash__(self):
        return hash((self.trigger, frozenset(self.arguments.items())))


@dataclass(eq=True)
class Relation(AnnData):
    relation: str
    arg1: Entity
    arg2: Entity

    @_utils.return_not_implemented
    def __lt__(self, other):
        return (self.arg1, self.arg2) < (other.arg1, other.arg2)

    def __hash__(self):
        return hash((self.relation, self.arg1, self.arg2))


@dataclass
class Equivalence(AnnData):
    items: t.List[Entity]

    @_utils.return_not_implemented
    def __lt__(self, other):
        return tuple(sorted(self.items)) < tuple(sorted(other.items))


@dataclass
class Attribute(AnnData):
    tag: str
    items: t.List[AnnData]

    @_utils.return_not_implemented
    def __lt__(self, other):
        return self.tag < other.tag


@dataclass
class Normalization(AnnData):
    entity: Entity
    ontology: str
    ont_id: str

    @_utils.return_not_implemented
    def __lt__(self, other):
        return self.entity < other.entity
