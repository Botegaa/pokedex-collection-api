from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PokemonCreate(BaseModel):
    nome: str = Field(..., examples=["pikachu"], description="Nome do Pokémon a ser buscado na PokeAPI")
    apelido: Optional[str] = Field(None, examples=["Pikas"])
    anotacoes: Optional[str] = Field(None, examples=["Capturado na rota 1"])


class PokemonUpdate(BaseModel):
    apelido: Optional[str] = None
    anotacoes: Optional[str] = None


class PokemonOut(BaseModel):
    id: int
    nome: str
    apelido: Optional[str] = None
    tipos: List[str]
    hp: int
    ataque: int
    defesa: int
    velocidade: int
    imagem_url: Optional[str] = None
    anotacoes: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class CompararRequest(BaseModel):
    pokemon_id_1: int = Field(..., description="ID (na sua coleção) do primeiro Pokémon")
    pokemon_id_2: int = Field(..., description="ID (na sua coleção) do segundo Pokémon")
    anotacoes: Optional[str] = Field(None, description="Observações sobre esta comparação")
