# Shared (generic) Bayesian predictor, parametrized by LotteryConfig-like attributes.
# For now, we lightly wrap the Lotofacil class to keep behavior identical and
# allow smooth migration. Game-level modules can import from this shared path.

from Oraculo.Lotofacil.models.bayesian import BayesianLotofacilPredictor as BayesianPredictor
