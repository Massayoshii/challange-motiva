from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from models import ItemCronograma
from logic import calc_urgencia
from database import db


class GeradorCronograma:

    def __init__(self, num_equipes: int = 3, horas_por_dia: float = 8.0):
        self.num_equipes = num_equipes
        self.horas_por_dia = horas_por_dia

        print(f"✓ Gerador de Cronograma criado:")
        print(f"  - Equipes disponíveis: {num_equipes}")
        print(f"  - Horas por dia: {horas_por_dia}h\n")

    def obter_trechos_ordenados(self) -> List[Tuple]:
        return calc_urgencia.get_trechos_ordenados_por_urgencia(descendente=True)

    def filtrar_trechos_para_intervir(
        self,
        trechos_ordenados: List[Tuple],
        limiar_urgencia: float = 40
    ) -> List[Tuple]:

        trechos_filtrados = [
            (t, s) for t, s in trechos_ordenados
            if s.urgencia >= limiar_urgencia
        ]

        return trechos_filtrados

    def calcular_tempo_estimado(self, trecho: Dict, status) -> float:

        urgencia = status.urgencia

        if urgencia >= 70:
            tempo = 4.0
        elif urgencia >= 50:
            tempo = 3.0
        else:
            tempo = 2.0

        if trecho['tipo_vegetacao'] == 'agressiva':
            tempo += 0.5
        elif trecho['tipo_vegetacao'] == 'baixa':
            tempo -= 0.5

        return max(tempo, 1.5)

    def calcular_custo_estimado(
        self,
        trecho: Dict,
        tempo_horas: float
    ) -> float:

        valor_hora = 150.0
        overhead = 100.0

        custo = (tempo_horas * valor_hora) + overhead

        return custo

    def gerar_cronograma_semana(
        self,
        data_inicio: Optional[datetime] = None
    ) -> List[ItemCronograma]:

        if data_inicio is None:
            data_inicio = datetime.now()

        trechos_ordenados = self.obter_trechos_ordenados()

        trechos_para_intervir = self.filtrar_trechos_para_intervir(
            trechos_ordenados
        )

        if not trechos_para_intervir:
            print("ℹ️  Nenhum trecho precisa de intervenção esta semana")
            return []

        cronograma = []
        data_atual = data_inicio
        equipe_atual = 1
        horas_alocadas_dia = 0

        for trecho, status in trechos_para_intervir:

            tempo_estimado = self.calcular_tempo_estimado(trecho, status)
            custo_estimado = self.calcular_custo_estimado(
                trecho,
                tempo_estimado
            )

            if horas_alocadas_dia + tempo_estimado > self.horas_por_dia:
                data_atual += timedelta(days=1)
                horas_alocadas_dia = 0
                equipe_atual = 1

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

            horas_alocadas_dia += tempo_estimado
            equipe_atual = (equipe_atual % self.num_equipes) + 1

        return cronograma

    def gerar_relatorio_cronograma(
        self,
        cronograma: List[ItemCronograma]
    ) -> str:

        relatorio = ""
        relatorio += "┌" + "─" * 78 + "┐\n"
        relatorio += "│" + " " * 78 + "│\n"
        relatorio += "│" + "  CRONOGRAMA SEMANAL DE MANUTENÇÃO - MOTIVA CCR".center(78) + "│\n"
        relatorio += "│" + " " * 78 + "│\n"
        relatorio += "└" + "─" * 78 + "┘\n\n"

        if not cronograma:
            relatorio += "✅ Nenhuma intervenção necessária esta semana!\n"
            return relatorio

        dias = {}

        for item in cronograma:
            dia_str = item.data.strftime('%d/%m/%Y (%A)')

            if dia_str not in dias:
                dias[dia_str] = []

            dias[dia_str].append(item)

        dias_traducao = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }

        total_horas = 0
        total_custo = 0

        for dia_original in sorted(dias.keys()):

            partes = dia_original.split('(')
            data_parte = partes[0].strip()
            dia_eng = partes[1].replace(')', '').strip() if len(partes) > 1 else ''
            dia_pt = dias_traducao.get(dia_eng, dia_eng)

            itens_dia = dias[dia_original]

            relatorio += f"\n📅 {data_parte} ({dia_pt})\n"
            relatorio += "─" * 80 + "\n"

            horas_dia = 0
            custo_dia = 0

            for idx, item in enumerate(itens_dia, 1):

                if item.prioridade == "ALTO":
                    emoji = "🔴"
                elif item.prioridade == "MÉDIO":
                    emoji = "🟡"
                else:
                    emoji = "🟢"

                relatorio += f"  {idx}. {emoji} Equipe {item.equipe_id} → {item.nome_trecho}\n"
                relatorio += (
                    f"     Prioridade: {item.prioridade:6} | "
                    f"Tempo: {item.tempo_estimado_horas:.1f}h | "
                    f"Custo: R$ {item.custo_estimado:.2f}\n"
                )
                relatorio += "\n"

                horas_dia += item.tempo_estimado_horas
                custo_dia += item.custo_estimado

            relatorio += (
                f"  📊 Resumo do dia: {horas_dia:.1f}h de trabalho | "
                f"Custo: R$ {custo_dia:.2f}\n"
            )
            relatorio += "\n"

            total_horas += horas_dia
            total_custo += custo_dia

        relatorio += "┌" + "─" * 78 + "┐\n"
        relatorio += "│" + " RESUMO SEMANAL".ljust(79) + "│\n"
        relatorio += "├" + "─" * 78 + "┤\n"
        relatorio += f"│  Total de trechos a intervir: {len(cronograma):2d}                                                  │\n"
        relatorio += f"│  Total de horas: {total_horas:.1f}h                                                        │\n"
        relatorio += f"│  Equipes necessárias: {self.num_equipes}                                                               │\n"
        relatorio += f"│  Custo total estimado: R$ {total_custo:.2f}                                              │\n"
        relatorio += "└" + "─" * 78 + "┘\n"

        return relatorio

    def get_cronograma_como_lista(
        self,
        cronograma: List[ItemCronograma]
    ) -> List[Dict]:

        lista = []

        for item in cronograma:
            lista.append({
                'data': item.data.strftime('%d/%m/%Y'),
                'hora': item.data.strftime('%H:%M'),
                'trecho': item.nome_trecho,
                'equipe': item.equipe_id,
                'prioridade': item.prioridade,
                'tempo_horas': item.tempo_estimado_horas,
                'custo_reais': item.custo_estimado
            })

        return lista

    def gerar_analise_impacto(
        self,
        cronograma: List[ItemCronograma]
    ) -> Dict:

        custo_otimizado_semana = sum(
            item.custo_estimado for item in cronograma
        )
        custo_otimizado_mes = custo_otimizado_semana * 4

        todos_trechos = db.get_todos_trechos()
        custo_fixo_semana = len(todos_trechos) * 2.5 * 150
        custo_fixo_mes = custo_fixo_semana * 4

        economia_semana = custo_fixo_semana - custo_otimizado_semana
        economia_mes = custo_fixo_mes - custo_otimizado_mes

        percentual = (
            (economia_mes / custo_fixo_mes) * 100
            if custo_fixo_mes > 0
            else 0
        )

        return {
            'custo_otimizado_semana': custo_otimizado_semana,
            'custo_otimizado_mes': custo_otimizado_mes,
            'custo_fixo_semana': custo_fixo_semana,
            'custo_fixo_mes': custo_fixo_mes,
            'economia_semana': economia_semana,
            'economia_mes': economia_mes,
            'percentual_economia': percentual
        }


