# bratlib

Bratlib is a library for natural language processing data facilitation with the [brat standoff format](https://brat.nlplab.org/standoff.html) of text annotations.
At the core of this library are classes that represent individual annotations, documents as a whole, and data sets as a whole.
These classes can be used as-is or can be extended for different use cases, while providing a format that can be shared
between NLP libraries as part of a larger end-to-end solution.

Bratlib also contains tools for analyzing document annotations, including calculators for binary classification scores.
These are available as importable functions or as command line tools.
 