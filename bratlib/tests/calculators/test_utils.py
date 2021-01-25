import pandas as pd

from bratlib.calculators._utils import calculate_scores

df = pd.DataFrame.from_dict({
    'A': [1, 1, 1, 1],
    'B': [1, 2, 3, 4],
    'C': [5, 6, 7, 8]
}, columns=['tp', 'fp', 'tn', 'fn'], orient='index')


def test_calculate_scores():
    expected = pd.DataFrame.from_dict({
        'A': [1/2, 1/2, .5],
        'B': [1/3, 1/5, .25],
        'C': [5/11, 5/13, .416666]
    }, columns=['precision', 'recall', 'f1'], orient='index')
    actual = calculate_scores(df)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False)


def test_calculate_scores_macro():
    expected = pd.DataFrame.from_dict({
        'A': [1 / 2, 1 / 2, .5],
        'B': [1 / 3, 1 / 5, .25],
        'C': [5 / 11, 5 / 13, .416666],
        '(macro)': [0.4292929292929293, 0.36153846153846153, 0.38888866666666666]
    }, columns=['precision', 'recall', 'f1'], orient='index')
    actual = calculate_scores(df, macro=True)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False)


def test_calculate_scores_micro():
    expected = pd.DataFrame.from_dict({
        'A': [1 / 2, 1 / 2, .5],
        'B': [1 / 3, 1 / 5, .25],
        'C': [5 / 11, 5 / 13, .416666],
        '(micro)': [0.4375, 0.35, 0.38888888888888884]
    }, columns=['precision', 'recall', 'f1'], orient='index')
    actual = calculate_scores(df, micro=True)
    pd.testing.assert_frame_equal(expected, actual, check_dtype=False)
