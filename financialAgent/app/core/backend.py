"""Cliente HTTP das ferramentas. Regras financeiras ficam no backend Node.js."""

from typing import Any
from urllib.parse import quote

import httpx

from app.config.settings import get_settings


def path_id(value: str) -> str:
    # IDs sempre ocupam um único segmento, sem permitir injetar rota/query.
    return quote(value, safe="") if value not in ("", ".", "..") else "invalid-id"


def payload(values: dict[str, Any], *exclude: str) -> dict[str, Any]:
    """Omite campos não informados, preservando false, zero e strings vazias."""
    return {key: value for key, value in values.items() if value is not None and key not in exclude}


def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    filters = payload(params or {})
    try:
        # Sem retries: um timeout em escrita pode ocorrer depois do commit.
        with httpx.Client(timeout=settings.backend_timeout_seconds, follow_redirects=False) as client:
            response = client.request(
                method, settings.backend_api_url.rstrip("/") + path,
                params=filters, json=body,
                headers={"X-Internal-Token": settings.agent_shared_secret.get_secret_value()},
            )
    except httpx.RequestError:
        return {
            "ok": False,
            "error": "Não foi possível receber a resposta do backend.",
            "outcome_unknown": method != "GET",
            "guidance": "Em operações de escrita, consulte os registros antes de tentar novamente.",
        }

    if response.status_code == 204:
        data = None
    else:
        try:
            data = response.json()
        except ValueError:
            return {
                "ok": False, "status_code": response.status_code,
                "error": "O backend retornou uma resposta que não é JSON.",
                "outcome_unknown": method != "GET",
            }
    if not response.is_success:
        return {
            "ok": False, "status_code": response.status_code,
            "error": data.get("error", "Falha na API financeira.") if isinstance(data, dict) else "Falha na API financeira.",
            "outcome_unknown": method != "GET" and response.status_code >= 500,
        }
    result: dict[str, Any] = {"ok": True, "status_code": response.status_code, "data": data}
    if method == "GET":
        result["filters"] = filters
        if "limit" in filters and isinstance(data, list):
            # A API não fornece count total; página cheia pode ter continuação.
            more = len(data) == filters["limit"]
            result["pagination"] = {
                "limit": filters["limit"], "offset": filters.get("offset", 0),
                "returned": len(data), "has_more_possible": more,
                "next_offset": filters.get("offset", 0) + len(data) if more else None,
            }
    return result
