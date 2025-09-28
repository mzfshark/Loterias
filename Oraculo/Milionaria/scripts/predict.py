#!/usr/bin/env python3
"""
Wrapper de execução para a +Milionária.

Instancia o EnhancedMilionariaPredictor e executa a análise completa, salvando
JSON/CSV em Oraculo/Milionaria/predictions.
"""

import os
import sys
import traceback

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.Milionaria.scripts.enhanced_predict import EnhancedMilionariaPredictor


def main() -> int:
    print("\n🚀 Iniciando pipeline de previsão - +Milionária")
    predictor = EnhancedMilionariaPredictor()
    try:
        results = predictor.run_complete_analysis()
        if not results:
            print("⚠️ Nenhum resultado foi gerado.")
            return 2
        print("\n✅ Pipeline +Milionária finalizada com sucesso.")
        return 0
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida pelo usuário.")
        return 130
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
