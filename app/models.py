from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from .database import Base


class Pokemon(Base):
    __tablename__ = "pokemons"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    apelido = Column(String, nullable=True)
    tipos = Column(String, nullable=False)  # ex: "electric,flying"
    hp = Column(Integer, default=0)
    ataque = Column(Integer, default=0)
    defesa = Column(Integer, default=0)
    velocidade = Column(Integer, default=0)
    imagem_url = Column(String, nullable=True)
    anotacoes = Column(String, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
