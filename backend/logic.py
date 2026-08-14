from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import StatusTrecho
from database import db


class CalculadorUrgencia:

    CICLO_IDEAL_DIAS = 30
    CRESCIMENTO_BASE_POR_DIA = 2.0

    TAXA_CRESCIMENTO = {
        "agressiva": 3.5,
        "moderada": 2.0,
        "baixa": 1.0
    }

    LIMITE_VERMELHO = 70
    LIMITE_AMARELO = 40

    def calcular_fator_clima(self, trecho_id: int) -> float:
        clima = db.get_clima_atual()

        if clima is None:
            return 1.0

        fator = 1.0

        if clima['chuva_mm'] > 30:
            fator += 0.5
        elif clima['chuva_mm'] > 15:
            fator += 0.25

        if clima['temperatura_media'] > 28:
            fator += 0.3
        elif clima['temperatura_media'] > 25:
            fator += 0.15

        return min(fator, 2.0)

    def calcular_crescimento_estimado(self, trecho_id: int) -> float:
        dias = db.get_dias_desde_manutencao(trecho_id)
        trecho = db.get_trecho(trecho_id)

        if trecho is None:
            return 0.0

        tipo_vegetacao = trecho['tipo_vegetacao']
        taxa_base = self.TAXA_CRESCIMENTO.get(tipo_vegetacao, 2.0)

        fator_clima = self.calcular_fator_clima(trecho_id)

        crescimento = taxa_base * dias * fator_clima

        return min(crescimento, 100.0)

    def calcular_urgencia(self, trecho_id: int) -> float:
        dias = db.get_dias_desde_manutencao(trecho_id)
        crescimento = self.calcular_crescimento_estimado(trecho_id)
        trecho = db.get_trecho(trecho_id)

        if trecho is None:
            return 0.0

        componente_dias = (dias / self.CICLO_IDEAL_DIAS) * 50
        componente_crescimento = (crescimento / 100) * 50
        componente_risco = trecho['risco_base'] * 10

        urgencia = componente_dias + componente_crescimento + componente_risco

        return min(urgencia, 100.0)

    def get_cor(self, urgencia: float) -> str:
        if urgencia >= self.LIMITE_VERMELHO:
            return "vermelho"
        elif urgencia >= self.LIMITE_AMARELO:
            return "amarelo"
        else:
            return "verde"

    def get_risco(self, urgencia: float) -> str:
        if urgencia >= self.LIMITE_VERMELHO:
            return "ALTO"
        elif urgencia >= self.LIMITE_AMARELO:
            return "MÉDIO"
        else:
            return "BAIXO"

    def calcular_dias_proxima_intervencao(self, trecho_id: int) -> int:
        crescimento = self.calcular_crescimento_estimado(trecho_id)

        if crescimento >= 80:
            return 0

        falta = 80 - crescimento
        taxa_diaria = self.TAXA_CRESCIMENTO.get("agressiva", 2.0)
        dias = falta / taxa_diaria

        return max(int(dias), 1)

    def get_status_trecho(self, trecho_id: int) -> StatusTrecho:
        urgencia = self.calcular_urgencia(trecho_id)
        crescimento = self.calcular_crescimento_estimado(trecho_id)
        dias_manutencao = db.get_dias_desde_manutencao(trecho_id)
        fator_clima = self.calcular_fator_clima(trecho_id)

        status = StatusTrecho(
            trecho_id=trecho_id,
            dias_desde_manutencao=dias_manutencao,
            crescimento_estimado=round(crescimento, 1),
            fator_clima=round(fator_clima, 2),
            urgencia=round(urgencia, 1),
            cor=self.get_cor(urgencia),
            proxima_intervencao_dias=self.calcular_dias_proxima_intervencao(trecho_id),
            risco_atual=self.get_risco(urgencia)
        )

        return status

    def get_status_todos_trechos(self) -> List[StatusTrecho]:
        todos_os_trechos = db.get_todos_trechos()
        status_list = []

        for trecho in todos_os_trechos:
            status = self.get_status_trecho(trecho['id'])
            status_list.append(status)

        return status_list

    def get_trechos_ordenados_por_urgencia(self, descendente: bool = True) -> List[tuple]:
        todos_os_trechos = db.get_todos_trechos()
        trechos_com_status = []

        for trecho in todos_os_trechos:
            status = self.get_status_trecho(trecho['id'])
            trechos_com_status.append((trecho, status))

        trechos_com_status.sort(
            key=lambda x: x[1].urgencia,
            reverse=descendente
        )

        return trechos_com_status


