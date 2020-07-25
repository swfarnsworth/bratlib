from __future__ import annotations

import os
import re
import typing as t
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

from cached_property import cached_property

# Define types
PathLike = t.Union[str, os.PathLike]

# Define regexes
ent_pattern = re.compile(r'(T\d+)\t([^\t]+) ((?:\d+ \d+;)*\d+ \d+)\t(.+)')
event_pattern = re.compile(r'(E\d+)\t[^\t:]+:T(\d+) ((?:[^\s:]+:T(?:\d+)[\s]*)+)')
rel_pattern = re.compile(r'R\d+\t(\S+) Arg1:(T\d+) Arg2:(T\d+)')
equiv_pattern = re.compile(r'\*\tEquiv ((?:T\d+[\s])+)')
attrib_pattern = re.compile(r'A\d+\t(\S+) ((?:[TE]\d+[\s])+)')
norm_pattern = re.compile(r'N\d+\tReference T(\d+) ((?:[^:])+):((?:[^\t])+)\t.+')


# Define annotation types

class AnnData:
    pass


@dataclass
class Entity(AnnData):
    tag: str
    spans: t.List[t.Tuple[int, int]]
    mention: str = field(compare=False)

    @classmethod
    def from_re(cls, match: t.Match):
        tag = match[2]

        # Create list of tuples for every pair of spans
        spans = [int(m[0]) for m in re.finditer(r'\d+', match[3])]
        span_iter = iter(spans)
        spans = list(zip(span_iter, span_iter))

        mention = match[4]

        return cls(tag, spans, mention)

    def __lt__(self, other):
        with suppress(AttributeError):
            return (self.spans[0], self.spans[-1], self.tag) < (other.spans[0], other.spans[-1], other.tag)
        return NotImplemented


@dataclass
class Event(AnnData):
    trigger: Entity
    arguments: t.List[Entity]

    def __lt__(self, other):
        with suppress(AttributeError):
            return (tuple(self.arguments), self.trigger) < (tuple(other.arguments), other.trigger)
        return NotImplemented


@dataclass
class Relation(AnnData):
    relation: str
    arg1: Entity
    arg2: Entity

    def __lt__(self, other):
        with suppress(AttributeError):
            return (self.arg1, self.arg2) < (other.arg1, other.arg2)
        return NotImplemented


@dataclass
class Equivalence(AnnData):
    items: t.List[Entity]

    def __lt__(self, other):
        with suppress(AttributeError):
            return tuple(sorted(self.items)) < tuple(sorted(other.items))
        return NotImplemented


@dataclass
class Attribute(AnnData):
    tag: str
    items: t.List[AnnData]

    def __lt__(self, other):
        # TODO
        return NotImplemented


@dataclass
class Normalization(AnnData):
    entity: Entity
    ontology: str
    ont_id: str

    def __lt__(self, other):
        with suppress(AttributeError):
            return self.entity < other.entity
        return NotImplemented


# Define file-level representation


class NoTxtError(FileNotFoundError):
    pass


class BratFile:

    def __init__(self, ann_path: PathLike, txt_path: PathLike):
        self.ann_path = Path(ann_path)
        self._txt_path = Path(txt_path) if isinstance(txt_path, (str, os.PathLike)) else None
        self.name = self.ann_path.name

        self._mapping = {}

    @classmethod
    def from_ann_path(cls, ann_path: PathLike):
        ann_path = Path(ann_path)
        possible_txt = Path(str(ann_path).rstrip('ann') + 'txt')
        txt_path = possible_txt if possible_txt.exists() else None
        return cls(ann_path, txt_path)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.name}, {self._txt_path}>'

    def __lt__(self, other):
        with suppress(AttributeError):
            return self.name < other.name
        return NotImplemented

    @property
    def txt_path(self):
        if self._txt_path is None:
            raise NoTxtError('This BratFile does not have an associated txt file')
        return self._txt_path

    @cached_property
    def _data_dict(self) -> t.Dict[str, t.List[AnnData]]:
        with self.ann_path.open() as f:
            text = f.read()

        data_dict = {}

        # Entities
        ent_mapping = {match[1]: Entity.from_re(match) for match in ent_pattern.finditer(text)}
        self._mapping.update(ent_mapping)
        data_dict['entities'] = sorted(ent_mapping.values())

        # Relations
        rels = []

        for match in rel_pattern.finditer(text):
            tag = match[1]
            arg1 = self._mapping[match[2]]
            arg2 = self._mapping[match[3]]
            new_rel = Relation(tag, arg1, arg2)
            rels.append(new_rel)
        data_dict['relations'] = sorted(rels)

        # Equivalences
        equivs = []

        for match in equiv_pattern.finditer(text):
            equiv_entities = [self._mapping[e] for e in re.finditer(r'T\d+', match[1])]
            equiv_entities.sort()
            equivs.append(Equivalence(equiv_entities))

        data_dict['equivalences'] = sorted(equivs)

        # Attributes
        attrs = []

        for match in attrib_pattern.finditer(text):
            tag = match[1]
            data = [self._mapping[e] for e in re.finditer(r'[ET]\d+', match[2])]
            attrs.append(Attribute(tag, data))

        data_dict['attributes'] = attrs

        # TODO norms

        return data_dict

    @property
    def entities(self) -> t.Iterable[Entity]:
        return self._data_dict['entities']

    @property
    def relations(self) -> t.Iterable[Relation]:
        return self._data_dict['relations']

    @property
    def equivalences(self) -> t.Iterable[Equivalence]:
        return self._data_dict['equivalences']

    @property
    def attributes(self) -> t.Iterable[Attribute]:
        return self._data_dict['attributes']

    @property
    def normalizations(self) -> t.Iterable[Normalization]:
        # return self._data_dict['normalizations']
        raise NotImplementedError


class BratDataset:

    def __init__(self, dir_path: PathLike, brat_files: t.List[BratFile]):
        self.directory = Path(dir_path)
        self.brat_files = brat_files

    @classmethod
    def from_directory(cls, dir_path: PathLike) -> BratDataset:
        directory = Path(dir_path)
        brat_files = [BratFile.from_ann_path(p) for p in directory.iterdir() if p.suffix == '.ann']
        brat_files.sort()
        return cls(directory, brat_files)

    def __iter__(self) -> t.Iterator[BratFile]:
        return iter(self.brat_files)
