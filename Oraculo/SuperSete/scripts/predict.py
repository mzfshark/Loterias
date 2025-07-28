import os
import sys
import json
from datetime import datetime
import pandas as pd

# Adiciona raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.SuperSete.models import frequency
from Oraculo.SuperSete.models import poisson
from Oraculo.SuperSete.models import markov
from Oraculo.SuperSete.models import bayesian
from Oraculo.SuperSete.models import evolutionary

# Configs
DATA_PATH = "Oraculo/SuperSete/data/SuperSete.csv"
OUTPUT_PATH = "Oraculo/SuperSete/predictions"

print("\n📊 Carregando dados históricos...")
df = pd.read_csv(DATA_PATH)
assert df.shape[1] == 7, "O dataset deve ter exatamente 7 colunas."
print(f"Linhas carregadas: {len(df)} | Último sorteio: {df.index[-1]}")

# -----------------------------
# Estatísticas
# -----------------------------
print("\n📈 Calculando estatísticas...")
freqs = frequency.calculate_frequency_by_column(df)
poisson_scores = poisson.column_poisson_scores(freqs)
markov_preds = markov.generate_predictions(df)
priors = bayesian.initialize_priors()
bayes_post = bayesian.update_posteriors(priors, df.tail(10))
top_bayes = bayesian.get_top_candidates(bayes_post, top_n=3)

print("\n🎯 Top 3 dígitos por coluna (modelo Bayesiano):")
for col, digs in top_bayes.items():
    print(f"{col}: {digs}")

# -----------------------------
# Geração de apostas
# -----------------------------
print("\n🎰 Gerando apostas...")
freq_apostas = []
for i in range(5):
    jogo = [max(col.items(), key=lambda x: x[1])[0] for col in freqs.values()]
    freq_apostas.append(jogo)

markov_apostas = [[v for v in col.keys()][0] for col in markov_preds.values()]

evo_games = evolutionary.evolve_population(
    evolutionary.initialize_population(50),
    freqs,
    generations=30
)

# -----------------------------
# Salvamento
# -----------------------------
print("\n💾 Salvando apostas...")
today = datetime.now().strftime("%Y-%m-%d")
os.makedirs(OUTPUT_PATH, exist_ok=True)

output = []
for j in freq_apostas:
    output.append({"modelo": "frequencia", "jogo": j})
output.append({"modelo": "markov", "jogo": markov_apostas})
for j in evo_games:
    output.append({"modelo": "evolutivo", "jogo": j})

json_path = os.path.join(OUTPUT_PATH, f"prediction_{today}.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

csv_path = os.path.join(OUTPUT_PATH, f"prediction_{today}.csv")
pd.DataFrame([{**{"col"+str(i+1): num for i, num in enumerate(x['jogo'])}, "modelo": x['modelo']} for x in output]).to_csv(csv_path, index=False)

print(f"\n✅ Previsões salvas:")
print(f"- JSON: {json_path}")
print(f"- CSV : {csv_path}")

print("\n🚀 Pipeline de previsão finalizada com sucesso.")
