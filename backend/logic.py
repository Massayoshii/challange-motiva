from datetime import datetime, timedelta
from models import StatusTrecho
from database import db

class CalculadorUrgencia:
    """Calcula a urgência e status de cada trecho"""
    
    # Configurações
    CICLO_IDEAL_DIAS = 30  # Manutenção a cada 30 dias
    CRESCIMENTO_POR_DIA = 2.0  # % por dia (base)
    
    def calcular_fator_clima(self, trecho_id):
        """
        Calcula multiplicador climático
        Chuva + calor = crescimento mais rápido
        """
        clima = db.get_clima_atual()
        if not clima:
            return 1.0
        
        fator = 1.0
        
        # Chuva acelera crescimento
        if clima['chuva_mm'] > 30:
            fator += 0.5
        elif clima['chuva_mm'] > 15:
            fator += 0.25
        
        # Temperatura quente acelera
        if clima['temperatura_media'] > 28:
            fator += 0.3
        elif clima['temperatura_media'] > 25:
            fator += 0.15
        
        return min(fator, 2.0)  # Máximo 2.0
    
    def calcular_crescimento_estimado(self, trecho_id):
        """
        Calcula % de crescimento estimado da vegetação
        Baseado em: dias desde manutenção + clima
        """
        dias = db.get_dias_desde_manutencao(trecho_id)
        trecho = db.get_trecho(trecho_id)
        
        # Taxa de crescimento base (depende do tipo)
        taxa_base = {
            "agressiva": 3.5,      # 3.5% por dia
            "moderada": 2.0,       # 2.0% por dia
            "baixa": 1.0           # 1.0% por dia
        }
        
        taxa = taxa_base.get(trecho['tipo_vegetacao'], 2.0)
        
        # Aplicar fator climático
        fator_clima = self.calcular_fator_clima(trecho_id)
        
        # Crescimento = taxa × dias × fator climático
        crescimento = taxa * dias * fator_clima
        
        # Máximo 100%
        return min(crescimento, 100.0)
    
    def calcular_urgencia(self, trecho_id):
        """
        Calcula nível de urgência (0-100)
        """
        dias = db.get_dias_desde_manutencao(trecho_id)
        crescimento = self.calcular_crescimento_estimado(trecho_id)
        trecho = db.get_trecho(trecho_id)
        
        # Fórmula: (dias/ciclo) × 50 + crescimento × 50
        urgencia = (dias / self.CICLO_IDEAL_DIAS) * 50 + (crescimento / 100) * 50
        
        # Adicionar risco base do trecho
        urgencia += trecho['risco_base'] * 10
        
        return min(urgencia, 100.0)
    
    def get_cor(self, urgencia):
        """Retorna cor baseada em urgência"""
        if urgencia >= 70:
            return "vermelho"
        elif urgencia >= 40:
            return "amarelo"
        else:
            return "verde"
    
    def get_risco(self, urgencia):
        """Retorna nível de risco textual"""
        if urgencia >= 70:
            return "ALTO"
        elif urgencia >= 40:
            return "MÉDIO"
        else:
            return "BAIXO"
    
    def calcular_dias_proxima_intervencao(self, trecho_id):
        """
        Calcula em quantos dias a próxima intervenção será necessária
        """
        crescimento = self.calcular_crescimento_estimado(trecho_id)
        
        # Se ainda não atingiu ponto crítico (80%), calcular tempo
        if crescimento < 80:
            # Quanto falta para atingir 80%?
            falta = 80 - crescimento
            taxa_diaria = self.CRESCIMENTO_POR_DIA
            dias = falta / taxa_diaria
            return max(int(dias), 1)
        else:
            return 0  # Intervir imediatamente
    
    def get_status_trecho(self, trecho_id):
        """Retorna o status completo de um trecho"""
        urgencia = self.calcular_urgencia(trecho_id)
        crescimento = self.calcular_crescimento_estimado(trecho_id)
        dias_manutencao = db.get_dias_desde_manutencao(trecho_id)
        
        return StatusTrecho(
            trecho_id=trecho_id,
            dias_desde_manutencao=dias_manutencao,
            crescimento_estimado=round(crescimento, 1),
            fator_clima=round(self.calcular_fator_clima(trecho_id), 2),
            urgencia=round(urgencia, 1),
            cor=self.get_cor(urgencia),
            proxima_intervencao_dias=self.calcular_dias_proxima_intervencao(trecho_id),
            risco_atual=self.get_risco(urgencia)
        )

# Instância global
calc_urgencia = CalculadorUrgencia()