import json
from datetime import datetime, timedelta
from models import *

class DatabaseSimulada:
    """Simula um banco de dados com arquivos JSON"""
    
    def __init__(self):
        # Carregar dados dos arquivos
        with open('../data/trechos.json') as f:
            self.trechos = json.load(f)
        with open('../data/manutencoes.json') as f:
            self.manutencoes = json.load(f)
        with open('../data/clima.json') as f:
            self.clima = json.load(f)
    
    def get_trecho(self, trecho_id):
        return next((t for t in self.trechos if t['id'] == trecho_id), None)
    
    def get_ultima_manutencao(self, trecho_id):
        """Retorna a última manutenção de um trecho"""
        manutencoes_trecho = [m for m in self.manutencoes if m['trecho_id'] == trecho_id]
        if not manutencoes_trecho:
            return None
        return max(manutencoes_trecho, key=lambda m: m['data'])
    
    def get_dias_desde_manutencao(self, trecho_id):
        """Calcula dias desde última manutenção"""
        ultima = self.get_ultima_manutencao(trecho_id)
        if not ultima:
            return 999  # Muito tempo (nunca foi mantido)
        data_manutencao = datetime.strptime(ultima['data'], '%Y-%m-%d')
        dias = (datetime.now() - data_manutencao).days
        return dias
    
    def get_clima_atual(self):
        """Retorna o clima mais recente"""
        if not self.clima:
            return None
        return max(self.clima, key=lambda c: c['data'])

db = DatabaseSimulada()