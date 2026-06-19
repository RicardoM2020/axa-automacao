"""
Automação do ERP B2B para extração do relatório AXA.
Usa Playwright com perfil persistente do Chrome (aproveita senha salva).
"""

import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from config import ERP_URL, EMPRESA_ERP, DATA_INICIO, DATA_FIM, OUTPUT_DIR
from gmail_reader import buscar_codigo_2fa

# Pasta de download padrão
DOWNLOAD_DIR = OUTPUT_DIR / "erp_download"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Caminho do perfil do Chrome salvo (usa credenciais já guardadas no navegador)
CHROME_USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"


def extrair_relatorio_erp() -> Path:
    """
    Faz login no ERP, seleciona PLL Inovação, passa pelo 2FA e baixa o relatório Excel.
    Retorna o caminho do arquivo baixado.
    """
    with sync_playwright() as p:
        print("[ERP] Abrindo navegador...")

        # Usa perfil persistente do Chrome para aproveitar senha salva
        if CHROME_USER_DATA.exists():
            context = p.chromium.launch_persistent_context(
                str(CHROME_USER_DATA),
                channel="chrome",
                headless=False,
                downloads_path=str(DOWNLOAD_DIR),
                args=["--profile-directory=Default"],
            )
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = p.chromium.launch(headless=False, downloads_path=str(DOWNLOAD_DIR))
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

        arquivo_baixado = _executar_fluxo(page, context)
        context.close()
        return arquivo_baixado


