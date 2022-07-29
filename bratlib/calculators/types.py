import typing as t

import pandas as pd

CountsDataFrame = t.NewType('CountsDataFrame', pd.DataFrame)
ScoresDataFrame = t.NewType('ScoresDataFrame', pd.DataFrame)
ConfusionMatrixDataFrame = t.NewType('ConfusionMatrixDataFrame', pd.DataFrame)
