# Setup — Automação AXA

## 1. Instalar dependências

```
cd "C:\Users\ricardo.marques.PLL\Documents\A35 - CLAUDE IA\AXA_Automacao"
pip install -r requirements.txt
playwright install chromium
```

## 2. Configurar .env

Copie `.env.example` para `.env` e preencha:

```
GMAIL_USER=r.marques.ricardo100@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
SHEET_ID=1J1FK7oukGdu4nXJnnCmyLeKkUdBDzg5-olv8yovbHtg
```

### Como gerar o App Password do Gmail:
1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Outro (nome personalizado)" → "ERP AXA"
3. Copie a senha gerada (16 caracteres) para o .env

## 3. Configurar Google Sheets (OAuth)

Na primeira execução, o script vai abrir uma janela do navegador pedindo autorização para acessar o Google Sheets. Depois de autorizar, as credenciais ficam salvas localmente.

Para isso, você precisa de um arquivo `oauth_credentials.json` na pasta. Instrução:
1. Acesse: https://console.cloud.google.com/
2. Crie um projeto → Habilite a API Google Sheets
3. Crie credencial OAuth → Tipo "Aplicativo de Desktop"
4. Baixe o JSON e salve como `oauth_credentials.json` na pasta do projeto

## 4. Executar

### Fluxo completo (abre o navegador, extrai e processa):
```
python main.py
```

### Só processar (usando arquivo ERP já baixado):
```
python main.py --so-processar
```

### Processar arquivo específico:
```
python main.py --arquivo "C:\caminho\para\relatorio.xlsx"
```

### Sem integração com Google Sheets:
```
python main.py --sem-sheets
```

## 5. Outputs gerados

Todos os arquivos ficam na pasta `output/`:

- `Lote_AXA_YYYYMMDD_B2B_2.0_Lote_86_GIS.xlsx` — arquivo para enviar à AXA
- `Conferencia_AXA_YYYYMMDD.xlsx` — relatório interno com:
  - Aba "Todos os Sinistros" — visão completa com todas as validações
  - Aba "Divergências" — sinistros com diferença entre valor ERP e valor calculado
  - Aba "Excluídos" — sinistros removidos do lote e motivo
  - Aba "Resumo" — totais e indicadores

## Regras implementadas

| Situação | Ação |
|---|---|
| Indenização já faturada | Remove indenização do lote |
| Despesa já faturada + Negado/Sem Atendimento | Remove da lista completamente |
| Despesa já faturada + Reparo/Reposição/Crédito | Zera despesa, mantém indenização |
| estado_aparelho = LIKE NEW | Indenização = 82% do LMI |
| estado_aparelho = Refurbished | Indenização = 81% do LMI |
| Derramamento de Líquido / Danos Elétricos | Normalizado para Quebra Acidental |
