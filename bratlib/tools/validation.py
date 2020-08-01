import argparse
import os
from operator import add
from functools import reduce

from bratlib.data import BratDataset, BratFile


def validate_ann(ann: BratFile) -> None:
    with ann.txt_path.open() as f:
        text = f.read()

    for ent in ann.entities:
        mention_in_text = reduce(add, (text[a:b] for a, b in ent.spans))

        if mention_in_text != ent.mention:
            print(ent, mention_in_text)


def validate_dataset(data: BratDataset) -> None:
    for ann in data:
        validate_ann(ann)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()

    input_ = args.input

    if os.path.isdir(input_):
        data = BratDataset.from_directory(input_)
        validate_dataset(data)
    elif os.path.isfile(input_):
        ann = BratFile.from_ann_path(input_)
        validate_ann(ann)
    else:
        raise FileNotFoundError('input is not a file or directory')


if __name__ == '__main__':
    main()
