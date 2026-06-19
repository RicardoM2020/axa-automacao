"""
Lê o código 2FA do Gmail via IMAP.
Requer App Password do Google (não a senha normal da conta).
"""

import imaplib
import email
import re
import time
from config import GMAIL_USER, GMAIL_APP_PASSWORD, GMAIL_IMAP


def buscar_codigo_2fa(timeout_segundos: int = 90, assunto_parcial: str = "código") -> str | None:
    """
    Aguarda e retorna o código 2FA enviado por email após o login no ERP.
    Busca nos últimos emails não lidos por um código numérico de 4-8 dígitos.
    """
    if not GMAIL_APP_PASSWORD:
        raise ValueError(
            "GMAIL_APP_PASSWORD não configurado no .env\n"
            "Gere em: https://myaccount.google.com/apppasswords"
        )

    print(f"[Gmail] Aguardando código 2FA (timeout: {timeout_segundos}s)...")

    inicio = time.time()
    tentativa = 0

    while time.time() - inicio < timeout_segundos:
        tentativa += 1
        try:
            mail = imaplib.IMAP4_SSL(GMAIL_IMAP)
            mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            mail.select("INBOX")

            # Busca emails não lidos dos últimos minutos
            _, mensagens = mail.search(None, "UNSEEN")
            ids = mensagens[0].split()

            if ids:
                # Lê os mais recentes primeiro
                for msg_id in reversed(ids[-10:]):
                    _, dados = mail.fetch(msg_id, "(RFC822)")
                    msg = email.message_from_bytes(dados[0][1])

                    assunto = msg.get("Subject", "").lower()
                    corpo = _extrair_corpo(msg)

                    # Verifica se é email do ERP B2B
                    remetente = msg.get("From", "").lower()
                    if "grupopll" in remetente or "erp" in remetente or "b2b" in remetente or "codigo" in assunto or "autenticação" in assunto or "token" in assunto:
                        codigo = _extrair_codigo(corpo)
                        if codigo:
                            print(f"[Gmail] Código encontrado: {codigo}")
                            mail.store(msg_id, "+FLAGS", "\\Seen")
                            mail.logout()
                            return codigo

                    # Tenta encontrar código em qualquer email recente com número
                    codigo = _extrair_codigo(corpo)
                    if codigo and len(corpo) < 2000:  # Emails curtos provavelmente são 2FA
                        print(f"[Gmail] Código encontrado em email de '{msg.get('From', '')}': {codigo}")
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                        mail.logout()
                        return codigo

            mail.logout()

        except Exception as e:
            print(f"[Gmail] Erro na tentativa {tentativa}: {e}")

        print(f"[Gmail] Aguardando... ({int(time.time() - inicio)}s)")
        time.sleep(5)

    print("[Gmail] Timeout: código não encontrado. Insira manualmente:")
    return input("Código 2FA: ").strip()


def _extrair_corpo(msg) -> str:
    corpo = ""
    if msg.is_multipart():
        for parte in msg.walk():
            tipo = parte.get_content_type()
            if tipo in ("text/plain", "text/html"):
                try:
                    corpo += parte.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
    else:
        try:
            corpo = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return corpo


def _extrair_codigo(texto: str) -> str | None:
    # Padrões comuns de código 2FA: 4-8 dígitos isolados
    padroes = [
        r'\b(\d{6})\b',   # 6 dígitos (mais comum)
        r'\b(\d{4})\b',   # 4 dígitos
        r'\b(\d{8})\b',   # 8 dígitos
        r'[Cc]ódigo[:\s]+(\d+)',
        r'[Tt]oken[:\s]+(\d+)',
        r'[Cc]ode[:\s]+(\d+)',
    ]
    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            return match.group(1)
    return None
