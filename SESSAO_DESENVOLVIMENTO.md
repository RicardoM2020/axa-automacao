# Sessão de Desenvolvimento — Automação AXA
**Data:** 04/06/2026  
**Duração:** Sessão completa (~6h de trabalho)  
**Desenvolvido com:** Claude Sonnet 4.6 (Claude Code)

---

## O que foi construído

Sistema completo de automação da apuração e faturamento quinzenal dos sinistros da seguradora AXA pela PLL Inovação em Serviços de Tecnologia e Telefonia LTDA (CNPJ: 31.312.752/0001-11).

---

## Arquivos do projeto

```
AXA_Automacao/
├── app.py                  # Interface web Flask (upload CSV → download lote)
├── main.py                 # CLI — ponto de entrada principal
├── config.py               # Configurações (lote atual, datas, paths, credenciais)
├── lote_processor.py       # Toda a lógica de negócio + geração de Excel
├── matriz_parametros.py    # Tabela de regras (cobertura × finalização × aparelho)
├── erp_extractor.py        # Playwright: login automático ERP B2B + download CSV
├── gmail_reader.py         # IMAP: leitura automática do código 2FA
├── exportar_token.py       # Gera GOOGLE_TOKEN em base64 para o Railway
├── requirements.txt        # Dependências Python
├── Procfile                # Deploy Railway
├── railway.toml            # Configuração Railway
├── .gitignore
├── .env.example            # Template de variáveis de ambiente
├── .claude/launch.json     # Preview Flask local (porta 5001)
├── templates/index.html    # Interface web (upload + log + download)
└── output/                 # Arquivos gerados (gitignored)
```

---

## Contexto do processo

- **Periodicidade:** Quinzenal — dias **05 e 22** de cada mês
- **Fonte dos dados:** ERP B2B → `erp-b2b.grupopll.com.br` → relatório CSV
- **Período do relatório:** últimos 6 meses (data atual − 180 dias)
- **Próximo lote:** B2B 2.0 Lote 86 GIS (atualizar em `config.py` antes de cada apuração)
- **Envio:** Por e-mail para analista da AXA → após aprovação → emitir nota fiscal
- **Google Sheets:** `1J1FK7oukGdu4nXJnnCmyLeKkUdBDzg5-olv8yovbHtg`
  - Aba `Hist. Faturados` — 41.704 registros de histórico de pagamentos
  - Aba `Matriz Parametros` — regras de cálculo
- **Credenciais Google:** projeto `RECEITASAXA` no Google Cloud (ID: `receitasaxa`, organização `grupopll.com.br`)

---

## Regras de negócio implementadas

### 1. Normalização de coberturas

| Entrada | Saída |
|---|---|
| Derramamento de Líquido | Quebra Acidental |
| Danos Elétricos | Quebra Acidental |
| Quebra Acidental + % franquia = 0 | Extensão da Garantia Original |
| Cobertura vazia | → NATUREZA → DESCRIÇÃO DO EVENTO |

**Mapeamento NATUREZA → Cobertura:**
- Quebra Acidental / Dano Funcional → Quebra Acidental
- Furto / Roubo → Roubo e Furto

**Mapeamento DESCRIÇÃO DO EVENTO → Cobertura (fallback):**
- roubado, roubo, furtado, furto, subtra, arrombamento → Roubo e Furto
- quebr, queda, dano, molh, liquid, agua → Quebra Acidental
- garantia → Extensão da Garantia Original

### 2. Normalização de Tipo de Aparelho

- Vazio / NaN → **CELULAR**
- TELEFONE FIXO, NOTEBOOK, qualquer outro → **TABLET**
- `Valor Pagto Despesa = R$ 127,07` com aparelho CELULAR → corrige para **TABLET** (diferença = -38,12)

### 3. Normalização de Status/Finalização

Quando vazios, preenche via:
1. Coluna `Observações` com "NEGADO" → Status=Negado, Finalização=Negado
2. Coluna `setor_status`:
   - "sem atendimento" → Encerrado / Sem Atendimento
   - "indenizado" → Indenizado / Crédito em Conta
   - "negado" → Negado / Negado
   - "reparo" → Indenizado / Reparo
   - "reposi" → Indenizado / Reposição