try:
    calc_urgencia = CalculadorUrgencia()
    print("✓ Calculador de Urgência inicializado com sucesso!\n")
except Exception as e:
    print(f"❌ Erro ao inicializar calculador: {e}")
    calc_urgencia = None


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTE DA LÓGICA DE CÁLCULO")
    print("="*70 + "\n")

    if calc_urgencia is None:
        print("❌ Calculador não inicializado")
    else:
        print("📊 TESTE 1: Status Detalhado de um Trecho")
        print("-" * 70)

        trecho_id = 1
        status = calc_urgencia.get_status_trecho(trecho_id)
        trecho = db.get_trecho(trecho_id)

        print(f"Trecho: {trecho['nome']}")
        print(f"Tipo de vegetação: {trecho['tipo_vegetacao']}")
        print(f"Risco base: {trecho['risco_base']*100:.0f}%")
        print()
        print(f"📅 Dias sem manutenção: {status.dias_desde_manutencao} dias")
        print(f"📈 Crescimento estimado: {status.crescimento_estimado}%")
        print(f"🌤️  Fator climático: {status.fator_clima}x")
        print(f"⚠️  Urgência: {status.urgencia}%")
        print(f"🎨 Cor: {status.cor}")
        print(f"🚨 Risco: {status.risco_atual}")
        print(f"📅 Próxima intervenção: {status.proxima_intervencao_dias} dias")
        print()

        print("🔴 TESTE 2: Top 3 Trechos Mais Urgentes")
        print("-" * 70)

        trechos_urgentes = calc_urgencia.get_trechos_ordenados_por_urgencia()

        for idx, (trecho, status) in enumerate(trechos_urgentes[:3], 1):
            print(f"{idx}. {trecho['nome']}")
            print(f"   Urgência: {status.urgencia}% | Risco: {status.risco_atual} | Cor: {status.cor}")
        print()

        print("🎨 TESTE 3: Distribuição de Cores (Status de Todos)")
        print("-" * 70)

        todos_status = calc_urgencia.get_status_todos_trechos()

        vermelhos = [s for s in todos_status if s.cor == "vermelho"]
        amarelos = [s for s in todos_status if s.cor == "amarelo"]
        verdes = [s for s in todos_status if s.cor == "verde"]

        print(f"🟢 Verde (OK): {len(verdes)} trechos")
        print(f"🟡 Amarelo (Atenção): {len(amarelos)} trechos")
        print(f"🔴 Vermelho (Urgente): {len(vermelhos)} trechos")
        print()

        print("🌿 TESTE 4: Urgência Média por Tipo de Vegetação")
        print("-" * 70)

        urgencia_por_tipo = {}

        for trecho in db.get_todos_trechos():
            tipo = trecho['tipo_vegetacao']
            status = calc_urgencia.get_status_trecho(trecho['id'])

            if tipo not in urgencia_por_tipo:
                urgencia_por_tipo[tipo] = []

            urgencia_por_tipo[tipo].append(status.urgencia)

        for tipo, urgencias in sorted(urgencia_por_tipo.items()):
            media = sum(urgencias) / len(urgencias)
            print(f"  {tipo.upper()}: {media:.1f}% de urgência média")
        print()

        print("🌤️  TESTE 5: Impacto do Clima Atual")
        print("-" * 70)

        clima = db.get_clima_atual()
        if clima:
            print(f"Data: {clima['data']}")
            print(f"Temperatura: {clima['temperatura_media']}°C")
            print(f"Chuva: {clima['chuva_mm']}mm")
            print(f"Umidade: {clima['umidade']}%")
            print()

            fator = calc_urgencia.calcular_fator_clima(1)
            print(f"Fator climático: {fator}x")

            if fator > 1.3:
                print("⚠️  Clima ESTÁ ACELERANDO o crescimento!")
            elif fator > 1.0:
                print("ℹ️  Clima está levemente acelerando o crescimento")
            else:
                print("✓ Clima está normal")
        print()

        print("✅ Todos os testes concluídos com sucesso!")