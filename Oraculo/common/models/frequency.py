import pandas as pd
from collections import defaultdict
from typing import Dict

try:
    from ...core.gaussian_baseline import GaussianBaseline
    _GAUSS_AVAILABLE = True
except Exception:
    _GAUSS_AVAILABLE = False


def calculate_frequency_by_column(df: pd.DataFrame) -> dict:
    """
    Calcula a frequência absoluta dos dígitos (0 a 9) em cada uma das 7 colunas do Super Sete.
    """
    freq_dict = defaultdict(lambda: defaultdict(int))

    for col in df.columns:
        for digit in df[col]:
            freq_dict[col][int(digit)] += 1

    return {col: dict(digs) for col, digs in freq_dict.items()}


def normalize_frequency(freq_dict: dict) -> dict:
    """
    Converte a frequência absoluta em relativa (%), com 4 casas decimais por coluna.
    """
    norm_dict = {}

    for col, digit_counts in freq_dict.items():
        total = sum(digit_counts.values())
        norm_dict[col] = {
            digit: round(count / total, 4)
            for digit, count in digit_counts.items()
        }

    return norm_dict


def apply_gaussian_prior_supersete(norm_freq: dict, gaussian: 'GaussianBaseline') -> dict:
    """
    Repondera a frequência relativa por coluna (SuperSete) usando densidade Gaussiana da baseline.
    Espera `gaussian.density_col` preenchido por coluna (0..6) e dígitos (0..9).
    Retorna novo dicionário de frequências relativas reponderadas e renormalizadas por coluna.
    """
    if not _GAUSS_AVAILABLE or gaussian is None or not getattr(gaussian, 'density_col', None):
        return norm_freq

    out: Dict[str, Dict[int, float]] = {}
    # As chaves de norm_freq são nomes de colunas; mapeamos por índice
    columns = list(norm_freq.keys())
    for idx, col in enumerate(columns):
        digit_probs = norm_freq[col]
        # Aplica densidade por dígito
        reweighted = {d: float(digit_probs.get(d, 0.0)) * float(gaussian.density_col[idx].get(d, 1.0)) for d in digit_probs}
        s = sum(reweighted.values())
        if s > 0:
            reweighted = {d: v / s for d, v in reweighted.items()}
        out[col] = reweighted
    return out


if __name__ == '__main__':
    # Exemplo de uso
    df = pd.DataFrame({
        'Coluna1': [1, 2, 2, 3, 1],
        'Coluna2': [0, 1, 0, 0, 9],
        'Coluna3': [5, 5, 5, 6, 6],
        'Coluna4': [7, 8, 8, 8, 7],
        'Coluna5': [3, 3, 2, 2, 1],
        'Coluna6': [4, 4, 4, 4, 4],
        'Coluna7': [9, 9, 9, 8, 7],
    })
    abs_freq = calculate_frequency_by_column(df)
    rel_freq = normalize_frequency(abs_freq)

    print("Frequência Absoluta:")
    print(abs_freq)

    print("\nFrequência Relativa:")
    print(rel_freq)
