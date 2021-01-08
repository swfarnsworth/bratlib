import os
import typing as t
from pathlib import Path
from bratlib.data.file_types import BratFile

_PathLike = t.Union[str, os.PathLike]


class BratDataset:

    def __init__(self, dir_path: _PathLike, brat_files: t.List[BratFile]):
        self.directory = Path(dir_path)
        self.brat_files = brat_files

    @classmethod
    def from_directory(cls, dir_path: _PathLike):
        """
        Automatically creates BratFiles for all the ann files in a given directory when creating the BratDataset.
        """
        directory = Path(dir_path)
        brat_files = [BratFile.from_ann_path(p) for p in directory.iterdir() if p.suffix == '.ann']
        brat_files.sort()
        return cls(directory, brat_files)

    def __iter__(self) -> t.Iterator[BratFile]:
        return iter(self.brat_files)
