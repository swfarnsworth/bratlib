import argparse
import re
import typing as t
from collections import namedtuple
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from bratlib.converters import Line, LineList
from bratlib.data import Relation, BratFile
from bratlib.data.extensions.instance import ContigEntity

con_pattern = re.compile(r"c=\"(.+?)\" (\d+):(\d+) (\d+):(\d+)\|\|t=\"(.+?)\"")
whitespace_pattern = re.compile(r'\s+')


@dataclass(eq=True, frozen=True)
class ConEntity:
    mention: str
    start_line: int
    start_token: int
    end_line: int
    end_token: int
    tag: str


def _create_con_list(con_doc: str) -> t.Iterator[ConEntity]:
    for m in con_pattern.finditer(con_doc):
        yield ConEntity(m[1], int(m[2]), int(m[3]), int(m[4]), int(m[5]), m[6])


def convert_con(con: ConEntity, lines: LineList) -> ContigEntity:
    line: Line = lines[con.start_line]
    first_token = con.mention.split()[0]
    first_match = None
    for m in re.finditer(re.escape(first_token), line.text, re.IGNORECASE):
        start = m.start()
        if len(whitespace_pattern.findall(line.text[:start])) == con.start_token:
            first_match = m
            break

    assert first_match is not None

    if (con.start_line, con.start_token) == (con.end_line, con.end_token):
        start += line.start
        end = line.start + first_match.end()
        mention = lines.text[start:end].replace('\n', ' ')
        return ContigEntity(con.tag, [(start, end)], mention)

    line: Line = lines[con.end_line]
    last_token = con.mention.split()[-1]
    for m in re.finditer(re.escape(last_token), line.text, re.IGNORECASE):
        end = m.end()
        if len(whitespace_pattern.findall(line.text[:m.start()])) == con.end_token:
            break

    start += lines[con.start_line].start
    end += lines[con.end_line].start

    mention = lines.text[start:end].replace('\n', ' ')

    return ContigEntity(con.tag, [(start, end)], mention)


rel_pattern = re.compile(r'c="([^"]*)" (\d+):(\d+) (\d+):(\d+)\|\|r="([^"]*)"\|\|c="([^"]*)" (\d+):(\d+) (\d+):(\d+)')

_ConRelCon = namedtuple('ConRelCon', 'start_line start_token end_line end_token')
_ConRelation = namedtuple('ConRelation', 'rel arg1 arg2')


def _create_rel_list(rel_doc: str) -> t.Iterator[_ConRelation]:
    for m in rel_pattern.finditer(rel_doc):
        arg1 = _ConRelCon(*[int(i) for i in m[2:5]])
        arg2 = _ConRelCon(*[int(i) for i in m[8:11]])
        yield _ConRelation(m[6], arg1, arg2)


def convert_rel(rel: _ConRelation, lines: LineList, ents: t.Dict[t.Tuple[int, int], ConEntity]) -> Relation:
    rel_type = rel.rel
    con_a, con_b = rel.arg1, rel.arg2

    fake_arg1 = ConEntity('NULL', con_a.start_line, con_a.start_token, con_a.end_line, con_a.end_token, 'NULL')
    arg1 = convert_con(fake_arg1, lines)
    with suppress(KeyError):
        arg1 = ents[arg1.start, arg1.end]

    fake_arg2 = ConEntity('NULL', con_b.start_line, con_b.start_token, con_b.end_line, con_b.end_token, 'NULL')
    arg2 = convert_con(fake_arg2, lines)
    with suppress(KeyError):
        arg2 = ents[arg2.start, arg2.end]

    return Relation(rel_type, arg1, arg2)


def _switch_extension(path: Path, new_extension: str) -> Path:
    return Path(str(path).replace('.txt', '.' + new_extension))


def convert_directory(path: Path):
    files = list(path.iterdir())
    txt_files = [f for f in files if f.suffix == '.txt']

    for tf in txt_files:

        new_ann = BratFile.from_data()

        with tf.open() as f:
            text = f.read()

        lines = LineList.from_str(text)

        con_path = _switch_extension(tf, 'con')
        if not con_path.exists():
            continue

        with con_path.open() as f:
            con_text = f.read()

        con_generator = _create_con_list(con_text)
        new_ann._entities = [convert_con(c, lines) for c in con_generator]

        rel_path = _switch_extension(tf, 'rel')
        if rel_path.exists():
            ent_dict = {(e.start, e.end): e for e in new_ann.entities}

            with rel_path.open() as f:
                rel_text = f.read()

            rel_generator = _create_rel_list(rel_text)
            new_ann._relations = [convert_rel(rel, lines, ent_dict) for rel in rel_generator]

        ast_path = _switch_extension(tf, 'ast')
        if ast_path.exists():
            pass

        print(new_ann)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory')
    parser.add_argument('output_directory')
    args = parser.parse_args()

    convert_directory(Path(args.input_directory))


if __name__ == '__main__':
    main()
