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

    df = df.groupby(['suite', 'run'], as_index=False).agg({'speedup': gmean})
    df = df.pivot(index='suite', columns='run', values='speedup')

    df.to_markdown(sys.stdout)

if __name__ == '__main__':
    main()
