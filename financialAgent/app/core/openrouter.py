import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from app.config.settings import Settings, get_settings
from app.core.tools import TOOLS
from app.core.conversations import HISTORY_LIMIT

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_TOOL_ROUNDS = 5


class OpenRouterNotConfiguredError(RuntimeError):
    """Indica que a chave da OpenRouter ainda não foi configurada."""


def _build_chat_model(settings: Settings) -> ChatOpenAI:
    api_key = settings.openrouter_api_key.get_secret_value()
    if not api_key or api_key == "your_openrouter_api_key_here":
        raise OpenRouterNotConfiguredError(
            "Configure OPENROUTER_API_KEY no arquivo .env antes de chamar o chat."
        )

    headers = {"X-Title": settings.openrouter_app_name}
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url

    return ChatOpenAI(
        model="openrouter/auto",
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers=headers,
        temperature=0.5,
        max_tokens=settings.openrouter_max_tokens,
    )
                   

async def generate_chat_response(message: str, history: list[dict[str, str]] | None = None) -> str:
    """Consulta o modelo configurado da OpenRouter usando LangChain."""
    model = _build_chat_model(get_settings())
    model_with_tools = model.bind_tools(TOOLS)
    tool_lookup = {registered_tool.name: registered_tool for registered_tool in TOOLS}
    messages = []
    for item in (history or [])[-HISTORY_LIMIT:]:
        message_type = HumanMessage if item["role"] == "user" else AIMessage
        messages.append(message_type(content=item["content"]))
    messages.append(HumanMessage(content=message))

    for _ in range(MAX_TOOL_ROUNDS):
        result = await model_with_tools.ainvoke(messages)
        if not result.tool_calls:
            break

        messages.append(result)
        for tool_call in result.tool_calls:
            tool = tool_lookup.get(tool_call["name"])
            if tool is None:
                tool_result = f"A ferramenta '{tool_call['name']}' não está registrada."
            else:
                try:
                    tool_result = await tool.ainvoke(tool_call.get("args", {}))
                except ValidationError as exc:
                    # A validação ocorre antes da execução: nada foi gravado.
                    # Devolve os campos inválidos para o modelo corrigir a chamada.
                    tool_result = {
                        "ok": False,
                        "error": "Argumentos inválidos para a ferramenta; nenhuma operação executada.",
                        "validation_errors": exc.errors(include_input=False, include_url=False, include_context=False),
                        "guidance": "Corrija os argumentos conforme o esquema. IDs e valores monetários devem ser strings. Peça ao usuário os dados que faltarem.",
                    }
            messages.append(
                ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    tool_call_id=tool_call["id"],
                )
            )                                        
    else:
        # Pede uma resposta final sem ferramentas para evitar um ciclo infinito.
        result = await model.ainvoke(messages)

    content = result.content
    if isinstance(content, str):
        return content
    return "".join(
        str(part.get("text", "")) if isinstance(part, dict) else str(part)
        for part in content
    )
