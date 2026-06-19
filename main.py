"""
Automação AXA — Ponto de entrada principal.
Executa o fluxo completo: extração ERP → processamento → geração do lote.

Uso:
    python main.py                  # Fluxo completo (extrai do ERP + processa)
    python main.py --so-processar   # Usa arquivo ERP já baixado (sem abrir navegador)
    python main.py --arquivo relatorio.xlsx  # Processa arquivo específico
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

from config import OUTPUT_DIR, LOTE_ATUAL


def main():
    parser = argparse.ArgumentParser(description="Automação de Faturamento AXA — PLL Inovação")
    parser.add_argument("--so-processar", action="store_true",
                        help="Pula a extração do ERP e usa o último arquivo baixado")
    parser.add_argument("--arquivo", type=str, default=None,
                        help="Caminho para arquivo ERP já baixado (.xlsx)")
    parser.add_argument("--sem-sheets", action="store_true",
                        help="Não lê/escreve no Google Sheets (usa histórico vazio)")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  AUTOMAÇÃO AXA — {LOTE_ATUAL}")
    print(f"  {datetime.today().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)

    # --- ETAPA 1: Extração do ERP ---
    arquivo_erp = None

    if args.arquivo:
        arquivo_erp = Path(args.arquivo)
        print(f"\n[1/4] Usando arquivo informado: {arquivo_erp}")
    elif args.so_processar:
        arquivo_erp = _ultimo_arquivo_erp()
        print(f"\n[1/4] Usando último arquivo baixado: {arquivo_erp}")
    else:
        print("\n[1/4] Extraindo relatório do ERP B2B...")
        try:
            from erp_extractor import extrair_relatorio_erp
            arquivo_erp = extrair_relatorio_erp()
        except Exception as e:
            print(f"\n[ERRO] Falha na extração automática: {e}")
            print("       Baixe o relatório manualmente e use: python main.py --arquivo <caminho>")
            sys.exit(1)

    if not arquivo_erp or not arquivo_erp.exists():
        print(f"[ERRO] Arquivo não encontrado: {arquivo_erp}")
        sys.exit(1)

    # --- ETAPA 2: Leitura e limpeza ---
    print("\n[2/4] Lendo e limpando relatório ERP...")
    import pandas as pd
    from lote_processor import (
        limpar_relatorio, verificar_colunas,
        carregar_hist_faturados, marcar_faturamentos,
        aplicar_regras_faturamento, gerar_lote,
        exportar_excel, salvar_hist_faturados,
    )

    try:
        if arquivo_erp.suffix.lower() == ".csv":
            for enc in ("utf-8-sig", "latin-1", "cp1252", "utf-8"):
                try:
                    df_erp = pd.read_csv(arquivo_erp, dtype=str, sep=";", encoding=enc)
                    print(f"       Encoding detectado: {enc}")
                    break
                except UnicodeDecodeError:
                    continue
        else:
            df_erp = pd.read_excel(arquivo_erp, sheet_name=0, dtype=str, header=0)
        print(f"       {len(df_erp)} linhas carregadas, {len(df_erp.columns)} colunas.")
    except Exception as e:
        print(f"[ERRO] Não foi possível ler o arquivo Excel: {e}")
        sys.exit(1)

    df_erp = limpar_relatorio(df_erp)
    colunas_faltando = verificar_colunas(df_erp)
    if colunas_faltando:
        print(f"\n[ATENCAO] Colunas ausentes no ERP: {colunas_faltando}")
        print("  O processamento continuara mas alguns valores podem estar incorretos.")

    # --- ETAPA 3: Cruzamento com histórico ---
    print("\n[3/4] Cruzando com histórico de faturamentos...")
    if args.sem_sheets:
        print("       Modo --sem-sheets: histórico ignorado.")
        df_hist = pd.DataFrame()
    else:
        try:
            df_hist = carregar_hist_faturados()
        except Exception as e:
            print(f"       Aviso: não foi possível carregar Hist. Faturados ({e})")
            print("       Continuando sem verificação de duplo faturamento...")
            df_hist = pd.DataFrame()

    df_erp = marcar_faturamentos(df_erp, df_hist)

    # --- ETAPA 4: Aplicação das regras e geração do lote ---
    print("\n[4/4] Aplicando regras de faturamento...")
    df_processado = aplicar_regras_faturamento(df_erp)
    df_lote       = gerar_lote(df_processado)

    caminho_lote, caminho_conf = exportar_excel(df_lote, df_processado, df_hist)

    # Atualiza histórico no Google Sheets (opcional)
    if not args.sem_sheets and not df_lote.empty:
        atualizar = input("\nAtualizar Hist. Faturados no Google Sheets com os sinistros deste lote? (s/N): ")
        if atualizar.strip().lower() == "s":
            _preparar_historico_e_salvar(df_lote, salvar_hist_faturados)

    # --- Resumo final ---
    _exibir_resumo_final(df_processado, df_lote, caminho_lote, caminho_conf)


def _ultimo_arquivo_erp() -> Path | None:
    """Retorna o arquivo ERP mais recente na pasta de downloads."""
    download_dir = OUTPUT_DIR / "erp_download"
    arquivos = sorted(download_dir.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
    return arquivos[0] if arquivos else None


def _preparar_historico_e_salvar(df_lote, fn_salvar):
    """Prepara as colunas do histórico e salva."""
    import pandas as pd
    from config import LOTE_ATUAL
    hoje = datetime.today().strftime("%d/%m/%Y")

    col_os = next((c for c in ["Ordem de Serviço", "OS", "O,S"] if c in df_lote.columns), None)
    col_sin = next((c for c in ["Sinistro AXA"] if c in df_lote.columns), None)

    registros = []
    for _, row in df_lote.iterrows():
        registros.append({
            "OS":                   row.get(col_os, ""),
            "Sinistro":             row.get(col_sin, ""),
            "Data Pago":            hoje,
            "Valor Pago":           row.get("valor_indenizacao_correto", 0),
            "Metodo de Pagamento":  "Lote B2B",
            "Comprovante Bancário": LOTE_ATUAL,
            "Data Indenização":     hoje,
            "Seguradora":           "AXA",
        })

    fn_salvar(pd.DataFrame(registros))


def _exibir_resumo_final(df_total, df_lote, caminho_lote, caminho_conf):
    total_inden = df_lote.loc[df_lote["incluir_indenizacao"], "valor_indenizacao_correto"].sum()
    total_desp  = df_lote.loc[df_lote["incluir_despesa"],     "valor_despesa_correto"].sum()
    no_lote = df_total["incluir_indenizacao"] | df_total["incluir_despesa"]
    col_ei = next((c for c in df_total.columns if "Valor Pagto Indeniza" in c), None)
    col_ed = next((c for c in df_total.columns if "Valor Pagto Despesa"  in c), None)
    erp_i_zero = df_total[col_ei].fillna(0).astype(float) == 0 if col_ei else pd.Series(False, index=df_total.index)
    erp_d_zero = df_total[col_ed].fillna(0).astype(float) == 0 if col_ed else pd.Series(False, index=df_total.index)
    divergencias = int((
        no_lote & (
            ((df_total["diferenca_indenizacao"].abs() > 0.01) & ~erp_i_zero) |
            ((df_total["diferenca_despesa"].abs()     > 0.01) & ~erp_d_zero)
        )
    ).sum())

    print("\n" + "=" * 60)
    print("  RESUMO DO LOTE")
    print("=" * 60)
    print(f"  Lote:                {LOTE_ATUAL}")
    print(f"  Sinistros no lote:   {len(df_lote)}")
    print(f"  Excluídos:           {len(df_total) - len(df_lote)}")
    print(f"  Divergências:        {divergencias}")
    print(f"  Total Indenização:   R$ {total_inden:,.2f}")
    print(f"  Total Despesa:       R$ {total_desp:,.2f}")
    print(f"  TOTAL GERAL:         R$ {total_inden + total_desp:,.2f}")
    print("=" * 60)
    print(f"\n  Lote para AXA:    {caminho_lote}")
    print(f"  Conferencia:      {caminho_conf}")
    print()

    if divergencias > 0:
        print(f"  [!] {divergencias} sinistro(s) com divergencia de valor.")
        print("     Verifique a aba 'Divergencias' no arquivo de conferencia.")
    print()


if __name__ == "__main__":
    main()
