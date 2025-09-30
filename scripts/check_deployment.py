#!/usr/bin/env python3
"""
Script para verificar a saúde do deployment do GitHub Pages
"""

import requests
import sys
import time
from urllib.parse import urljoin

def check_pages_deployment(base_url: str, max_retries: int = 5) -> bool:
    """Verifica se o GitHub Pages está funcionando corretamente"""
    
    endpoints = [
        "",  # index.html
        "styles.css",
    ]
    
    print(f"🔍 Verificando deployment em: {base_url}")
    
    for retry in range(max_retries):
        try:
            for endpoint in endpoints:
                url = urljoin(base_url, endpoint)
                print(f"📡 Testando: {url}")
                
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ {endpoint or 'index.html'}: OK ({len(response.content)} bytes)")
                elif response.status_code == 404 and endpoint == "styles.css":
                    print(f"⚠️ {endpoint}: Não encontrado (opcional)")
                else:
                    print(f"❌ {endpoint or 'index.html'}: Status {response.status_code}")
                    return False
            
            print("🎉 Todos os endpoints estão funcionando!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Tentativa {retry + 1}/{max_retries} falhou: {e}")
            if retry < max_retries - 1:
                print("⏳ Aguardando 30 segundos...")
                time.sleep(30)
    
    return False

if __name__ == "__main__":
    import os
    
    # Pega URL do GitHub Pages das variáveis de ambiente
    repo = os.environ.get("GITHUB_REPOSITORY", "mzfshark/Loterias")
    owner = repo.split("/")[0]
    repo_name = repo.split("/")[1]
    
    pages_url = f"https://{owner}.github.io/{repo_name}/"
    
    if check_pages_deployment(pages_url):
        print("✅ Deployment verificado com sucesso!")
        sys.exit(0)
    else:
        print("❌ Falha na verificação do deployment")
        sys.exit(1)