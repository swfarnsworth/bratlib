from __future__ import annotations

import os
import re
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from cached_property import cached_property

from bratlib.utils import except_return

# Define types
PathLike = t.Union[str, os.PathLike]

# Define regexes
ent_pattern = re.compile(r'(T\d+)\t([^\t]+) ((?:\d+ \d+;)*\d+ \d+)\t(.+)')
event_pattern = re.compile(
    r'(?P<id>E\d+)\t(?P<trigger>[^\t:]+):(?P<trigger_ent>T\d+) (?P<items>(?:Org\d:[TRAN]\d+[\s]*)+)')
rel_pattern = re.compile(r'R\d+\t(\S+) Arg1:(T\d+) Arg2:(T\d+)')
equiv_pattern = re.compile(r'\*\tEquiv ((?:T\d+[\s])+)')
attrib_pattern = re.compile(r'A\d+\t(\S+) ((?:[TE]\d+[\s])+)')
norm_pattern = re.compile(r'N\d+\tReference (T\d+) ((?:[^:])+):((?:[^\t])+)\t.+')

# Decorator to streamline comparison operator implementations
_notimp = except_return(NotImplemented, AttributeError)


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

    @_notimp
    def __lt__(self, other):
        return (self.spans[0], self.spans[-1], self.tag) < (other.spans[0], other.spans[-1], other.tag)

    def __hash__(self):
        return hash((self.tag, tuple(self.spans), self.mention))

    @_notimp
    def __eq__(self, other):
        return (self.tag, self.spans, self.mention) == (other.tag, other.spans, other.mention)


@dataclass
class Event(AnnData):
    trigger: Entity
    arguments: t.List[Entity]

    @_notimp
    def __lt__(self, other):
        return self.trigger < other.trigger

    def __hash__(self):
        return hash((self.trigger, tuple(self.arguments)))


@dataclass(eq=True)
class Relation(AnnData):
    relation: str
    arg1: Entity
    arg2: Entity

    @_notimp
    def __lt__(self, other):
        return (self.arg1, self.arg2) < (other.arg1, other.arg2)

    def __hash__(self):
        return hash((self.relation, self.arg1, self.arg2))


@dataclass
class Equivalence(AnnData):
    items: t.List[Entity]

    @_notimp
    def __lt__(self, other):
        return tuple(sorted(self.items)) < tuple(sorted(other.items))


@dataclass
class Attribute(AnnData):
    tag: str
    items: t.List[AnnData]

    @_notimp
    def __lt__(self, other):
        return self.tag < other.tag


@dataclass
class Normalization(AnnData):
    entity: Entity
    ontology: str
    ont_id: str

    @_notimp
    def __lt__(self, other):
        return self.entity < other.entity


# Define file-level representation


class NoTxtError(FileNotFoundError):
    pass


