import pandas as pd
import sys
from scipy.stats import gmean

def with_baselines(df: pd.DataFrame) -> pd.DataFrame:
    sel = df.loc[df['run'] == 'baseline', ['suite', 'benchmark', 'result']]
    sel.rename(columns={'result': 'baseline'}, inplace=True)

    return df.merge(sel, on=['suite', 'benchmark'])

def add_speedups(df: pd.DataFrame):
    wb = with_baselines(df)

    df['speedup'] = wb['baseline'] / wb['result']

def main():
    df = pd.read_csv(sys.stdin)

    add_speedups(df)

    df = df[df['run'] != 'baseline'].drop('run', axis=1)
    df = df.groupby('suite').agg(
        min=pd.NamedAgg('speedup', 'min'),
        max=pd.NamedAgg('speedup', 'max'),
        mean=pd.NamedAgg('speedup', gmean)
    )

    df.to_markdown(sys.stdout)

if __name__ == '__main__':
    main()
