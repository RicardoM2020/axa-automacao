"""
Matriz de parâmetros para cálculo de Despesa e % de Indenização.
Chave: (cobertura, status, tipo_finalizacao, tipo_aparelho)
Valor: (valor_despesa, pct_indenizacao)
"""

MATRIZ = {
    # --- Derramamento de Líquido ---
    ("Derramamento de Líquido", "Encerrado", "Sem Atendimento", "CELULAR"):  (88.95,  0),
    ("Derramamento de Líquido", "Encerrado", "Sem Atendimento", "TABLET"):   (127.07, 0),
    ("Derramamento de Líquido", "Indenizado", "Crédito em Conta", "CELULAR"):(88.95,  100),
    ("Derramamento de Líquido", "Indenizado", "Crédito em Conta", "TABLET"): (127.07, 100),
    ("Derramamento de Líquido", "Indenizado", "Reparo",           "CELULAR"):(88.95,  53),
    ("Derramamento de Líquido", "Indenizado", "Reposição",        "CELULAR"):(88.95,  87),
    ("Derramamento de Líquido", "Negado",     "Negado",           "CELULAR"):(88.95,  0),
    ("Derramamento de Líquido", "Negado",     "Negado",           "TABLET"): (127.07, 0),
    ("Derramamento de Líquido", "Negado",     "Sem atendimento",  "CELULAR"):(88.95,  0),

    # --- Extensão da Garantia Original ---
    ("Extensão da Garantia Original", "Encerrado", "Sem Atendimento", "CELULAR"):  (88.95,  0),
    ("Extensão da Garantia Original", "Encerrado", "Sem Atendimento", "TABLET"):   (127.07, 0),
    ("Extensão da Garantia Original", "Indenizado", "Crédito em Conta","CELULAR"): (88.95,  100),
    ("Extensão da Garantia Original", "Indenizado", "Crédito em Conta","NOTEBOOK"):(127.07, 100),
    ("Extensão da Garantia Original", "Indenizado", "Crédito em Conta","TABLET"):  (127.07, 100),
    ("Extensão da Garantia Original", "Indenizado", "Reparo",          "CELULAR"): (88.95,  32),
    ("Extensão da Garantia Original", "Indenizado", "Reparo",          "TABLET"):  (127.07, 32),
    ("Extensão da Garantia Original", "Indenizado", "Reposição",       "CELULAR"): (88.95,  85),
    ("Extensão da Garantia Original", "Indenizado", "Indenizado Via parceiro","CELULAR"):  (88.95,  0),
    ("Extensão da Garantia Original", "Indenizado", "Indenizado Via parceiro","NOTEBOOK"): (127.07, 0),
    ("Extensão da Garantia Original", "Indenizado", "Indenizado Via parceiro","TABLET"):   (127.07, 0),
    ("Extensão da Garantia Original", "Indenizado", "Indenizado Via parceiro","OUTROS"):   (127.07, 0),
    ("Extensão da Garantia Original", "Negado",     "Negado",          "CELULAR"): (88.95,  0),
    ("Extensão da Garantia Original", "Negado",     "Negado",          "TABLET"):  (127.07, 0),
    ("Extensão da Garantia Original", "Negado",     "Negado",          "NOTEBOOK"):(127.07, 0),
    ("Extensão da Garantia Original", "Negado",     "Sem atendimento", "CELULAR"): (88.95,  0),
    ("Extensão da Garantia Original", "Negado",     "Sem atendimento", "TABLET"):  (127.07, 0),

    # --- Quebra Acidental ---
    ("Quebra Acidental", "Encerrado", "Sem Atendimento", "CELULAR"):  (88.95,  0),
    ("Quebra Acidental", "Encerrado", "Sem Atendimento", "TABLET"):   (127.07, 0),
    ("Quebra Acidental", "Indenizado", "Crédito em Conta", "CELULAR"):(88.95,  100),
    ("Quebra Acidental", "Indenizado", "Crédito em Conta", "TABLET"): (127.07, 100),
    ("Quebra Acidental", "Indenizado", "Crédito em Conta", "NOTEBOOK"):(127.07,100),
    ("Quebra Acidental", "Indenizado", "Reparo",           "CELULAR"):(88.95,  53),
    ("Quebra Acidental", "Indenizado", "Reparo",           "TABLET"): (127.07, 53),
    ("Quebra Acidental", "Indenizado", "Reposição",        "CELULAR"):(88.95,  87),
    ("Quebra Acidental", "Indenizado", "Reposição",        "TABLET"): (127.07, 87),
    ("Quebra Acidental", "Negado",     "Negado",           "CELULAR"):(88.95,  0),
    ("Quebra Acidental", "Negado",     "Negado",           "TABLET"): (127.07, 0),
    ("Quebra Acidental", "Negado",     "Negado",           "NOTEBOOK"):(127.07,0),
    ("Quebra Acidental", "Negado",     "Sem atendimento",  "CELULAR"):(88.95,  0),
    ("Quebra Acidental", "Negado",     "Sem atendimento",  "TABLET"): (127.07, 0),

    # --- Roubo e Furto ---
    ("Roubo e Furto", "Encerrado", "Sem Atendimento", "CELULAR"):  (127.07, 0),
    ("Roubo e Furto", "Encerrado", "Sem Atendimento", "TABLET"):   (127.07, 0),
    ("Roubo e Furto", "Indenizado", "Crédito em Conta", "CELULAR"):(127.07, 100),
    ("Roubo e Furto", "Indenizado", "Crédito em Conta", "TABLET"): (127.07, 100),
    ("Roubo e Furto", "Indenizado", "Reposição",        "CELULAR"):(127.07, 86),
    ("Roubo e Furto", "Indenizado", "Reposição",        "TABLET"): (127.07, 86),
    ("Roubo e Furto", "Negado",     "Negado",           "CELULAR"):(127.07, 0),
    ("Roubo e Furto", "Negado",     "Negado",           "TABLET"): (127.07, 0),
    ("Roubo e Furto", "Negado",     "Encerrado",        "CELULAR"):(127.07, 0),

    ("Roubo e Furto", "Indenizado", "Crédito em Conta", "NOTEBOOK"): (127.07, 100),
    ("Roubo e Furto", "Negado",     "Negado",           "NOTEBOOK"): (127.07, 0),
    ("Roubo e Furto", "Encerrado",  "Sem Atendimento",  "NOTEBOOK"): (127.07, 0),

    # --- Roubo ou Subtração Mediante Arrombamento ---
    ("Roubo ou Subtração Mediante Arrombamento", "Indenizado", "Crédito em Conta", "TABLET"):(127.07, 100),
}

