import argparse
import re

import pandas as pd

from bratlib.data import BratDataset, BratFile, Entity


def _validate_contiguous_entity(ent: Entity, text: str) -> bool:
    a, b = ent.spans[0]
    return ent.mention == text[a:b]


def _validate_noncontiguous_entity(ent: Entity, text: str) -> bool:
    mention = r'\s*'.join(re.escape(text[a:b]) for a, b in ent.spans)
    return bool(re.fullmatch(mention, ent.mention))


def validate_bratfile_entities(ann: BratFile) -> pd.DataFrame:
    """
    Validates that the mentions given for each entity align with the given character spans.
    For non-contiguous spans, the number of whitespace characters between subspans in the brat file don't count.
    Returns a DataFrame of bd.Entity -> bool.
    """
    text = ann.txt_path.read_text()
    df = pd.DataFrame.from_dict(
        {e: (_validate_contiguous_entity if len(e.spans) == 1 else _validate_noncontiguous_entity)(e, text)
         for e in ann.entities},
        orient='index', columns=['match']
    )
    df.index.rename('entity', inplace=True)
    return df


def validate_bratdataset_entities(data: BratDataset) -> pd.DataFrame:
    """
    Validates that mentions align with the given spans for a whole dataset.
    Returns a DataFrame of (bd.Entity, str) -> bool, where the str is the name of the file
    in which the entity appears.
    """
    outer_df = pd.DataFrame()
    for ann in data:
        df = validate_bratfile_entities(ann)
        df['file_name'] = ann.ann_path.stem
        outer_df = outer_df.append(df.set_index('file_name', append=True))
    return outer_df


def main():
    FILE, DIR = 'file', 'dir'
    ENTITY = 'entity'

    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to the target file or directory')
    parser.add_argument('scope', help='Whether the path is a file or a directory', choices=[FILE, DIR])
    parser.add_argument('validation_type',
                        help='Type of validation to perform (only entity is supported currently)',
                        default=ENTITY, choices=[ENTITY])

    args = parser.parse_args()

    if args.scope == DIR:
        validation = validate_bratdataset_entities(BratDataset.from_directory(args.path))
    else:
        validation = validate_bratfile_entities(BratFile.from_ann_path(args.path))

    if validation['match'].all():
        print(f'All entities valid in {args.path}.')
    else:
        print(validation[~validation['match']].to_csv(columns=[]))


if __name__ == '__main__':
    main()
