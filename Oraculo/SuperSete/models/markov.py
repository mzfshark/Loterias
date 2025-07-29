import pandas as pd
from collections import defaultdict
from typing import Dict


def build_transition_matrix(df: pd.DataFrame) -> Dict[str, Dict[int, Dict[int, float]]]:
    """
    Constrói a matriz de transição de 1ª ordem por coluna.
    Retorna um dicionário: {coluna: {from_digit: {to_digit: probabilidade}}}
    """
    transitions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for col in df.columns:
        col_data = df[col].astype(int).tolist()
        for i in range(len(col_data) - 1):
            from_d = col_data[i]
            to_d = col_data[i + 1]
            transitions[col][from_d][to_d] += 1

    # Normaliza para probabilidades
    result = {}
    for col, from_map in transitions.items():
        result[col] = {}
        for from_d, to_map in from_map.items():
            total = sum(to_map.values())
            result[col][from_d] = {
                to_d: round(count / total, 4) for to_d, count in to_map.items()
            }

    return result


def predict_next_digit(transitions: Dict[int, Dict[int, float]], last_digit: int) -> Dict[int, float]:
    """
    Retorna as probabilidades dos próximos dígitos com base no último observado.
    """
    return transitions.get(last_digit, {})


def generate_predictions(df: pd.DataFrame) -> Dict[str, Dict[int, float]]:
    """
    Para cada coluna, prevê o próximo dígito baseado no último valor da série e na matriz de transição.
    """
    transition_matrix = build_transition_matrix(df)
    predictions = {}

    last_row = df.tail(1).astype(int)
    for col in df.columns:
        last_digit = int(last_row[col].values[0])
        prediction = predict_next_digit(transition_matrix[col], last_digit)
        predictions[col] = prediction

    return predictions


if __name__ == '__main__':
    # Exemplo de uso
    data = pd.DataFrame({
        'Coluna1': [1, 2, 3, 4, 5],
        'Coluna2': [0, 1, 0, 1, 0],
        'Coluna3': [9, 8, 7, 6, 5],
        'Coluna4': [2, 2, 3, 3, 4],
        'Coluna5': [1, 3, 1, 3, 1],
        'Coluna6': [4, 4, 4, 4, 4],
        'Coluna7': [0, 2, 4, 6, 8],
    })

    transitions = build_transition_matrix(data)
    preds = generate_predictions(data)

    print("\nMatriz de transição (resumo):")
    for col, trans in transitions.items():
        print(f"{col}: {trans}")

    print("\nPrevisões para próxima linha:")
    for col, probs in preds.items():
        print(f"{col}: {probs}")