### 4. Fórmula de indenização

```
valor_indenizacao = ARRED(((% Indenização - % Franquia) × LMI) / 100, 2)
```

Fonte das variáveis:
- `%` → Matriz Parâmetros (por cobertura + status + finalização + aparelho)  
- `% Franquia` → coluna `PERCENTUAL COBRADO FRANQUIA` do ERP
- `LMI` → coluna `LMI DA APÓLICE` do ERP

### 5. Estados especiais do aparelho (coluna `estado_aparelho`)

- `LIKE NEW` + Reposição → **82% do LMI**
- `EXCELENTE` + Reposição → **81% do LMI**
- Qualquer outro → usa Matriz Parâmetros normalmente

### 6. Regras de exclusão do lote

| Regra | Condição | Ação |
|---|---|---|
| 0 | Encerrado/Sem Atendimento em Quebra Acidental ou EGO | Excluir tudo |
| 0b | Dados insuficientes (cobertura/status vazio após tentativas) | Excluir tudo |
| 1 | Indenização já faturada (via OS Interna PLL no histórico) | Remove indenização |
| 2 | Despesa já faturada + Negado/Sem Atendimento | Remove tudo |
| 3 | Despesa já faturada + Reparo/Reposição/Crédito | Zera despesa, mantém indenização |
| 4 | % Indenização = 0 | Sem indenização |
| 5 | Parceiros homologados + Reparo + valor diferente | Aceita valor do ERP |

### 7. Parceiros homologados (Reparo aceita valor ERP)

- SOLINFORMATICA
- InfoStore
- Sol Informática
- Papel & Cia
- Papel

### 8. Controle de duplo faturamento

- **Campo de cruzamento:** `OS Interna PLL` (ex: `930193438`)
- **Fonte:** aba `Hist. Faturados` do Google Sheets
- **Distinção por tipo:**
  - `Valor Pagto Indenização > 0` → `indenizacao_ja_faturada = True`
  - `Valor Pagto Despesa > 0` → `despesa_ja_faturada = True`
- OS com apenas despesa faturada **pode** ter indenização no novo lote

### 9. Divergências

- Sinistros **no lote** onde valor calculado ≠ valor ERP
- **Excluídos** da aba Divergências: casos onde ERP = 0 (intencional)
- **Excluídos** da aba Divergências: sinistros excluídos do lote

### 10. De/Para da coluna cobertura no arquivo final

| Interno | Arquivo Final (para AXA) |
|---|---|
| Roubo e Furto | **Roubo ou Furto Qualificado** |
| Quebra Acidental | Quebra Acidental |
| Extensão da Garantia Original | Extensão da Garantia Original |

### 11. Outras formatações do arquivo final

- `PERCENTUAL COBRADO FRANQUIA`: ponto → vírgula (`20.0` → `20,0`)
- `Número Lote`: preenchido com o número do lote atual (ex: `86`)
- `Razão`: preenchido com `"B2B 2.0"`
- Colunas internas de controle removidas do arquivo final

---

## Matriz de Parâmetros (valores por cobertura)

| Cobertura | Status | Finalização | Aparelho | Despesa | % Inden |
|---|---|---|---|---|---|
| Quebra Acidental | Indenizado | Reparo | CELULAR | 88,95 | 53% |
| Quebra Acidental | Indenizado | Reparo | TABLET | 127,07 | 53% |
| Quebra Acidental | Indenizado | Reposição | CELULAR | 88,95 | 87% |
| Quebra Acidental | Indenizado | Reposição | TABLET | 127,07 | 87% |
| Quebra Acidental | Indenizado | Crédito em Conta | CELULAR | 88,95 | 100% |
| Quebra Acidental | Indenizado | Crédito em Conta | TABLET | 127,07 | 100% |
| Quebra Acidental | Negado/Encerrado | Negado/Sem Atendimento | qualquer | variável | 0% |
| Extensão da Garantia | Indenizado | Reparo | CELULAR | 88,95 | 32% |
| Extensão da Garantia | Indenizado | Reparo | TABLET | 127,07 | 32% |
| Extensão da Garantia | Indenizado | Reposição | CELULAR | 88,95 | 85% |
| Extensão da Garantia | Indenizado | Crédito em Conta | qualquer | variável | 100% |
| Roubo e Furto | Indenizado | Reposição | CELULAR | 127,07 | 86% |
| Roubo e Furto | Indenizado | Reposição | TABLET | 127,07 | 86% |
| Roubo e Furto | Indenizado | Crédito em Conta | qualquer | 127,07 | 100% |
| Roubo e Furto | Encerrado | Sem Atendimento | qualquer | 127,07 | 0% |

