import math
from collections import defaultdict
from typing import Dict


def calculate_lambda(freq_dict: Dict[str, Dict[int, int]]) -> Dict[str, float]:
    """
    Calcula a média lambda (λ) de ocorrência de dígitos por coluna.
    """
    lambda_dict = {}
    for col, counts in freq_dict.items():
        total_freq = sum(counts.values())
        lambda_dict[col] = total_freq / 10  # 10 dígitos (0 a 9)
    return lambda_dict


def poisson_probability(k: int, lam: float) -> float:
    """
    Calcula a probabilidade de ocorrência de k eventos com média lambda usando Poisson.
    """
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def column_poisson_scores(freq_dict: Dict[str, Dict[int, int]]) -> Dict[str, Dict[int, float]]:
    """
    Calcula a probabilidade de ocorrência P(x=k) para cada dígito em cada coluna com base em Poisson.
    """
    lambda_dict = calculate_lambda(freq_dict)
    scores = defaultdict(dict)
    for col, counts in freq_dict.items():
        lam = lambda_dict[col]
        for digit, freq in counts.items():
            scores[col][digit] = round(poisson_probability(freq, lam), 6)
    return dict(scores)


if __name__ == '__main__':
    # Exemplo fictício
    freq_example = {
        'Coluna1': {0: 5, 1: 10, 2: 8, 3: 12, 4: 7, 5: 9, 6: 6, 7: 13, 8: 4, 9: 6},
        'Coluna2': {0: 7, 1: 11, 2: 5, 3: 9, 4: 6, 5: 12, 6: 4, 7: 8, 8: 3, 9: 5},
    }
    lambdas = calculate_lambda(freq_example)
    scores = column_poisson_scores(freq_example)

    print("Lambdas por coluna:")
    print(lambdas)

    print("\nScores de Poisson por coluna e dígito:")
    for col, probs in scores.items():
        print(f"{col}: {probs}")
