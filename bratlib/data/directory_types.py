import os
import typing as t
from pathlib import Path
from bratlib.data.file_types import BratFile

_PathLike = t.Union[str, os.PathLike]


class BratDataset:
    """
    A BratDataset represents a collection of BratFiles, and usually represents a specific directory on a file system.

    :ivar directory: the pathlib.Path of the directory this BratDataset represents.
    :ivar brat_files: List[BratFile] of the BratFiles in that directory, or which this instance is otherwise meant to
    represent.
    """

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
