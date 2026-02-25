#!/usr/bin/env python3
"""
Script para verificar e diagnosticar a configuração do workflow publish.yml
"""

import yaml
import os
from pathlib import Path

def check_workflow_names():
    """Verifica se os nomes dos workflows estão corretos"""
    
    workflows_dir = Path(".github/workflows")
    publish_yml = workflows_dir / "publish.yml"
    
    print("🔍 Verificando configuração dos workflows...\n")
    
    # Lê o publish.yml
    with open(publish_yml, 'r', encoding='utf-8') as f:
        publish_config = yaml.safe_load(f)
    
    # Extrai os nomes dos workflows que o publish.yml está esperando
    expected_workflows = publish_config['on']['workflow_run']['workflows']
    print(f"📋 Workflows esperados no publish.yml:")
    for workflow in expected_workflows:
        print(f"   - {workflow}")
    print()
    
    # Verifica os nomes reais dos workflows
    actual_workflows = {}
    workflow_files = [
        "lotofacil.yml",
        "supersete.yml", 
        "megasena.yml",
        "quina.yml",
        "milionaria.yml"
    ]
    
    print("📂 Nomes reais dos workflows:")
    for file in workflow_files:
        file_path = workflows_dir / file
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                actual_name = config.get('name', 'NOME_NÃO_ENCONTRADO')
                actual_workflows[file] = actual_name
                print(f"   {file}: '{actual_name}'")
        else:
            print(f"   {file}: ❌ ARQUIVO NÃO ENCONTRADO")
    print()
    
    # Compara os nomes
    print("🔍 Comparação:")
    all_match = True
    for expected in expected_workflows:
        found = False
        for file, actual in actual_workflows.items():
            if actual == expected:
                print(f"   ✅ '{expected}' encontrado em {file}")
                found = True
                break
        if not found:
            print(f"   ❌ '{expected}' NÃO ENCONTRADO em nenhum arquivo")
            all_match = False
    
    print()
    if all_match:
        print("🎉 Todos os nomes de workflows estão corretos!")
    else:
        print("⚠️  Há inconsistências nos nomes dos workflows.")
        print("💡 O publish.yml só será disparado se os nomes coincidirem exatamente.")
    
    return all_match

def check_trigger_logic():
    """Explica a lógica de acionamento do workflow"""
    
    print("\n" + "="*60)
    print("📖 LÓGICA DE ACIONAMENTO DO HTML PUBLISHER")
    print("="*60)
    
    print("""
🎯 **Como o publish.yml é disparado:**

1. **Trigger Principal**: workflow_run
   - Monitora workflows específicos: Lotofacil, SuperSete, MegaSena, Quina, +Milionaria
   - Tipo: completed (quando qualquer um desses workflows termina)
   - Branch: main (só funciona no branch main)

2. **Condição de Execução**: 
   - IF: github.event.workflow_run.conclusion == 'success'
   - OU: github.event_name == 'workflow_dispatch' (execução manual)
   - Só executa se o workflow anterior teve SUCESSO

3. **Trigger Manual**: workflow_dispatch
   - Permite execução manual via interface do GitHub
   - Útil para testes e debugging

⚠️  **Possíveis Problemas:**
   - Nomes de workflows incorretos (mais comum)
   - Workflow anterior falhou (conclusion != 'success')
   - Branch diferente de 'main'
   - Permissões insuficientes
   - Concorrência (cancel-in-progress: true)

🔧 **Para Debug:**
   - Execute manualmente via workflow_dispatch
   - Verifique logs dos workflows anteriores
   - Confirme que estão executando no branch main
   - Verifique se os workflows anteriores terminam com sucesso
""")

if __name__ == "__main__":
    os.chdir("/mnt/d/Rede/Github/mzfshark/Loterias")
    
    try:
        names_ok = check_workflow_names()
        check_trigger_logic()
        
        if names_ok:
            print("\n✅ Configuração parece estar correta!")
            print("💡 Se o publish.yml ainda não executar, verifique:")
            print("   1. Se os workflows estão executando no branch 'main'")
            print("   2. Se os workflows anteriores terminam com sucesso")
            print("   3. Execute manualmente via workflow_dispatch para testar")
        else:
            print("\n❌ Corrija os nomes dos workflows primeiro!")
            
    except Exception as e:
        print(f"❌ Erro ao verificar configuração: {e}")
        print("💡 Execute este script na raiz do repositório")