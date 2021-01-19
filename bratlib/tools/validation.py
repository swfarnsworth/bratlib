import argparse
import os
import re

import pandas as pd

from bratlib.data import BratDataset, BratFile, Entity


def _validate_contiguous_entity(ent: Entity, text: str) -> bool:
    a, b = ent.spans[0]
    return ent.mention == text[a:b]


def _validate_noncontiguous_entity(ent: Entity, text: str) -> bool:
    mention = r'\s*'.join(re.escape(text[a:b]) for a, b in ent.spans)
    return bool(re.fullmatch(mention, ent.mention))


def validate_bratfile(ann: BratFile) -> pd.DataFrame:
    text = ann.txt_path.read_text()
    return pd.DataFrame.from_dict(
        {e: (_validate_contiguous_entity if len(e.spans) == 1 else _validate_noncontiguous_entity)(e, text)
         for e in ann.entities},
        orient='index', columns=['match']
    )


def validate_bratdataset(data: BratDataset) -> pd.DataFrame:
    outer_df = pd.DataFrame()
    for ann in data:
        df = validate_bratfile(ann)
        df['file_name'] = ann.ann_path.stem
        df.set_index('file_name', append=True)
        outer_df = outer_df.append(df)
    return outer_df


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
