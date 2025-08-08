import pandas as pd
from collections import defaultdict

DIGITS = list(range(10))
COLS = 7


def initialize_priors():
    priors = {}
    for i in range(COLS):
        col_key = f"Coluna{i+1}"
        priors[col_key] = {d: 1/10 for d in DIGITS}
    return priors


def update_posteriors(priors, evidence: pd.DataFrame):
    posteriors = defaultdict(lambda: defaultdict(float))

    # Count occurrences from evidence
    for idx in range(COLS):
        col_key = f"Coluna{idx+1}"
        col_data = evidence.iloc[:, idx]
        counts = col_data.value_counts().to_dict()
        total = sum(counts.values())

        # Add evidence to priors
        for digit in DIGITS:
            posteriors[col_key][digit] = priors[col_key][digit] + counts.get(digit, 0)

        # Normalize
        col_total = sum(posteriors[col_key].values())
        for digit in DIGITS:
            posteriors[col_key][digit] /= col_total

    return posteriors


def get_top_candidates(posteriors: dict, top_n: int = 3):
    top_digits = {}
    for col_key, dist in posteriors.items():
        sorted_d = sorted(dist.items(), key=lambda x: x[1], reverse=True)
        top_digits[col_key] = [d for d, _ in sorted_d[:top_n]]
    return top_digits


if __name__ == '__main__':
    # Simulação simples
    data = pd.DataFrame({f"Coluna{i+1}": [0,1,2,3,4,5,6,7,8,9] for i in range(COLS)})
    priors = initialize_priors()
    post = update_posteriors(priors, data)
    top = get_top_candidates(post)
    print("Top candidatos por coluna:")
    print(top)
