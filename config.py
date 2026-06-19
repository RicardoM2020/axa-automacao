from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Lote atual
LOTE_ATUAL = "B2B 2.0 Lote 86 GIS"
LOTE_NUMERO = 86

# Período do relatório: hoje até 6 meses atrás
DATA_FIM = datetime.today()
DATA_INICIO = DATA_FIM - timedelta(days=180)

# Caminhos
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Google Sheets
SHEET_ID = os.getenv("SHEET_ID", "1J1FK7oukGdu4nXJnnCmyLeKkUdBDzg5-olv8yovbHtg")
ABA_HIST_FATURADOS = "Hist. Faturados"
ABA_MATRIZ = "Matriz Parametros"
ABA_PREP_LOTE = "Preparação Lote"

# ERP B2B
ERP_URL = "https://erp-b2b.grupopll.com.br/admin/controle-financeiro.php?modulo=FinanceiroRelatorios:PagamentoAxaList"
EMPRESA_ERP = "PLL Inovação"

# Gmail
GMAIL_USER = os.getenv("GMAIL_USER", "r.marques.ricardo100@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_IMAP = "imap.gmail.com"

# Coberturas que devem ser normalizadas para "Quebra Acidental"
COBERTURAS_NORMALIZAR = ["Derramamento de Líquido", "Danos Elétricos", "Danos eletricos"]

# Tipos de aparelho válidos
TIPOS_APARELHO_VALIDOS = ["CELULAR", "TABLET", "NOTEBOOK"]

# Tipos de finalização que permitem faturar despesa
FINALIZACOES_COM_DESPESA = ["Reparo", "Crédito em Conta", "Reposição"]

# Tipos de finalização que NÃO permitem faturar despesa
FINALIZACOES_SEM_DESPESA = ["Negado", "Sem Atendimento", "Sem atendimento"]
