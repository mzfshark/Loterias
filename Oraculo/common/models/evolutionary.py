import random
import copy
from typing import List, Dict


DIGITS = list(range(10))  # 0 a 9
COLS = 7  # Super Sete possui 7 colunas


def initialize_population(size: int) -> List[List[int]]:
    return [[random.choice(DIGITS) for _ in range(COLS)] for _ in range(size)]


def evaluate_fitness(jogo: List[int], freq_data: Dict[str, Dict[int, float]]) -> float:
    score = 0.0
    for idx, digit in enumerate(jogo):
        col_key = f"Coluna{idx+1}"
        score += freq_data.get(col_key, {}).get(digit, 0)
    return score


def mutate(jogo: List[int], mutation_rate: float = 0.1) -> List[int]:
    mutated = jogo.copy()
    for i in range(COLS):
        if random.random() < mutation_rate:
            mutated[i] = random.choice(DIGITS)
    return mutated


def crossover(parent1: List[int], parent2: List[int]) -> List[int]:
    cut = random.randint(1, COLS - 2)
    return parent1[:cut] + parent2[cut:]


def evolve_population(population: List[List[int]], freq_data: Dict[str, Dict[int, float]], generations: int = 50) -> List[List[int]]:
    pop_size = len(population)
    elite_size = max(2, int(0.2 * pop_size))

    for gen in range(generations):
        population.sort(key=lambda x: evaluate_fitness(x, freq_data), reverse=True)
        new_pop = population[:elite_size]

        while len(new_pop) < pop_size:
            parents = random.sample(population[:elite_size], 2)
            child = crossover(parents[0], parents[1])
            child = mutate(child, mutation_rate=0.1)
            new_pop.append(child)

        population = new_pop

    # Ordena por fitness final
    population.sort(key=lambda x: evaluate_fitness(x, freq_data), reverse=True)
    return population[:5]  # Retorna os 5 melhores jogos


if __name__ == '__main__':
    # Exemplo de uso com dados fictícios de frequência
    freq_data_example = {
        f"Coluna{i+1}": {d: random.random() for d in DIGITS} for i in range(COLS)
    }

    pop = initialize_population(100)
    melhores = evolve_population(pop, freq_data_example, generations=20)
    print("Melhores jogos otimizados:")
    for jogo in melhores:
        print(jogo)