try:
    gerador = GeradorCronograma(num_equipes=3, horas_por_dia=8)
except Exception as e:
    print(f"❌ Erro ao inicializar gerador: {e}")
    gerador = None


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTE DO GERADOR DE CRONOGRAMA")
    print("="*80 + "\n")

    if gerador is None:
        print("❌ Gerador não inicializado")
    else:
        print("📅 TESTE 1: Gerando Cronograma da Semana")
        print("-" * 80)

        cronograma = gerador.gerar_cronograma_semana()

        if cronograma:
            print(f"✓ Cronograma gerado com {len(cronograma)} itens\n")
        else:
            print("ℹ️  Nenhuma intervenção necessária\n")

        print("\n📊 TESTE 2: Relatório Completo")
        print("-" * 80)

        if cronograma:
            relatorio = gerador.gerar_relatorio_cronograma(cronograma)
            print(relatorio)

        print("\n💰 TESTE 3: Análise de Impacto Financeiro")
        print("-" * 80)

        analise = gerador.gerar_analise_impacto(cronograma)

        print(f"\nCronograma Inteligente (Otimizado):")
        print(f"  Custo semanal: R$ {analise['custo_otimizado_semana']:.2f}")
        print(f"  Custo mensal: R$ {analise['custo_otimizado_mes']:.2f}")

        print(f"\nCronograma Fixo (Situação Atual):")
        print(f"  Custo semanal: R$ {analise['custo_fixo_semana']:.2f}")
        print(f"  Custo mensal: R$ {analise['custo_fixo_mes']:.2f}")

        print(f"\n🎯 ECONOMIA:")
        print(f"  Semanal: R$ {analise['economia_semana']:.2f}")
        print(f"  Mensal: R$ {analise['economia_mes']:.2f}")
        print(f"  Percentual: {analise['percentual_economia']:.1f}%")

        print("\n\n📋 TESTE 4: Cronograma como Lista (para exportar)")
        print("-" * 80)

        if cronograma:
            lista = gerador.get_cronograma_como_lista(cronograma)

            print(
                f"\n{'Data':10} | {'Trecho':25} | {'Equipe':6} | "
                f"{'Prior':7} | {'Tempo':5} | {'Custo'}"
            )
            print("-" * 80)

            for item in lista[:5]:
                print(
                    f"{item['data']:10} | {item['trecho'][:25]:25} | "
                    f"{item['equipe']:6} | {item['prioridade']:7} | "
                    f"{item['tempo_horas']:5.1f} | "
                    f"R$ {item['custo_reais']:7.2f}"
                )

            if len(lista) > 5:
                print(f"... (+{len(lista)-5} mais)")

        print("\n✅ Todos os testes concluídos com sucesso!")