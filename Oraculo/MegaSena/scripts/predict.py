#!/usr/bin/env python3
"""
Wrapper de execução para a Mega-Sena.

Este script apenas instancia o EnhancedMegaSenaPredictor e executa a
análise completa, salvando os resultados em JSON/CSV no diretório
Oraculo/MegaSena/predictions, conforme esperado pelos workflows e pelo
gerador de HTML unificado.
"""

import os
import sys
import traceback

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.MegaSena.scripts.enhanced_predict import EnhancedMegaSenaPredictor


def main() -> int:
    print("\n🚀 Iniciando pipeline de previsão - Mega-Sena")
    predictor = EnhancedMegaSenaPredictor()
    try:
        results = predictor.run_complete_analysis()
        if not results:
            print("⚠️ Nenhum resultado foi gerado.")
            return 2
        print("\n✅ Pipeline Mega-Sena finalizada com sucesso.")
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
