"""
Cliente para a PokeAPI (https://pokeapi.co) — o serviço externo consumido
por este MVP. A PokeAPI é pública, gratuita e não exige cadastro/API key.

Este módulo consome e trata os dados da PokeAPI dentro da nossa própria
aplicação (nenhum redirecionamento é feito para o usuário final).
"""
import httpx

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"


class PokeAPIError(Exception):
    """Erro ao consultar ou interpretar dados da PokeAPI."""


def buscar_pokemon(nome: str) -> dict:
    nome = nome.lower().strip()
    if not nome:
        raise PokeAPIError("O nome do Pokémon não pode ser vazio.")

    try:
        resposta = httpx.get(f"{POKEAPI_BASE_URL}/pokemon/{nome}", timeout=10.0)
    except httpx.RequestError as exc:
        raise PokeAPIError(f"Não foi possível conectar à PokeAPI: {exc}") from exc

    if resposta.status_code == 404:
        raise PokeAPIError(f"Pokémon '{nome}' não foi encontrado na PokeAPI.")

    try:
        resposta.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PokeAPIError(f"Erro ao consultar a PokeAPI: {exc}") from exc

    dados = resposta.json()

    tipos = [t["type"]["name"] for t in dados.get("types", [])]
    stats = {s["stat"]["name"]: s["base_stat"] for s in dados.get("stats", [])}

    return {
        "nome": dados.get("name", nome),
        "tipos": tipos,
        "hp": stats.get("hp", 0),
        "ataque": stats.get("attack", 0),
        "defesa": stats.get("defense", 0),
        "velocidade": stats.get("speed", 0),
        "imagem_url": (dados.get("sprites") or {}).get("front_default"),
    }
