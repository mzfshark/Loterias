# Smoke test for ModelAdapter
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Oraculo.core.model_adapter import ModelAdapter
from Oraculo.core.lottery_configs import LOTOFACIL_CONFIG

adapter = ModelAdapter(LOTOFACIL_CONFIG)

# synthetic historical data: two simple games
data = [list(range(1,16)), list(range(2,17))]

print('Running adapt_poisson_model...')
res_poisson = adapter.adapt_poisson_model(data)
print('poisson ->', res_poisson)

print('\nRunning adapt_markov_model...')
res_markov = adapter.adapt_markov_model(data)
print('markov ->', res_markov)

print('\nRunning adapt_mutation_model...')
res_mutation = adapter.adapt_mutation_model(data)
print('mutation ->', res_mutation)

print('\nRunning adapt_beam_search_model...')
res_beam = adapter.adapt_beam_search_model(data)
print('beam_search ->', res_beam)

print('\nSmoke test finished')
