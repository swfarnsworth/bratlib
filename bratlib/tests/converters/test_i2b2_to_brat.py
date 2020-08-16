import unittest
from bratlib.data import Entity, Relation
from bratlib.data.extensions.instance import ContigEntity
from bratlib.converters.i2b2_to_brat import ConEntity, convert_con
from bratlib.converters import LineList


source_text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Quisque lorem nibh, molestie et varius accumsan, ultrices id quam.
Phasellus sed vulputate lacus.
Mauris nec elementum felis, et sollicitudin nunc.
Maecenas a tortor ac ipsum lacinia lobortis in eu augue.
Quisque efficitur eros quis mollis porta.
Fusce eget orci lorem.
Donec vitae arcu dolor.
Ut faucibus feugiat risus a vehicula.
"""

brat_ents = [
    ContigEntity('A', [(6, 11)], 'ipsum'),
    ContigEntity('B', [(28, 39)], 'consectetur'),
    ContigEntity('A', [(81, 94)], 'stie et vari'),
    ContigEntity('B', [(141, 145)], 'put')
]

brat_rels = [
    Relation('AB', brat_ents[0], brat_ents[1]),
    Relation('AB', brat_ents[2], brat_ents[3]),
]

con_ents = [
    ConEntity('ipsum', 1, 1, 1, 1, 'A'),
    ConEntity('consectetur', 1, 5, 1, 5, 'B'),
    ConEntity('stie et vari', 2, 3, 2, 5, 'A'),
    ConEntity('put', 3, 2, 3, 2, 'B')
]


class MyTestCase(unittest.TestCase):

    def test_something(self):
        lines = LineList.from_str(source_text)
        result = [convert_con(c, lines) for c in con_ents]
        self.assertListEqual(result, brat_ents)


if __name__ == '__main__':
    unittest.main()
