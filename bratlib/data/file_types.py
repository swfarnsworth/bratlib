import os
import re
import sys
import typing as t
from pathlib import Path

from cached_property import cached_property

from bratlib.data import _patterns, _utils
from bratlib.data.annotation_types import AnnData, Attribute, Entity, Event, Equivalence, Normalization, Relation

_PathLike = t.Union[str, os.PathLike]
_default_encoding = sys.getdefaultencoding()


class NoTxtError(FileNotFoundError):
    """Raised when a BratFile does not have an associated txt file."""
    pass


class BratParseError(Exception):
    """Raised when an ann file refers to annotations not found elsewhere in the document."""
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

    Accessing the `txt_path` attribute will raise NoTxtError if the instance does not have a txt file.
    """

    def __init__(self, ann_path: _PathLike, txt_path: _PathLike, *, encoding: str = _default_encoding):
        self.ann_path = Path(ann_path)
        self._txt_path = Path(txt_path) if txt_path is not None else None
        self.name = self.ann_path.stem

        self._mapping = {}
        self._encoding = encoding

    def _lookup_from_mapping(self, value: str):
        try:
            return self._mapping[value]
        except KeyError as e:
            new_e = BratParseError(f'An annotation refers to {value}, though this does not appear in the .ann file')
            raise new_e from e

    @classmethod
    def from_ann_path(cls, ann_path: _PathLike, *, encoding: str = _default_encoding):
        """Automatically pairs the ann file with a txt file if one by the same name exists in the directory"""
        ann_path = Path(ann_path)
        possible_txt = Path(str(ann_path).rstrip('ann') + 'txt')
        txt_path = possible_txt if possible_txt.exists() else None
        return cls(ann_path, txt_path, encoding=encoding)

    @classmethod
    def from_data(
        cls,
        entities: t.Optional[t.List[Entity]] = None,
        events: t.Optional[t.List[Event]] = None,
        relations: t.Optional[t.List[Relation]] = None,
        equivalences: t.Optional[t.List[Equivalence]] = None,
        attributes: t.Optional[t.List[Attribute]] = None,
        normalizations: t.Optional[t.List[Normalization]] = None,
        txt_path: t.Optional[_PathLike] = None
    ):
        """
        Creates an instance that does not represent an existing file. All data attributes are blank lists that
        can be mutated. The values for `ann_path` and `name` will belong to `Path` and `str`, respectively,
        but their properties beyond that are not guaranteed.
        """
        new = super().__new__(cls)
        super().__init__(new)
        args = [entities, events, relations, equivalences, attributes, normalizations]
        attrs = ['_entities', '_events', '_relations', '_equivalences', '_attributes', '_normalizations']
        for arg, attr in zip(args, attrs):
            setattr(new, attr, [] if arg is None else arg)
        new._txt_path, new.ann_path, new.name = txt_path, None, 'CREATED_MANUALLY'
        return new

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.name}>'

    @_utils.return_not_implemented
    def __lt__(self, other):
        return self.name < other.name

    @property
    def txt_path(self):
        if self._txt_path is None:
            raise NoTxtError('This BratFile does not have an associated txt file.')
        return self._txt_path

    @txt_path.setter
    def txt_path(self, value):
        self._txt_path = value

    @cached_property
    def _data_dict(self) -> t.Dict[str, t.List[AnnData]]:
        text = self.ann_path.read_text(encoding=self._encoding)
        data_dict = {}

        # Entities
        ent_mapping = {match[1]: Entity._from_re(match) for match in _patterns.ent_pattern.finditer(text)}
        self._mapping.update(ent_mapping)
        data_dict['entities'] = sorted(ent_mapping.values())

        # Events
        events = []

        for m in _patterns.event_pattern.finditer(text):
            trigger = self._lookup_from_mapping(m[3])
            if m[4]:
                items = {n[1].strip(): self._lookup_from_mapping(n[2]) for n in re.finditer(r'([^\t:]+):(T\d+)', m[4])}
            else:
                items = {}
            new_event = Event(m[2], trigger, items)
            self._mapping[m[1]] = new_event
            events.append(new_event)

        data_dict['events'] = sorted(events)

        # Relations
        rels = []

        for match in _patterns.rel_pattern.finditer(text):
            tag = match[1]
            arg1 = self._lookup_from_mapping(match[2])
            arg2 = self._lookup_from_mapping(match[3])
            new_rel = Relation(tag, arg1, arg2)
            rels.append(new_rel)
        data_dict['relations'] = sorted(rels)

        # Equivalences
        equivs = []

        for match in _patterns.equiv_pattern.finditer(text):
            equiv_entities = [self._lookup_from_mapping(e[0]) for e in re.finditer(r'T\d+', match[1])]
            equiv_entities.sort()
            equivs.append(Equivalence(equiv_entities))

        data_dict['equivalences'] = sorted(equivs)

        # Attributes
        attrs = []

        for match in _patterns.attrib_pattern.finditer(text):
            tag = match[1]
            data = [self._lookup_from_mapping(e[0]) for e in re.finditer(r'[ET]\d+', match[2])]
            attrs.append(Attribute(tag, data))

        data_dict['attributes'] = sorted(attrs)

        # Normalizations
        data_dict['normalizations'] = sorted(Normalization(ent_mapping[m[1]], m[2], m[3])
                                             for m in _patterns.norm_pattern.finditer(text))

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
            output += f'E{i}\t{event.event_type}:{mappings[event.trigger]}' + \
                      (' ' if event.arguments.items() else '') + \
                      space_join(f'{k}:{mappings[v]}' for k, v in event.arguments.items()) + '\n'

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
