from datetime import datetime, timedelta
from models import ItemCronograma
from logic import calc_urgencia
from database import db

class GeradorCronograma:
    """Gera cronograma automático de manutenções"""
    
    def __init__(self, num_equipes=3, horas_por_dia=8):
        self.num_equipes = num_equipes
        self.horas_por_dia = horas_por_dia
    
    def obter_trechos_ordenados(self):
        """
        Retorna trechos ordenados por urgência
        (mais urgentes primeiro)
        """
        trechos_com_urgencia = []
        
        for trecho in db.trechos:
            status = calc_urgencia.get_status_trecho(trecho['id'])
            trechos_com_urgencia.append((trecho, status))
        
        # Ordenar por urgência decrescente
        trechos_com_urgencia.sort(
            key=lambda x: x[1].urgencia,
            reverse=True
        )
        
        return trechos_com_urgencia
    
    def gerar_cronograma_semana(self, data_inicio=None):
        """
        Gera cronograma para uma semana
        """
        if data_inicio is None:
            data_inicio = datetime.now()
        
        # Pegar trechos ordenados por urgência
        trechos_ordenados = self.obter_trechos_ordenados()
        
        cronograma = []
        data_atual = data_inicio
        
        # Considerar apenas trechos com urgência > 40
        trechos_para_intervir = [
            t for t, status in trechos_ordenados 
            if status.urgencia > 40
        ]
        
        # Se não há trechos para intervir
        if not trechos_para_intervir:
            return cronograma
        
        equipe_atual = 1
        horas_alocadas_dia = 0
        
        for trecho in trechos_para_intervir:
            status = calc_urgencia.get_status_trecho(trecho['id'])
            
            # Tempo estimado: 2h por trecho (pode variar)
            tempo_estimado = 2.0
            custo_estimado = 500  # Base
            
            # Se urgência for alta, pode levar mais tempo
            if status.urgencia > 70:
                tempo_estimado = 3.0
                custo_estimado = 750
            
            # Se passou do limite de horas do dia, próximo dia
            if horas_alocadas_dia + tempo_estimado > self.horas_por_dia:
                data_atual += timedelta(days=1)
                horas_alocadas_dia = 0
                equipe_atual = 1
            
            # Adicionar ao cronograma
            item = ItemCronograma(
                data=data_atual,
                trecho_id=trecho['id'],
                nome_trecho=trecho['nome'],
                equipe_id=equipe_atual,
                prioridade=status.risco_atual,
                tempo_estimado_horas=tempo_estimado,
                custo_estimado=custo_estimado
            )
            
            cronograma.append(item)
            
            # Atualizar alocação
            horas_alocadas_dia += tempo_estimado
            
            # Alternar equipe
            equipe_atual = (equipe_atual % self.num_equipes) + 1
        
        return cronograma
    
    def gerar_relatorio_cronograma(self, cronograma):
        """Gera relatório em formato texto"""
        
        relatorio = "CRONOGRAMA DE MANUTENÇÃO - SEMANA\n"
        relatorio += "=" * 60 + "\n\n"
        
        # Agrupar por dia
        dias = {}
        for item in cronograma:
            dia = item.data.strftime('%d/%m/%Y')
            if dia not in dias:
                dias[dia] = []
            dias[dia].append(item)
        
        # Gerar relatório por dia
        total_horas = 0
        total_custo = 0
        
        for dia in sorted(dias.keys()):
            itens_dia = dias[dia]
            
            relatorio += f"📅 {dia}\n"
            relatorio += "-" * 60 + "\n"
            
            horas_dia = 0
            custo_dia = 0
            
            for item in itens_dia:
                relatorio += f"  • Equipe {item.equipe_id} → {item.nome_trecho}\n"
                relatorio += f"    Prioridade: {item.prioridade} | "
                relatorio += f"Tempo: {item.tempo_estimado_horas}h | "
                relatorio += f"Custo: R$ {item.custo_estimado}\n\n"
                
                horas_dia += item.tempo_estimado_horas
                custo_dia += item.custo_estimado
            
            relatorio += f"  Resumo do dia: {horas_dia}h | Custo: R$ {custo_dia}\n"
            relatorio += "\n"
            
            total_horas += horas_dia
            total_custo += custo_dia
        
        relatorio += "=" * 60 + "\n"
        relatorio += f"TOTAL SEMANAL: {total_horas}h | Custo: R$ {total_custo}\n"
        relatorio += f"Equipes necessárias: {self.num_equipes}\n"
        
        return relatorio

# Instância global
gerador = GeradorCronograma(num_equipes=3)