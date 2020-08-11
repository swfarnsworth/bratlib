import typing as t
from dataclasses import dataclass

from cached_property import cached_property


@dataclass
class Line:
    start: int
    text: str


class LineList:

    def __init__(self, lines: t.List[Line], text: str):
        self.lines = lines
        self.text = text

    @classmethod
    def from_str(cls, text: str):
        index = 0
        all_lines = []
        for line in text.split('\n'):
            all_lines.append(Line(index, line))
            index += len(line) + 1

        return cls(all_lines, text)

    def __getitem__(self, item):
        return self.lines[item - 1]

    @cached_property
    def _line_iter(self):
        return [range(line.start, line.start + len(line.text)) for line in self.lines]

    def by_index(self, index):
        for r, l in self._line_iter:
            if index in r:
                return l
        raise RuntimeError(f'index value {index} out of range for {self}')