def _executar_fluxo(page: Page, context) -> Path:
    print(f"[ERP] Acessando {ERP_URL}")
    page.goto(ERP_URL, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    # --- Seleção de empresa ---
    _selecionar_empresa(page)

    # --- Aceitar Termos de Uso ---
    _aceitar_termos(page)

    # --- Login / 2FA ---
    _fazer_login(page)

    # --- Configurar datas e baixar ---
    arquivo = _baixar_relatorio(page, context)
    return arquivo


def _selecionar_empresa(page: Page):
    """Seleciona PLL Inovação na tela inicial se solicitado."""
    try:
        # Aguarda campo de seleção de empresa (pode ser select, botão ou lista)
        page.wait_for_selector("text=PLL", timeout=5000)
        print(f"[ERP] Selecionando empresa: {EMPRESA_ERP}")

        # Tenta select HTML
        selects = page.query_selector_all("select")
        for sel in selects:
            opcoes = sel.inner_text()
            if "PLL" in opcoes or "Inovação" in opcoes:
                sel.select_option(label=EMPRESA_ERP)
                time.sleep(1)
                return

        # Tenta clicar em elemento com texto PLL Inovação
        page.click(f"text={EMPRESA_ERP}")
        time.sleep(1)

    except Exception:
        print("[ERP] Seleção de empresa não necessária ou já selecionada.")


def _aceitar_termos(page: Page):
    """Marca o checkbox 'Li e concordo com os Termos de Uso'."""
    seletores = [
        "text=Li e concordo",
        "input[type='checkbox']",
        "label:has-text('Termos de Uso')",
        "label:has-text('concordo')",
    ]
    for seletor in seletores:
        try:
            elemento = page.wait_for_selector(seletor, timeout=3000)
            if elemento:
                # Se é checkbox, garante que está marcado
                if elemento.get_attribute("type") == "checkbox":
                    if not elemento.is_checked():
                        elemento.check()
                else:
                    elemento.click()
                print("[ERP] Termos de Uso aceitos.")
                time.sleep(0.5)
                return
        except Exception:
            continue


def _fazer_login(page: Page):
    """Trata o fluxo de login e 2FA."""
    # Se já estiver logado (redirecionou para o relatório), pula
    if "controle-financeiro" in page.url or "dashboard" in page.url:
        print("[ERP] Sessão já ativa, sem necessidade de login.")
        return

    # Aguarda campo de email/usuário
    try:
        campo_email = page.wait_for_selector(
            "input[type='email'], input[name='email'], input[name='usuario'], input[placeholder*='email']",
            timeout=5000
        )
        if campo_email:
            # Senha pode já estar preenchida pelo Chrome — apenas submete
            print("[ERP] Formulário de login detectado. Tentando submeter com credenciais salvas...")
            page.keyboard.press("Enter")
            time.sleep(3)
    except Exception:
        pass

    # Verifica se precisa de 2FA
    _verificar_2fa(page)


def _verificar_2fa(page: Page):
    """Verifica e preenche o código 2FA se solicitado."""
    indicadores_2fa = [
        "input[name='codigo']",
        "input[placeholder*='código']",
        "input[placeholder*='token']",
        "input[placeholder*='code']",
        "text=código de verificação",
        "text=autenticação",
        "text=verificação",
        "input[maxlength='6']",
        "input[maxlength='8']",
    ]

    campo_2fa = None
    for seletor in indicadores_2fa:
        try:
            campo_2fa = page.wait_for_selector(seletor, timeout=4000)
            if campo_2fa:
                print("[ERP] Tela de 2FA detectada.")
                break
        except Exception:
            continue

    if campo_2fa:
        codigo = buscar_codigo_2fa(timeout_segundos=90)
        if codigo:
            campo_2fa.click()
            campo_2fa.fill(codigo)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(3)
            print("[ERP] Código 2FA inserido.")
    else:
        print("[ERP] Sem 2FA necessário.")


def _baixar_relatorio(page: Page, context) -> Path:
    """Navega até o relatório, preenche as datas e baixa o arquivo."""
    print("[ERP] Configurando datas do relatório...")

    # Navega para a URL do relatório se não estiver lá
    if "PagamentoAxaList" not in page.url:
        page.goto(ERP_URL, wait_until="networkidle", timeout=20000)
        time.sleep(2)

    data_inicio_str = DATA_INICIO.strftime("%d/%m/%Y")
    data_fim_str    = DATA_FIM.strftime("%d/%m/%Y")

    # Preenche data inicial
    _preencher_data(page, data_inicio_str, "inicial")

    # Preenche data final
    _preencher_data(page, data_fim_str, "final")

    # Clica no botão de exportar/baixar Excel
    print(f"[ERP] Baixando relatório: {data_inicio_str} → {data_fim_str}")

    botoes_export = [
        "text=Excel",
        "text=Exportar",
        "text=Download",
        "button:has-text('Excel')",
        "a:has-text('Excel')",
        "input[value='Excel']",
        "button[title*='Excel']",
    ]

    with page.expect_download(timeout=60000) as download_info:
        clicado = False
        for seletor in botoes_export:
            try:
                page.click(seletor, timeout=3000)
                clicado = True
                print(f"[ERP] Botão de export clicado: '{seletor}'")
                break
            except Exception:
                continue

        if not clicado:
            raise RuntimeError(
                "[ERP] Botão de exportação não encontrado. "
                "Verifique manualmente a página do relatório."
            )

    download = download_info.value
    nome_arquivo = f"relatorio_axa_{DATA_FIM.strftime('%Y%m%d')}.xlsx"
    caminho_destino = DOWNLOAD_DIR / nome_arquivo
    download.save_as(str(caminho_destino))

    print(f"[ERP] Relatório salvo em: {caminho_destino}")
    return caminho_destino


def _preencher_data(page: Page, data: str, tipo: str):
    """Tenta preencher campo de data por vários seletores possíveis."""
    seletores = [
        f"input[name*='{tipo}']",
        f"input[placeholder*='{tipo}']",
        f"input[id*='{tipo}']",
        "input[type='date']",
        "input[placeholder*='DD/MM/YYYY']",
        "input[placeholder*='dd/mm/yyyy']",
    ]
    for seletor in seletores:
        try:
            campos = page.query_selector_all(seletor)
            if campos:
                idx = 0 if tipo == "inicial" else -1
                campos[idx].click(triple_click=True)
                campos[idx].fill(data)
                time.sleep(0.3)
                return
        except Exception:
            continue
    print(f"[ERP] Aviso: campo de data {tipo} não encontrado automaticamente.")