---

## Interface Web (Flask)

**Acesso local:** http://localhost:5001  
**Iniciar:** `python app.py` na pasta do projeto

**Fluxo da interface:**
1. Usuário edita Nome do Lote e Número
2. Faz upload do CSV exportado do ERP
3. Clica "Processar Lote"
4. Vê log em tempo real
5. Baixa os dois arquivos Excel gerados

**Para deploy no Railway:**
1. `git init && git add . && git commit -m "AXA Faturamento"`
2. Railway → New Project → Deploy from GitHub
3. Variáveis de ambiente necessárias:
   - `SECRET_KEY` = qualquer string aleatória
   - `SHEET_ID` = `1J1FK7oukGdu4nXJnnCmyLeKkUdBDzg5-olv8yovbHtg`
   - `GOOGLE_TOKEN` = valor gerado por `python exportar_token.py`
4. Railway detecta `railway.toml` automaticamente

---

## Outputs gerados

Em `output/`:

| Arquivo | Conteúdo |
|---|---|
| `Lote_AXA_YYYYMMDD_HHMM_B2B_2.0_Lote_XX_GIS.xlsx` | Arquivo para enviar à AXA |
| `Conferencia_AXA_YYYYMMDD_HHMM.xlsx` | Relatório interno |

**Abas da Conferência:**
- **Todos os Sinistros** — visão completa com todas as validações
- **Divergências** — sinistros no lote com valor diferente do ERP (apenas ERP ≠ 0)
- **Excluídos** — com motivo + valores já faturados no histórico
- **Resumo** — totais, motivos de exclusão com contagens e totais do histórico

---

## Comandos úteis

```bash
# Processar arquivo já baixado (sem Google Sheets — teste rápido)
python main.py --arquivo "C:\caminho\PagamentoAxa.csv" --sem-sheets

# Processar com Google Sheets (produção)
python main.py --arquivo "C:\caminho\PagamentoAxa.csv"

# Só processar (usa último CSV baixado)
python main.py --so-processar

# Fluxo completo (abre navegador, faz login no ERP, baixa CSV, processa)
python main.py

# Interface web local
python app.py

# Gerar GOOGLE_TOKEN para Railway
python exportar_token.py
```

---

## Configuração antes de cada apuração

Em `config.py`, atualizar:
```python
LOTE_ATUAL  = "B2B 2.0 Lote 87 GIS"   # incrementar
LOTE_NUMERO = 87
```

Ou alterar diretamente na interface web antes de processar.

---

## Dependências instaladas

```
flask, gunicorn, playwright, pandas, openpyxl,
python-dotenv, gspread, google-auth, google-auth-oauthlib, requests
```

Playwright: `python -m playwright install chromium`

---

## Skill criada

Localização: `C:\Users\ricardo.marques.PLL\.claude\skills\axa-faturamento\`

A skill é carregada automaticamente quando qualquer membro da equipe mencionar "faturamento AXA", "lote AXA", "apuração AXA" ou similar em qualquer sessão do Claude Code.

---

## Próximos passos pendentes

- [ ] Deploy no Railway (configurar git + variáveis de ambiente)
- [ ] Testar interface web com lote real (aguardando próxima apuração dia 22/06/2026)
- [ ] Definir acesso para equipe (URL do Railway após deploy)
- [ ] Automação completa do login no ERP (erp_extractor.py — testar Playwright com login real)
