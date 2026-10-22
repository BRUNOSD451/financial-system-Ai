import logging
from time import monotonic
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from openai import APIStatusError
from app.core.conversations import conversation_store

from app.core.openrouter import (
    OpenRouterNotConfiguredError,
    generate_chat_response,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(
        min_length=1,
        max_length=12_000,
        description="Mensagem enviada ao modelo.",
    )
    conversation_id: UUID | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    conversation_id, conversation = conversation_store.begin(
        str(request.conversation_id) if request.conversation_id else None
    )
    try:
        reply = await generate_chat_response(request.message, list(conversation.messages))
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("Resposta vazia do provedor.")
        conversation.messages.extend([
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply[:12_000]},
        ])
    except OpenRouterNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except APIStatusError as exc:
        logger.warning("Provedor de IA retornou HTTP %s", exc.status_code)
        detail = (
            "A OpenRouter recusou a chamada por créditos insuficientes para o limite de tokens solicitado. "
            "Reduza OPENROUTER_MAX_TOKENS no .env do agente ou adicione créditos na OpenRouter."
            if exc.status_code == 402
            else "O provedor de IA recusou a solicitação. Tente novamente mais tarde."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except Exception as exc:
        logger.exception("Falha ao consultar a OpenRouter")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível obter uma resposta do provedor de IA.",
        ) from exc

    finally:
        conversation.busy = False
        conversation.touched = monotonic()
        if not conversation.messages:
            conversation_store.delete(conversation_id)

    return ChatResponse(reply=reply, conversation_id=conversation_id)


@router.delete("/api/conversations/{conversation_id}", status_code=204, tags=["chat"])
async def clear_conversation(conversation_id: UUID):
    conversation_store.delete(str(conversation_id))
    return Response(status_code=204)