# Percentuais especiais por estado do aparelho (aplicados sobre o LMI)
PCT_LIKE_NEW  = 82  # % do LMI — estado "LIKE NEW"
PCT_EXCELENTE = 81  # % do LMI — estado "EXCELENTE"


def buscar_matriz(cobertura: str, status: str, tipo_finalizacao: str, tipo_aparelho: str):
    """
    Retorna (valor_despesa, pct_indenizacao) para a combinação dada.
    Tenta primeiro com tipo_aparelho exato, depois sem aparelho (fallback).
    Retorna None se não encontrar.
    """
    chave = (cobertura, status, tipo_finalizacao, tipo_aparelho)
    resultado = MATRIZ.get(chave)

    if resultado is None:
        # Tenta variações de capitalização no tipo de finalização
        for (cob, sta, fin, apa), val in MATRIZ.items():
            if (cob.strip().lower() == cobertura.strip().lower() and
                sta.strip().lower() == status.strip().lower() and
                fin.strip().lower() == tipo_finalizacao.strip().lower() and
                apa.strip().upper() == tipo_aparelho.strip().upper()):
                resultado = val
                break

    return resultado


def calcular_valores(cobertura: str, status: str, tipo_finalizacao: str,
                     tipo_aparelho: str, lmi: float, estado_aparelho: str = "",
                     pct_franquia: float = 0) -> dict:
    """
    Retorna dict com valor_despesa, pct_indenizacao, valor_indenizacao_correto.
    Fórmula: ARRED(((% Indenização - % Franquia) × LMI) / 100, 2)
    Aplica regras especiais de LIKE NEW e Refurbished.
    """
    estado = (estado_aparelho or "").strip().upper()

    def _calcular(pct: float, descricao: str, valor_despesa: float) -> dict:
        pct_liquido = pct - pct_franquia
        valor = round((pct_liquido * lmi) / 100, 2)
        return {
            "valor_despesa": valor_despesa,
            "pct_indenizacao": pct,
            "pct_franquia": pct_franquia,
            "pct_liquido": pct_liquido,
            "valor_indenizacao_correto": max(valor, 0),
            "regra_aplicada": descricao,
        }

    # Regras especiais por estado do aparelho (apenas Reposição)
    if estado == "LIKE NEW" and tipo_finalizacao == "Reposição":
        resultado_matriz = buscar_matriz(cobertura, status, tipo_finalizacao, tipo_aparelho)
        valor_despesa = resultado_matriz[0] if resultado_matriz else 0
        return _calcular(PCT_LIKE_NEW, f"LIKE NEW -> {PCT_LIKE_NEW}% do LMI", valor_despesa)

    if estado == "EXCELENTE" and tipo_finalizacao == "Reposição":
        resultado_matriz = buscar_matriz(cobertura, status, tipo_finalizacao, tipo_aparelho)
        valor_despesa = resultado_matriz[0] if resultado_matriz else 0
        return _calcular(PCT_EXCELENTE, f"EXCELENTE -> {PCT_EXCELENTE}% do LMI", valor_despesa)

    # Regra padrão: busca na matriz
    resultado_matriz = buscar_matriz(cobertura, status, tipo_finalizacao, tipo_aparelho)
    if resultado_matriz is None:
        return {
            "valor_despesa": 0,
            "pct_indenizacao": 0,
            "pct_franquia": pct_franquia,
            "pct_liquido": 0,
            "valor_indenizacao_correto": 0,
            "regra_aplicada": "NAO ENCONTRADO NA MATRIZ",
        }

    valor_despesa, pct = resultado_matriz
    return _calcular(pct, f"Matriz -> {pct}% LMI", valor_despesa)
