from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Trecho:
    """Representa um trecho de rodovia"""
    id: int
    nome: str
    km_inicio: float
    km_fim: float
    tipo_vegetacao: str  # "agressiva", "moderada", "baixa"
    risco_base: float  # 0-1 (risco natural do local)
    
@dataclass
class Manutencao:
    """Registro de manutenção realizada"""
    id: int
    trecho_id: int
    data: datetime
    tipo: str  # "roçada", "poda", "limpeza"
    dias_duracao: int
    custo: float

@dataclass
class DadosClimaticos:
    """Dados climáticos por data"""
    data: datetime
    temperatura_media: float
    chuva_mm: float
    umidade: float

@dataclass
class StatusTrecho:
    """Status atual de um trecho (calculado)"""
    trecho_id: int
    dias_desde_manutencao: int
    crescimento_estimado: float  # 0-100%
    fator_clima: float  # multiplicador 0.5-2.0
    urgencia: float  # 0-100
    cor: str  # "verde", "amarelo", "vermelho"
    proxima_intervencao_dias: int
    risco_atual: str  # "BAIXO", "MÉDIO", "ALTO"

@dataclass
class ItemCronograma:
    """Um item do cronograma de manutenção"""
    data: datetime
    trecho_id: int
    nome_trecho: str
    equipe_id: int
    prioridade: str  # "URGENTE", "ALTO", "MÉDIO"
    tempo_estimado_horas: float
    custo_estimado: float