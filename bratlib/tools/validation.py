import argparse
import os
import typing as t
from functools import reduce
from operator import add

from bratlib.data import BratDataset, BratFile, Entity


def validate_entity(ent: Entity, text: str) -> bool:
    mention_in_text = reduce(add, (text[a:b] for a, b in ent.spans))
    valid = ent.mention == mention_in_text
    if not valid:
        print(ent, mention_in_text)
    return valid


def validate_bratfile(ann: BratFile) -> t.List[bool]:
    with ann.txt_path.open() as f:
        text = f.read()
    return [validate_entity(ent, text) for ent in ann.entities]


def validate_bratdataset(data: BratDataset) -> None:
    for ann in data:
        validate_bratfile(ann)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()

    input_ = args.input

    if os.path.isdir(input_):
        data = BratDataset.from_directory(input_)
        validate_bratdataset(data)
    elif os.path.isfile(input_):
        ann = BratFile.from_ann_path(input_)
        validate_bratfile(ann)
    else:
        raise FileNotFoundError('input is not a file or directory')


if __name__ == '__main__':
    main()
