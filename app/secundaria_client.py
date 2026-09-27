"""Cliente HTTP para conversar com a API secundária (calculadora de batalhas)."""
import os
from typing import Optional

import httpx

API_SECUNDARIA_URL = os.getenv("API_SECUNDARIA_URL", "http://localhost:8001")


def solicitar_comparacao(pokemon_1: dict, pokemon_2: dict, anotacoes: Optional[str] = None) -> dict:
    payload = {
        "pokemon_1": pokemon_1,
        "pokemon_2": pokemon_2,
        "anotacoes": anotacoes,
    }
    try:
        resposta = httpx.post(f"{API_SECUNDARIA_URL}/comparacoes", json=payload, timeout=10.0)
        resposta.raise_for_status()
    except httpx.RequestError as exc:
        raise ConnectionError(
            f"Não foi possível conectar à API secundária em {API_SECUNDARIA_URL}: {exc}"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise ConnectionError(f"A API secundária retornou um erro: {exc}") from exc

    return resposta.json()
