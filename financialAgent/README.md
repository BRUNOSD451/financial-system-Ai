# Agent Finance API

API REST em Python com FastAPI, LangChain e OpenRouter. As 40 ferramentas financeiras chamam as APIs do backend Node.js; consultas ao MySQL e cálculos financeiros ficam no Node.js.

## Requisitos

- Python 3.11 ou superior
- Uma chave de API da OpenRouter: <https://openrouter.ai/keys>

## Configuração (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Crie o arquivo `.env` localmente; ele e ignorado pelo Git. Configure `OPENROUTER_API_KEY` com sua chave ; o modelo atual esta definido em `app/core/openrouter.py`. As variaveis estao documentadas no [README da raiz](../README.md).

Para conectar ao Node.js, estas configurações usam os valores padrão abaixo quando omitidas do `.env`:

```dotenv
BACKEND_API_URL=http://127.0.0.1:3000
BACKEND_TIMEOUT_SECONDS=20
OPENROUTER_MAX_TOKENS=2048
```

Inicie também o backend com `npm run dev` dentro de `backEnd`. Se os serviços estiverem em máquinas ou contêineres diferentes, ajuste `BACKEND_API_URL` para o endereço acessível pelo Python.

## Executar

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

A API fica em `http://127.0.0.1:8000`. A documentação interativa fica em `http://127.0.0.1:8000/docs`.

## Endpoint

`POST /api/chat`

Corpo JSON:

```json
{
  "message": "Consulte meu resumo financeiro de setembro de 2026"
}
```

Resposta:

```json
{
  "reply": "...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Também há um endpoint simples de verificação em `GET /health`. Mensagens vazias ou acima de 12.000 caracteres são rejeitadas. Se a chave não estiver configurada, `/api/chat` retorna `503`; falhas do provedor retornam `502` sem expor detalhes internos.

## Verificacao

Inicie a API e consulte `/health`. Os testes automatizados nao fazem parte desta versao do repositorio.

## Ferramentas financeiras

- Consultas de contas, categorias, lançamentos, contas a pagar, cartões, faturas, orçamentos e transferências.
- Criação e atualização de cadastros, registro de lançamentos, transferências e pagamentos, fechamento de fatura e exclusões permitidas pelas APIs.
- Comparação de meses, análise de orçamento e compromissos por vencimento, calculados pelos endpoints `/insights` do Node.js.

As respostas são objetos com `ok`, `status_code` e `data`, ou `error` em caso de falha. Listas paginadas incluem `limit`, `offset`, `returned`, `has_more_possible` e `next_offset`; uma página cheia não garante que existam mais registros e não representa o total do período.

IDs e valores monetários são strings; datas usam `YYYY-MM-DD`. Nas atualizações, campos omitidos são preservados. `atualizar_lancamento` aceita `remove_category` para limpar a categoria e remove o vínculo anterior ao trocar conta por cartão ou vice-versa. `atualizar_conta_a_pagar` aceita `remove_account` para remover a conta vinculada.

As chamadas HTTP não têm repetição automática. Um timeout de escrita retorna `outcome_unknown: true`: consulte os registros antes de repetir, pois a operação pode ter sido gravada. O loop executa as ferramentas sem bloquear o FastAPI e entrega erros de validação ao modelo.

O chat recebe `message` e `conversation_id` opcional (UUID). Na primeira chamada, omita o ID; a resposta inclui `reply` e `conversation_id`. Nas seguintes, envie o mesmo ID. O backend guarda as 12 ultimas mensagens concluidas (6 pares usuario/assistente), sem aceitar `history` do cliente. Cada conversa fica isolada. `DELETE /api/conversations/{conversation_id}` limpa o historico. Chamadas simultaneas na mesma conversa retornam 409; ID inexistente ou expirado retorna 404. Falhas nao adicionam mensagens ao historico.

## Estrutura do projeto

```text
app/
  main.py              # Entrada da API
  core/                # Funcionalidades
    api.py             # Endpoints e modelos de entrada e resposta
    openrouter.py      # Consulta ao modelo de IA
    tools.py           # 40 ferramentas financeiras
    backend.py         # Cliente HTTP do Node.js
  config/              # Configurações
    settings.py        # Leitura do ambiente e do .env
```


O armazenamento e em memoria, por processo: reiniciar o agente apaga as conversas. Execute com um worker. Conversas inativas expiram em 24 horas (limpeza no proximo envio); o limite e 1.000 conversas. Para multiplos workers ou persistencia entre reinicios, sera necessario armazenamento compartilhado. O ID deve ser mantido privado: este app local nao possui autenticacao por usuario.
