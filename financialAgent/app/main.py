import logging
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.core.api import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Agent Finance API",
    description="API de chat com modelos da OpenRouter usando LangChain.",
    version="1.0.0",
    # Documentação interativa desligada: o agente não é público.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Sem CORS: o navegador nunca chama o agente; só o backend, com o segredo compartilhado.
_shared_secret = get_settings().agent_shared_secret.get_secret_value()
if len(_shared_secret) < 32:
    raise RuntimeError("AGENT_SHARED_SECRET precisa ter pelo menos 32 caracteres (o mesmo do backend).")


@app.middleware("http")
async def require_internal_token(request: Request, call_next):
    if request.url.path != "/health":
        token = request.headers.get("x-internal-token", "")
        if not secrets.compare_digest(token.encode(), _shared_secret.encode()):
            return JSONResponse({"detail": "Não autorizado."}, status_code=401)
    return await call_next(request)


app.include_router(router)
