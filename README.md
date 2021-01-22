# bratlib

Bratlib is a library for natural language processing data facilitation with the [brat standoff format](https://brat.nlplab.org/standoff.html) of text annotations.
At the core of this library are classes that represent individual annotations, documents as a whole, and data sets as a whole.
These classes can be used as-is or can be extended for different use cases, while providing a format that can be shared
between NLP libraries as part of a larger end-to-end solution.

Bratlib also contains tools for analyzing document annotations, including calculators for binary classification scores.
These are available as importable functions or as command line tools.

## Usage

The primary data facilitation classes are defined in `bratlib.data`

* `BratDataset` represents a directory containing ann and txt files. The constructor `BratDataset.from_directory(dir_path)` with automatically read the directory and pair any matching ann and txt files into `BratFile` instances. `BratDataset` instances are iterables of `BratFile` instances.
* `BratFile` represents an individual ann file and its respective txt file, if it exists. The constructor `BratFile.from_ann_path(ann_path)` will handle finding the txt file. `BratFile` instances search the ann file they represent for all their entries that are formatted correctly.

## Example
Consider `example.ann`
```
T1  A 1 2  lorem
T2  B 3 5;5 6  ipsum
R1  C Arg1:T1 Arg2:T2
```

```python
>>> from bratlib import data as bd
>>> ann = bd.BratFile.from_ann_path('example.ann')
>>> list(ann.entities)
[bd.Entity(tag='A', spans=[(1, 2)], mention='lorem'), bd.Entity(tag='B', spans=[(3, 5), (5, 6)], mention='ipsum')]
>>> list(ann.relations)
[bd.Relation(relation='C', arg1=bd.Entity(tag='A', spans=[(1, 2)], mention='lorem'), arg2=bd.Entity(tag='B', spans=[(3, 5), (5, 6)], mention='ipsum'))]
```
