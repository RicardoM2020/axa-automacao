"""
Interface Web — Faturamento AXA
Flask app para upload do CSV, processamento e download dos arquivos.
"""

import os
import base64
import pickle
import uuid
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, session
import pandas as pd

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "axa-pll-secret-2024")

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Estado das tarefas em memória {job_id: {status, log, lote_path, conf_path}}
JOBS = {}


# ---------------------------------------------------------------------------
# Google Sheets — suporta token.pickle local ou env var (Railway)
# ---------------------------------------------------------------------------

def _preparar_google_token():
    """Se GOOGLE_TOKEN estiver no env (base64), decodifica para token.pickle."""
    token_env = os.getenv("GOOGLE_TOKEN")
    token_path = BASE_DIR / "token.pickle"
    if token_env and not token_path.exists():
        with open(token_path, "wb") as f:
            f.write(base64.b64decode(token_env))


_preparar_google_token()


# ---------------------------------------------------------------------------
# Processamento em background
# ---------------------------------------------------------------------------

def _processar(job_id: str, csv_path: Path, lote_atual: str, lote_numero: int, sem_sheets: bool):
    job = JOBS[job_id]
    log = []

    def _log(msg):
        log.append(msg)
        job["log"] = log.copy()

    try:
        import config as cfg
        # Sobrescreve configurações de lote dinamicamente
        cfg.LOTE_ATUAL  = lote_atual
        cfg.LOTE_NUMERO = lote_numero

        from lote_processor import (
            limpar_relatorio, verificar_colunas,
            carregar_hist_faturados, marcar_faturamentos,
            aplicar_regras_faturamento, gerar_lote, exportar_excel,
        )

        _log("Lendo arquivo CSV...")
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                df_erp = pd.read_csv(csv_path, dtype=str, sep=";", encoding=enc)
                _log(f"{len(df_erp)} linhas carregadas ({enc}).")
                break
            except UnicodeDecodeError:
                continue

        _log("Limpando e normalizando dados...")
        df_erp = limpar_relatorio(df_erp)
        faltando = verificar_colunas(df_erp)
        if faltando:
            _log(f"Aviso: colunas ausentes no ERP: {faltando}")

        df_hist = pd.DataFrame()
        if not sem_sheets:
            try:
                _log("Carregando historico de faturamentos (Google Sheets)...")
                df_hist = carregar_hist_faturados()
                _log(f"{len(df_hist)} registros no historico.")
            except Exception as e:
                _log(f"Aviso: nao foi possivel carregar historico ({e}). Continuando sem verificacao de duplo faturamento.")

        _log("Cruzando com historico...")
        df_erp = marcar_faturamentos(df_erp, df_hist)

        _log("Aplicando regras de faturamento...")
        df_processado = aplicar_regras_faturamento(df_erp)
        df_lote = gerar_lote(df_processado)

        n_lote     = len(df_lote)
        n_excluido = len(df_processado) - n_lote
        total_i    = df_lote.loc[df_lote["incluir_indenizacao"], "valor_indenizacao_correto"].sum()
        total_d    = df_lote.loc[df_lote["incluir_despesa"],     "valor_despesa_correto"].sum()

        _log(f"Lote: {n_lote} sinistros | Excluidos: {n_excluido}")
        _log(f"Total Indenizacao: R$ {total_i:,.2f}")
        _log(f"Total Despesa:     R$ {total_d:,.2f}")
        _log(f"TOTAL GERAL:       R$ {total_i + total_d:,.2f}")

        _log("Gerando arquivos Excel...")
        caminho_lote, caminho_conf, caminho_fatura = exportar_excel(df_lote, df_processado, df_hist if not df_hist.empty else None)

        job["lote_path"]   = str(caminho_lote)
        job["conf_path"]   = str(caminho_conf)
        job["fatura_path"] = str(caminho_fatura)
        job["resumo"] = {
            "lote":        n_lote,
            "excluidos":   n_excluido,
            "indenizacao": f"R$ {total_i:,.2f}",
            "despesa":     f"R$ {total_d:,.2f}",
            "total":       f"R$ {total_i + total_d:,.2f}",
            "lote_nome":   lote_atual,
        }
        job["status"] = "concluido"
        _log("Processamento concluido!")

    except Exception as e:
        import traceback
        _log(f"ERRO: {e}")
        _log(traceback.format_exc())
        job["status"] = "erro"

    finally:
        # Remove o CSV temporário
        try:
            csv_path.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    # Lê lote atual do config
    try:
        import config as cfg
        lote_atual  = cfg.LOTE_ATUAL
        lote_numero = cfg.LOTE_NUMERO
    except Exception:
        lote_atual  = "B2B 2.0 Lote 86 GIS"
        lote_numero = 86
    return render_template("index.html", lote_atual=lote_atual, lote_numero=lote_numero)


@app.route("/processar", methods=["POST"])
def processar():
    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    lote_nome   = request.form.get("lote_nome", "B2B 2.0 Lote 86 GIS").strip()
    lote_numero = int(request.form.get("lote_numero", 86))
    sem_sheets  = request.form.get("sem_sheets") == "1"

    # Salva CSV temporariamente
    job_id   = str(uuid.uuid4())
    csv_path = UPLOAD_DIR / f"{job_id}.csv"
    arquivo.save(str(csv_path))

    JOBS[job_id] = {"status": "processando", "log": [], "lote_path": None, "conf_path": None, "fatura_path": None}

    thread = threading.Thread(
        target=_processar,
        args=(job_id, csv_path, lote_nome, lote_numero, sem_sheets),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"erro": "Job nao encontrado."}), 404
    return jsonify({
        "status":   job["status"],
        "log":      job["log"],
        "resumo":   job.get("resumo"),
        "tem_lote":   bool(job.get("lote_path")),
        "tem_conf":   bool(job.get("conf_path")),
        "tem_fatura": bool(job.get("fatura_path")),
    })


@app.route("/download/<job_id>/<tipo>")
def download(job_id, tipo):
    job = JOBS.get(job_id)
    if not job:
        return "Job nao encontrado.", 404

    if tipo == "lote" and job.get("lote_path"):
        path = Path(job["lote_path"])
        return send_file(str(path), as_attachment=True, download_name=path.name)
    elif tipo == "conferencia" and job.get("conf_path"):
        path = Path(job["conf_path"])
        return send_file(str(path), as_attachment=True, download_name=path.name)
    elif tipo == "fatura" and job.get("fatura_path"):
        path = Path(job["fatura_path"])
        return send_file(str(path), as_attachment=True, download_name=path.name)

    return "Arquivo nao disponivel.", 404


@app.route("/health")
def health():
    return jsonify({"status": "ok", "ts": datetime.now().isoformat()})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
