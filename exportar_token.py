"""
Exporta o token.pickle como base64 para usar como variável de ambiente no Railway.
Execute uma vez localmente: python exportar_token.py
Cole o valor gerado como GOOGLE_TOKEN no Railway.
"""
import base64
from pathlib import Path

token_path = Path(__file__).parent / "token.pickle"

if not token_path.exists():
    print("token.pickle nao encontrado. Execute o script principal uma vez para gerar.")
else:
    valor = base64.b64encode(token_path.read_bytes()).decode()
    print("\n=== Cole este valor como GOOGLE_TOKEN no Railway ===\n")
    print(valor)
    print("\n====================================================\n")
    print(f"Tamanho: {len(valor)} caracteres")
