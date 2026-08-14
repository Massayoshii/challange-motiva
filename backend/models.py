from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Trecho:
    id: int
    nome: str
    km_inicio: float
    km_fim: float
    tipo_vegetacao: str
    risco_base: float


@dataclass
class Manutencao:
    id: int
    trecho_id: int
    data: str
    tipo: str
    dias_duracao: int
    custo: float


@dataclass
class DadosClimaticos:
    data: str
    temperatura_media: float
    chuva_mm: float
    umidade: float


@dataclass
class StatusTrecho:
    trecho_id: int
    dias_desde_manutencao: int
    crescimento_estimado: float
    fator_clima: float
    urgencia: float
    cor: str
    proxima_intervencao_dias: int
    risco_atual: str


@dataclass
class ItemCronograma:
    data: datetime
    trecho_id: int
    nome_trecho: str
    equipe_id: int
    prioridade: str
    tempo_estimado_horas: float
    custo_estimado: float