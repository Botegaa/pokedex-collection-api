from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .pokeapi_client import PokeAPIError, buscar_pokemon
from .secundaria_client import solicitar_comparacao

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Principal - Meu Pokédex",
    description=(
        "Gerencia uma coleção pessoal de Pokémons. Ao adicionar um Pokémon, "
        "os dados são buscados na PokeAPI (serviço externo). Para comparar "
        "dois Pokémons, esta API delega o cálculo para a API secundária."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_out(p: models.Pokemon) -> dict:
    return {
        "id": p.id,
        "nome": p.nome,
        "apelido": p.apelido,
        "tipos": p.tipos.split(",") if p.tipos else [],
        "hp": p.hp,
        "ataque": p.ataque,
        "defesa": p.defesa,
        "velocidade": p.velocidade,
        "imagem_url": p.imagem_url,
        "anotacoes": p.anotacoes,
        "criado_em": p.criado_em,
    }


@app.get("/", tags=["Status"])
def raiz():
    return {
        "servico": "API Principal - Meu Pokédex",
        "status": "online",
        "documentacao_interativa": "/docs",
    }


@app.post("/pokemons", response_model=schemas.PokemonOut, status_code=201, tags=["Pokémons"])
def criar_pokemon(payload: schemas.PokemonCreate, db: Session = Depends(get_db)):
    """Busca o Pokémon na PokeAPI (serviço externo) e o salva na coleção pessoal."""
    try:
        dados = buscar_pokemon(payload.nome)
    except PokeAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    pokemon = models.Pokemon(
        nome=dados["nome"],
        apelido=payload.apelido,
        tipos=",".join(dados["tipos"]),
        hp=dados["hp"],
        ataque=dados["ataque"],
        defesa=dados["defesa"],
        velocidade=dados["velocidade"],
        imagem_url=dados["imagem_url"],
        anotacoes=payload.anotacoes,
    )
    db.add(pokemon)
    db.commit()
    db.refresh(pokemon)
    return _to_out(pokemon)


@app.get("/pokemons", response_model=List[schemas.PokemonOut], tags=["Pokémons"])
def listar_pokemons(
    tipo: Optional[str] = Query(None, description="Filtra por tipo, ex.: fire, water, electric"),
    ordenar_por: Optional[str] = Query(None, description="hp, ataque, defesa ou velocidade"),
    ordem: str = Query("desc", description="asc ou desc"),
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista os Pokémons salvos, com filtro por tipo, ordenação e paginação (funcionalidades extras)."""
    query = db.query(models.Pokemon)

    if tipo:
        query = query.filter(models.Pokemon.tipos.like(f"%{tipo.lower()}%"))

    campos_validos = {
        "hp": models.Pokemon.hp,
        "ataque": models.Pokemon.ataque,
        "defesa": models.Pokemon.defesa,
        "velocidade": models.Pokemon.velocidade,
    }
    if ordenar_por in campos_validos:
        coluna = campos_validos[ordenar_por]
        query = query.order_by(desc(coluna) if ordem == "desc" else asc(coluna))
    else:
        query = query.order_by(models.Pokemon.id.asc())

    offset = (pagina - 1) * tamanho_pagina
    resultados = query.offset(offset).limit(tamanho_pagina).all()
    return [_to_out(p) for p in resultados]


@app.get("/pokemons/{pokemon_id}", response_model=schemas.PokemonOut, tags=["Pokémons"])
def obter_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    pokemon = db.query(models.Pokemon).filter(models.Pokemon.id == pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon não encontrado.")
    return _to_out(pokemon)


@app.put("/pokemons/{pokemon_id}", response_model=schemas.PokemonOut, tags=["Pokémons"])
def atualizar_pokemon(pokemon_id: int, payload: schemas.PokemonUpdate, db: Session = Depends(get_db)):
    pokemon = db.query(models.Pokemon).filter(models.Pokemon.id == pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon não encontrado.")

    if payload.apelido is not None:
        pokemon.apelido = payload.apelido
    if payload.anotacoes is not None:
        pokemon.anotacoes = payload.anotacoes

    db.commit()
    db.refresh(pokemon)
    return _to_out(pokemon)


@app.delete("/pokemons/{pokemon_id}", status_code=204, tags=["Pokémons"])
def remover_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    pokemon = db.query(models.Pokemon).filter(models.Pokemon.id == pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon não encontrado.")

    db.delete(pokemon)
    db.commit()
    return None


@app.post("/pokemons/comparar", tags=["Batalhas"])
def comparar_pokemons(payload: schemas.CompararRequest, db: Session = Depends(get_db)):
    """
    Busca dois Pokémons da coleção e envia os dados para a API secundária,
    que calcula a efetividade de tipos e aponta o provável vencedor.
    """
    p1 = db.query(models.Pokemon).filter(models.Pokemon.id == payload.pokemon_id_1).first()
    p2 = db.query(models.Pokemon).filter(models.Pokemon.id == payload.pokemon_id_2).first()

    if not p1 or not p2:
        raise HTTPException(status_code=404, detail="Um dos Pokémons informados não foi encontrado na coleção.")

    pokemon_1 = {
        "nome": p1.apelido or p1.nome,
        "tipos": p1.tipos.split(","),
        "hp": p1.hp,
        "ataque": p1.ataque,
        "defesa": p1.defesa,
        "velocidade": p1.velocidade,
    }
    pokemon_2 = {
        "nome": p2.apelido or p2.nome,
        "tipos": p2.tipos.split(","),
        "hp": p2.hp,
        "ataque": p2.ataque,
        "defesa": p2.defesa,
        "velocidade": p2.velocidade,
    }

    try:
        resultado = solicitar_comparacao(pokemon_1, pokemon_2, payload.anotacoes)
    except ConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return resultado
