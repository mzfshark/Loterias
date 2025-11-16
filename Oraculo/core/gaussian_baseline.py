import math
from typing import Dict, List, Tuple, Optional


class GaussianBaseline:
    """
    Calcula métricas gaussianas (μ, σ, z, densidade) por jogo.

    Suporte:
    - Jogos de números: Lotofácil (1..25, k=15), MegaSena (1..60, k=6), Quina (1..80, k=5)
    - +Milionária: principais (1..50, k=6) e trevos (1..6, k=2)
    - SuperSete: 7 colunas, dígitos 0..9 (por coluna)

    Entrada esperada: lista de jogos históricos (cada jogo é lista de ints),
    e para SuperSete, cada jogo é lista de 7 dígitos (0..9).
    """

    def __init__(self,
                 game_name: str,
                 number_range: Tuple[int, int],
                 numbers_per_game: int,
                 has_bonus: bool = False,
                 bonus_count: int = 0,
                 bonus_range: Tuple[int, int] = (0, 0)):
        self.game = game_name.lower()
        self.min_n, self.max_n = number_range
        self.k = numbers_per_game
        self.has_bonus = has_bonus
        self.bonus_count = bonus_count
        self.bmin, self.bmax = bonus_range

        # Estruturas de resultados
        self.mu: Dict[str, float] = {}
        self.sigma: Dict[str, float] = {}
        self.z: Dict[str, float] = {}
        self.density: Dict[str, float] = {}

        # Para SuperSete (por coluna)
        self.mu_col: List[Dict[int, float]] = []
        self.sigma_col: List[Dict[int, float]] = []
        self.z_col: List[Dict[int, float]] = []
        self.density_col: List[Dict[int, float]] = []

    @staticmethod
    def _gauss_pdf(z: float, sigma: float) -> float:
        # Se sigma ~ 0, retornar densidade unitária (evita div/0; considera tudo próximo da média)
        if sigma <= 1e-9:
            return 1.0
        return (1.0 / (sigma * math.sqrt(2.0 * math.pi))) * math.exp(-(z * z) / 2.0)

    def fit(self, history: List[List[int]], bonus_history: Optional[List[List[int]]] = None):
        """
        Calcula μ, σ, z e densidade para o jogo informado.
        """
        if self.game == 'supersete':
            self._fit_supersete(history)
            return self

        total_draws = max(1, len(history))
        freq = self._count_main_frequencies(history)
        mu, sigma = self._compute_params(total_draws, self.k, self.min_n, self.max_n)
        self._store_main_params(mu, sigma)
        self._populate_main_metrics(freq, mu, sigma)

        if self.has_bonus and bonus_history:
            self._fit_bonus(bonus_history, total_draws)

        return self

    def _count_main_frequencies(self, history: List[List[int]]) -> Dict[int, int]:
        freq: Dict[int, int] = {n: 0 for n in range(self.min_n, self.max_n + 1)}
        for draw in history:
            for n in draw:
                if self.min_n <= n <= self.max_n:
                    freq[n] += 1
        return freq

    @staticmethod
    def _compute_params(total_draws: int, k: int, min_n: int, max_n: int) -> Tuple[float, float]:
        universe = float(max_n - min_n + 1)
        p = k / universe
        mu = total_draws * p
        sigma = math.sqrt(max(1e-12, total_draws * p * (1.0 - p)))
        return mu, sigma

    def _store_main_params(self, mu: float, sigma: float) -> None:
        self.mu['main'] = mu
        self.sigma['main'] = sigma

    def _populate_main_metrics(self, freq: Dict[int, int], mu: float, sigma: float) -> None:
        for n in range(self.min_n, self.max_n + 1):
            zn = (freq[n] - mu) / sigma if sigma > 0 else 0.0
            self.z[str(n)] = zn
            self.density[str(n)] = self._gauss_pdf(zn, sigma)

    def _fit_bonus(self, bonus_history: List[List[int]], total_draws: int) -> None:
        bf = {t: 0 for t in range(self.bmin, self.bmax + 1)}
        for br in bonus_history:
            for t in br:
                if self.bmin <= t <= self.bmax:
                    bf[t] += 1
        bp = self.bonus_count / float(self.bmax - self.bmin + 1)
        bmu = total_draws * bp
        bsigma = math.sqrt(max(1e-12, total_draws * bp * (1.0 - bp)))
        self.mu['bonus'] = bmu
        self.sigma['bonus'] = bsigma
        for t in range(self.bmin, self.bmax + 1):
            zt = (bf[t] - bmu) / bsigma if bsigma > 0 else 0.0
            self.z[f"bonus:{t}"] = zt
            self.density[f"bonus:{t}"] = self._gauss_pdf(zt, bsigma)

    def _fit_supersete(self, history: List[List[int]]):
        total_draws = max(1, len(history))
        cols = 7
        digits = list(range(10))

        freq_cols = self._count_supersete_frequencies(history, cols)
        mu, sigma = self._compute_supersete_params(total_draws)
        for c in range(cols):
            mu_map, sigma_map, z_map, dens_map = self._build_supersete_column_metrics(freq_cols[c], digits, mu, sigma)
            self.mu_col.append(mu_map)
            self.sigma_col.append(sigma_map)
            self.z_col.append(z_map)
            self.density_col.append(dens_map)

    @staticmethod
    def _count_supersete_frequencies(history: List[List[int]], cols: int) -> List[Dict[int, int]]:
        digits = list(range(10))
        freq_cols: List[Dict[int, int]] = [{d: 0 for d in digits} for _ in range(cols)]
        for draw in history:
            if len(draw) != cols:
                continue
            for c, d in enumerate(draw):
                if 0 <= d <= 9:
                    freq_cols[c][d] += 1
        return freq_cols

    @staticmethod
    def _compute_supersete_params(total_draws: int) -> Tuple[float, float]:
        p = 1.0 / 10.0
        mu = total_draws * p
        sigma = math.sqrt(max(1e-12, total_draws * p * (1.0 - p)))
        return mu, sigma

    def _build_supersete_column_metrics(self, freq_col: Dict[int, int], digits: List[int], mu: float, sigma: float):
        mu_map: Dict[int, float] = {}
        sigma_map: Dict[int, float] = {}
        z_map: Dict[int, float] = {}
        dens_map: Dict[int, float] = {}
        for d in digits:
            z = (freq_col[d] - mu) / sigma if sigma > 0 else 0.0
            mu_map[d] = mu
            sigma_map[d] = sigma
            z_map[d] = z
            dens_map[d] = self._gauss_pdf(z, sigma)
        return mu_map, sigma_map, z_map, dens_map

    # APIs de consulta
    def density_for(self, n: int, is_bonus: bool = False) -> float:
        if self.game == 'supersete':
            # Não aplicável numericamente; usar density_for_col
            return 1.0
        key = f"bonus:{n}" if is_bonus else str(n)
        return self.density.get(key, 1.0)

    def density_for_col(self, col: int, digit: int) -> float:
        if not self.density_col or col < 0 or col >= len(self.density_col):
            return 1.0
        return self.density_col[col].get(digit, 1.0)

    def z_for(self, n: int, is_bonus: bool = False) -> float:
        key = f"bonus:{n}" if is_bonus else str(n)
        return self.z.get(key, 0.0)