class BratFile:
    """
    BratFiles contain the following attributes for representing data found in their files:
    entities, events, relations, equivalences, attributes, normalizations.
    Accessing any one of these attributes for the first time will trigger opening the file for the first time,
    and all the data read from the file is cached.

    Every data item is represented once, so any subsequent references to the same data item are the same object.
    For example, any Relation accessible via `brat_file.relations` refers to two Entities; these are the same
    two Entity objects one would find in `brat_file.entities`.

    Giving a BratFile instance attributes of the same name as these with a leading underscore (so `_entities` instead
    of `entities`) will cause subsequent accesses of the non-underscore name to return that value.

    Accessing the `txt_path` attribute will raise NoTxtError if the instance does not have a txt file.
    """

    def __init__(self, ann_path: PathLike, txt_path: PathLike):
        self.ann_path = Path(ann_path)
        self._txt_path = Path(txt_path) if isinstance(txt_path, (str, os.PathLike)) else None
        self.name = self.ann_path.stem

        self._mapping = {}

    @classmethod
    def from_ann_path(cls, ann_path: PathLike):
        """Automatically pairs the ann file with a txt file if one by the same name exists in the directory"""
        ann_path = Path(ann_path)
        possible_txt = Path(str(ann_path).rstrip('ann') + 'txt')
        txt_path = possible_txt if possible_txt.exists() else None
        return cls(ann_path, txt_path)

    @classmethod
    def from_data(cls,
                  entities: t.Optional[t.List[Entity]] = None,
                  events: t.Optional[t.List[Event]] = None,
                  relations: t.Optional[t.List[Relation]] = None,
                  equivalences: t.Optional[t.List[Equivalence]] = None,
                  attributes: t.Optional[t.List[Attribute]] = None,
                  normalizations: t.Optional[t.List[Normalization]] = None,
                  ):
        """
        Creates an instance that does not represent an existing file. All data attributes are blank lists that
        can be mutated. These instances are not guaranteed to have an `ann_path` attribute defined.
        """
        new = super().__new__(cls)
        super().__init__(new)
        args = [entities, events, relations, equivalences, attributes, normalizations]
        attrs = ['_entities', '_events', '_relations', '_equivalences', '_attributes', '_normalizations']
        for arg, attr in zip(args, attrs):
            setattr(new, attr, [] if arg is None else arg)
        new._txt_path = None
        return new

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.name}>'

    @_notimp
    def __lt__(self, other):
        return self.name < other.name

    @property
    def txt_path(self):
        if self._txt_path is None:
            raise NoTxtError('This BratFile does not have an associated txt file.')
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

        events = []
        for m in event_pattern.finditer(text):
            trigger = self._mapping[m['trigger_ent']]
            items = [self._mapping[n[1]] for n in re.finditer(r'Org\d:([TRAN]\d+)', m['items'])]
            new_event = Event(trigger, items)
            self._mapping[m['id']] = new_event
            events.append(new_event)

        data_dict['events'] = sorted(events)

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
            equiv_entities = [self._mapping[e[0]] for e in re.finditer(r'T\d+', match[1])]
            equiv_entities.sort()
            equivs.append(Equivalence(equiv_entities))

        data_dict['equivalences'] = sorted(equivs)

        # Attributes
        attrs = []

        for match in attrib_pattern.finditer(text):
            tag = match[1]
            data = [self._mapping[e[0]] for e in re.finditer(r'[ET]\d+', match[2])]
            attrs.append(Attribute(tag, data))

        data_dict['attributes'] = sorted(attrs)

        # Normalizations
        data_dict['normalizations'] = sorted(Normalization(ent_mapping[m[1]], m[2], m[3])
                                             for m in norm_pattern.finditer(text))

        return data_dict

    @property
    def entities(self) -> t.Iterable[Entity]:
        return self._data_dict['entities'] if not hasattr(self, '_entities') else self._entities

    @property
    def events(self) -> t.Iterable[Event]:
        return self._data_dict['events'] if not hasattr(self, '_events') else self._events

    @property
    def relations(self) -> t.Iterable[Relation]:
        return self._data_dict['relations'] if not hasattr(self, '_relations') else self._relations

    @property
    def equivalences(self) -> t.Iterable[Equivalence]:
        return self._data_dict['equivalences'] if not hasattr(self, '_equivalences') else self._equivalences

    @property
    def attributes(self) -> t.Iterable[Attribute]:
        return self._data_dict['attributes'] if not hasattr(self, '_attributes') else self._attributes

    @property
    def normalizations(self) -> t.Iterable[Normalization]:
        return self._data_dict['normalizations'] if not hasattr(self, '_normalizations') else self._normalizations

    def __str__(self):
        """
        This method creates a representation that can be written to file,
        and is thus not a light-weight method call; use __repr__ for a lightweight representation
        """
        mappings = {}
        semicolon_join = ';'.join
        space_join = ' '.join

        output = ""

        for i, ent in enumerate(self.entities, 1):
            spans = semicolon_join(f'{s[0]} {s[1]}' for s in ent.spans)
            mappings[ent] = f'T{i}'
            output += f'T{i}\t{ent.tag} {spans}\t{ent.mention}\n'

        for i, event in enumerate(self.events, 1):
            mappings[event] = f'E{i}'
            output += f'E{i}\t{event.trigger.tag}:{mappings[event.trigger]} ' + \
                      space_join(f'Org{j}:{mappings[a]}' for j, a in enumerate(event.arguments, 1)) + '\n'

        for i, rel in enumerate(self.relations, 1):
            mappings[rel] = i
            output += f'R{i}\t{rel.relation} Arg1:{mappings[rel.arg1]} Arg2:{mappings[rel.arg2]}\n'

        for equiv in self.equivalences:
            output += f'*\tEquiv ' + space_join(mappings[x] for x in equiv.items) + '\n'

        for i, attr in enumerate(self.attributes, 1):
            output += f'A{i}\t{attr.tag} ' + space_join(mappings[x] for x in attr.items) + '\n'

        for i, norm in enumerate(self.normalizations, 1):
            output += f'N{i}\tReference {mappings[norm.entity]} {norm.ontology}:{norm.ont_id}\t{norm.entity.mention}\n'

        return output


class BratDataset:

    def __init__(self, dir_path: PathLike, brat_files: t.List[BratFile]):
        self.directory = Path(dir_path)
        self.brat_files = brat_files

    @classmethod
    def from_directory(cls, dir_path: PathLike) -> BratDataset:
        """
        Automatically creates BratFiles for all the ann files in a given directory when creating the BratDataset.
        """
        directory = Path(dir_path)
        brat_files = [BratFile.from_ann_path(p) for p in directory.iterdir() if p.suffix == '.ann']
        brat_files.sort()
        return cls(directory, brat_files)

    def __iter__(self) -> t.Iterator[BratFile]:
        return iter(self.brat_files)
