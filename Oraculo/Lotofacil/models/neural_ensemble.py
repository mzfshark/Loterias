import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Neural ensemble features will be limited.")


class NeuralEnsembleLotofacil:
    """
    Advanced neural network ensemble for Lotofacil prediction using multiple ML models.
    Combines Random Forest, Gradient Boosting, and Multi-Layer Perceptron.
    """
    
    def __init__(self, ensemble_size: int = 3):
        """
        Initialize the neural ensemble.
        
        Args:
            ensemble_size: Number of models in the ensemble
        """
        self.ensemble_size = ensemble_size
        self.models = []
        self.scalers = []
        self.feature_names = []
        self.is_trained = False
        
        if SKLEARN_AVAILABLE:
            # Initialize different types of models for diversity
            self.models = [
                RandomForestClassifier(n_estimators=100, random_state=42),
                GradientBoostingClassifier(n_estimators=100, random_state=42),
                MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=1000, random_state=42)
            ]
            self.scalers = [StandardScaler() for _ in range(len(self.models))]
    
    def extract_features(self, historical_data: List[List[int]], lookback: int = 10) -> np.ndarray:
        """
        Extract sophisticated features from historical lottery data.
        
        Args:
            historical_data: List of historical games
            lookback: Number of previous games to consider for features
            
        Returns:
            Feature matrix
        """
        features = []
        
        for i in range(lookback, len(historical_data)):
            game_features = []
            
            # Current game for target (we'll predict each number separately)
            current_game = historical_data[i]
            
            # Look at previous games
            prev_games = historical_data[i-lookback:i]
            
            # Feature 1: Frequency of each number in last N games
            all_prev_numbers = [num for game in prev_games for num in game]
            number_freq = Counter(all_prev_numbers)
            for num in range(1, 26):
                game_features.append(number_freq.get(num, 0))
            
            # Feature 2: Recency features (last appearance of each number)
            for num in range(1, 26):
                last_seen = -1
                for j, game in enumerate(reversed(prev_games)):
                    if num in game:
                        last_seen = j
                        break
                game_features.append(last_seen if last_seen != -1 else lookback)
            
            # Feature 3: Pattern features
            # Sum of previous games
            prev_sums = [sum(game) for game in prev_games]
            game_features.extend([
                np.mean(prev_sums),
                np.std(prev_sums),
                np.min(prev_sums),
                np.max(prev_sums)
            ])
            
            # Feature 4: Consecutive number patterns
            consecutive_counts = []
            for game in prev_games:
                sorted_game = sorted(game)
                consecutive = 0
                for k in range(len(sorted_game) - 1):
                    if sorted_game[k+1] - sorted_game[k] == 1:
                        consecutive += 1
                consecutive_counts.append(consecutive)
            
            game_features.extend([
                np.mean(consecutive_counts),
                np.std(consecutive_counts) if len(consecutive_counts) > 1 else 0
            ])
            
            # Feature 5: Distribution features (low, mid, high numbers)
            for game in prev_games[-3:]:  # Last 3 games
                low_count = sum(1 for num in game if num <= 8)
                mid_count = sum(1 for num in game if 9 <= num <= 17)
                high_count = sum(1 for num in game if num >= 18)
                game_features.extend([low_count, mid_count, high_count])
            
            # Feature 6: Even/Odd patterns
            for game in prev_games[-3:]:
                even_count = sum(1 for num in game if num % 2 == 0)
                odd_count = 15 - even_count
                game_features.extend([even_count, odd_count])
            
            features.append(game_features)
        
        return np.array(features)
    
    def prepare_targets(self, historical_data: List[List[int]], lookback: int = 10) -> List[np.ndarray]:
        """
        Prepare target variables for each number position.
        
        Args:
            historical_data: List of historical games
            lookback: Number of previous games used for features
            
        Returns:
            List of target arrays, one for each number (1-25)
        """
        targets = []
        
        # Create binary targets for each number
        for num in range(1, 26):
            num_targets = []
            for i in range(lookback, len(historical_data)):
                current_game = historical_data[i]
                num_targets.append(1 if num in current_game else 0)
            targets.append(np.array(num_targets))
        
        return targets
    
    def train(self, historical_data: List[List[int]], lookback: int = 10):
        """
        Train the ensemble models.
        
        Args:
            historical_data: List of historical games
            lookback: Number of previous games to use for features
        """
        if not SKLEARN_AVAILABLE:
            print("Warning: Cannot train neural ensemble without scikit-learn")
            return
        
        print(f"🧠 Treinando ensemble neural com {len(historical_data)} jogos...")
        
        # Extract features and targets
        X = self.extract_features(historical_data, lookback)
        y_list = self.prepare_targets(historical_data, lookback)
        
        print(f"📊 Features extraídas: {X.shape}")
        
        # Store feature information
        self.feature_names = [f"freq_{i}" for i in range(1, 26)] + \
                           [f"recency_{i}" for i in range(1, 26)] + \
                           ["sum_mean", "sum_std", "sum_min", "sum_max"] + \
                           ["consec_mean", "consec_std"] + \
                           [f"dist_{i}_{j}" for i in range(3) for j in ["low", "mid", "high"]] + \
                           [f"parity_{i}_{j}" for i in range(3) for j in ["even", "odd"]]
        
        # Train models for predicting overall number probabilities
        # We'll aggregate the individual number predictions
        y_aggregated = np.mean([y for y in y_list], axis=0)  # Average across all numbers
        
        model_scores = []
        for i, (model, scaler) in enumerate(zip(self.models, self.scalers)):
            print(f"🔧 Treinando modelo {i+1}/{len(self.models)}: {type(model).__name__}")
            
            # Scale features
            X_scaled = scaler.fit_transform(X)
            
            # Convert to binary classification problem using median split
            median_val = np.median(y_aggregated)
            y_binary = (y_aggregated > median_val).astype(int)
            
            # Check if we have both classes
            if len(np.unique(y_binary)) < 2:
                # Create more balanced binary target using quantiles
                q75 = np.percentile(y_aggregated, 75)
                y_binary = (y_aggregated > q75).astype(int)
                
                # If still only one class, use different approach
                if len(np.unique(y_binary)) < 2:
                    # Use top 40% vs bottom 60%
                    threshold = np.percentile(y_aggregated, 60)
                    y_binary = (y_aggregated > threshold).astype(int)
            
            # Final check - if still one class, skip this model
            if len(np.unique(y_binary)) < 2:
                print(f"  ⚠️ Dados insuficientes para treinamento - pulando modelo")
                model_scores.append(0.5)
                continue
            
            # Train model
            model.fit(X_scaled, y_binary)
            
            # Evaluate with cross-validation
            try:
                scores = cross_val_score(model, X_scaled, y_binary, cv=min(5, len(X_scaled)//2), scoring='accuracy')
                model_scores.append(np.mean(scores))
                print(f"  ✅ Acurácia CV: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
            except Exception as e:
                print(f"  ⚠️ Erro na validação cruzada: {str(e)}")
                model_scores.append(0.5)
        
        self.is_trained = True
        self.model_scores = model_scores
        print(f"✅ Treinamento concluído. Melhor modelo: {np.argmax(model_scores) + 1}")
    
    def predict_probabilities(self, recent_games: List[List[int]], lookback: int = 10) -> Dict[int, float]:
        """
        Predict probabilities for each number using the ensemble.
        
        Args:
            recent_games: Recent games for feature extraction
            lookback: Number of games to look back
            
        Returns:
            Dictionary mapping numbers to their predicted probabilities
        """
        if not SKLEARN_AVAILABLE or not self.is_trained:
            # Fallback to frequency-based prediction
            all_numbers = [num for game in recent_games[-lookback:] for num in game]
            number_freq = Counter(all_numbers)
            total = sum(number_freq.values())
            return {num: number_freq.get(num, 0) / total for num in range(1, 26)}
        
        # Extract features from recent games
        # Create a dummy next game for feature extraction
        extended_games = recent_games + [[]]  # Add empty game to extract features
        X = self.extract_features(extended_games, lookback)
        X_current = X[-1:] if len(X) > 0 else np.zeros((1, len(self.feature_names)))
        
        # Get predictions from each fitted model
        ensemble_predictions = []
        fitted_models = 0
        
        for model, scaler, score in zip(self.models, self.scalers, self.model_scores):
            try:
                # Check if model is fitted
                from sklearn.utils.validation import check_is_fitted
                check_is_fitted(model)
                
                X_scaled = scaler.transform(X_current)
                
                # Get probability predictions
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(X_scaled)[0]
                    # Take probability of positive class
                    prob = probs[1] if len(probs) > 1 else probs[0]
                else:
                    prob = model.predict(X_scaled)[0]
                
                ensemble_predictions.append(prob * score)  # Weight by model performance
                fitted_models += 1
                
            except Exception as e:
                # Model not fitted or other error, skip it
                continue
        
        # If no models are fitted, use frequency fallback
        if fitted_models == 0:
            all_numbers = [num for game in recent_games[-lookback:] for num in game]
            number_freq = Counter(all_numbers)
            total = sum(number_freq.values())
            return {num: number_freq.get(num, 0) / total if total > 0 else 1/25 for num in range(1, 26)}
        
        # Average ensemble predictions
        avg_ensemble_prob = np.mean(ensemble_predictions)
        
        # Convert ensemble prediction to number-specific probabilities
        # Use frequency analysis combined with ensemble insight
        recent_numbers = [num for game in recent_games[-lookback:] for num in game]
        number_freq = Counter(recent_numbers)
        
        probabilities = {}
        for num in range(1, 26):
            base_prob = number_freq.get(num, 0) / len(recent_numbers) if recent_numbers else 1/25
            # Adjust by ensemble prediction
            adjusted_prob = base_prob * (1 + avg_ensemble_prob)
            probabilities[num] = adjusted_prob
        
        # Normalize probabilities
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {num: prob / total_prob for num, prob in probabilities.items()}
        
        return probabilities
    
    def generate_prediction(self, historical_data: List[List[int]], 
                          train_split: float = 0.8, lookback: int = 10) -> Dict:
        """
        Generate prediction using the neural ensemble.
        
        Args:
            historical_data: Historical lottery data
            train_split: Fraction of data to use for training
            lookback: Number of previous games to consider
            
        Returns:
            Dictionary containing predictions and model information
        """
        # Split data for training and recent analysis
        split_idx = int(len(historical_data) * train_split)
        train_data = historical_data[:split_idx]
        recent_data = historical_data[split_idx:]
        
        # Train models if we have enough data
        if len(train_data) > lookback * 2:
            self.train(train_data, lookback)
        
        # Generate predictions
        probabilities = self.predict_probabilities(historical_data, lookback)
        
        # Select top 15 numbers
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        prediction = [num for num, _ in sorted_probs[:15]]
        
        # Calculate confidence score
        top_15_probs = [prob for _, prob in sorted_probs[:15]]
        confidence = np.mean(top_15_probs) / np.mean([prob for _, prob in sorted_probs])
        
        return {
            'prediction': sorted(prediction),
            'probabilities': probabilities,
            'confidence': confidence,
            'model_scores': self.model_scores if self.is_trained else [],
            'top_numbers_with_probs': sorted_probs[:15]
        }

    # ---- Stub mínimo para compatibilidade com o ModelAdapter ----
    def train_and_predict(self, historical_data: List[List[int]], lookback: int = 10):
        """
        Interface simplificada esperada pelo adapter.
        Retorna (prediction, confidence).
        """
        result = self.generate_prediction(historical_data, lookback=lookback)
        return result['prediction'], float(result.get('confidence', 0.6))


def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv') -> List[List[int]]:
    """Load historical Lotofacil data."""
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col]
    return df[colunas].values.tolist()


def gerar_predicao_neural_ensemble(dados: List[List[int]]) -> Dict:
    """
    Generate neural ensemble prediction for Lotofacil.
    
    Args:
        dados: Historical lottery data
        
    Returns:
        Dictionary containing prediction and analysis
    """
    ensemble = NeuralEnsembleLotofacil()
    resultado = ensemble.generate_prediction(dados)
    
    return resultado


if __name__ == '__main__':
    print("🧠 Executando predição com ensemble neural para Lotofacil...")
    
    # Load data
    dados = carregar_dados()
    print(f"📊 Dados carregados: {len(dados)} jogos históricos")
    
    # Generate neural ensemble prediction
    resultado = gerar_predicao_neural_ensemble(dados)
    
    print("\n🎯 Predição do Ensemble Neural:")
    print(f"Números previstos: {resultado['prediction']}")
    print(f"Confiança do modelo: {resultado['confidence']:.4f}")
    
    if resultado['model_scores']:
        print(f"Scores dos modelos: {[f'{score:.4f}' for score in resultado['model_scores']]}")
    
    print("\n📈 Top 15 números com probabilidades:")
    for i, (num, prob) in enumerate(resultado['top_numbers_with_probs']):
        print(f"{i+1:2d}. Número {num:2d}: {prob:.6f}")
    
    print(f"\n🔍 Disponibilidade scikit-learn: {'✅' if SKLEARN_AVAILABLE else '❌'}")