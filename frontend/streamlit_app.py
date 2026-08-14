import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import json

backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from logic import calc_urgencia
from scheduler import gerador
from database import db

st.set_page_config(
    page_title="Dashboard Motiva CCR",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    :root {
        --color-verde: #10B981;
        --color-amarelo: #F59E0B;
        --color-vermelho: #EF4444;
    }

    h1 {
        color: #1F2937;
        text-align: center;
        margin-bottom: 10px;
    }

    .subtitle {
        text-align: center;
        color: #6B7280;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1>🚗 Dashboard Inteligente - Motiva CCR</h1>
    <p style="font-size: 18px; color: #6B7280;">
        Gerenciamento Inteligente de Vegetação em Rodovias
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.title("📊 Navegação")

opcao_principal = st.sidebar.radio(
    "Escolha uma visualização:",
    [
        "🏠 Dashboard Principal",
        "📅 Cronograma Semanal",
        "🔍 Análise Detalhada",
        "💰 Relatório Financeiro",
        "⚙️ Configurações"
    ],
    key="main_nav"
)

st.sidebar.markdown("---")

with st.sidebar.expander("ℹ️ Informações do Sistema"):
    st.write(f"**Data Atual:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.write(f"**Total de Trechos:** {len(db.get_todos_trechos())}")

    todos_status = calc_urgencia.get_status_todos_trechos()
    verdes = len([s for s in todos_status if s.cor == "verde"])
    amarelos = len([s for s in todos_status if s.cor == "amarelo"])
    vermelhos = len([s for s in todos_status if s.cor == "vermelho"])

    st.write("**Status Geral:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🟢 Verde", verdes)

    with col2:
        st.metric("🟡 Amarelo", amarelos)

    with col3:
        st.metric("🔴 Vermelho", vermelhos)


if opcao_principal == "🏠 Dashboard Principal":

    st.markdown("## 📍 Status dos Trechos")
    st.markdown("*Clique em um card para ver mais detalhes*")
    st.markdown("---")

    dados_trechos = []
    todos_trechos = db.get_todos_trechos()

    for trecho in todos_trechos:
        status = calc_urgencia.get_status_trecho(trecho['id'])
        dados_trechos.append({
            'id': trecho['id'],
            'nome': trecho['nome'],
            'tipo': trecho['tipo_vegetacao'],
            'status': status
        })

    cols = st.columns(4)

    for idx, dados in enumerate(dados_trechos):
        col = cols[idx % 4]

        with col:
            trecho = dados['status']

            if trecho.cor == "vermelho":
                cor_hex = "#EF4444"
                emoji = "🔴"
            elif trecho.cor == "amarelo":
                cor_hex = "#F59E0B"
                emoji = "🟡"
            else:
                cor_hex = "#10B981"
                emoji = "🟢"

            st.markdown(f"""
            <div style="
                border: 2px solid {cor_hex};
                border-radius: 10px;
                padding: 15px;
                background-color: {cor_hex}15;
                margin-bottom: 10px;
                text-align: center;
            ">
                <h3 style="margin: 0; color: {cor_hex};">{emoji} Trecho {dados['id']}</h3>
                <p style="margin: 5px 0; font-size: 12px; color: #6B7280;">
                    {dados['nome'][:25]}
                </p>
                <h2 style="margin: 10px 0; color: {cor_hex};">
                    {trecho.urgencia:.0f}%
                </h2>
                <p style="margin: 5px 0; font-size: 11px; color: #6B7280;">
                    {trecho.risco_atual}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("## 📋 Tabela Detalhada")

    df_trechos = pd.DataFrame([
        {
            'ID': dados['id'],
            'Trecho': dados['nome'],
            'Vegetação': dados['tipo'],
            'Dias s/ Manutenção': dados['status'].dias_desde_manutencao,
            'Crescimento': f"{dados['status'].crescimento_estimado:.1f}%",
            'Urgência': f"{dados['status'].urgencia:.1f}%",
            'Risco': dados['status'].risco_atual,
            'Próx. Intervenção': f"{dados['status'].proxima_intervencao_dias}d"
        }
        for dados in dados_trechos
    ])

    st.dataframe(
        df_trechos,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎨 Distribuição de Risco")

        risco_counts = {
            'ALTO': len([d for d in dados_trechos if d['status'].risco_atual == 'ALTO']),
            'MÉDIO': len([d for d in dados_trechos if d['status'].risco_atual == 'MÉDIO']),
            'BAIXO': len([d for d in dados_trechos if d['status'].risco_atual == 'BAIXO'])
        }

        st.bar_chart(risco_counts)

    with col2:
        st.markdown("### 📈 Urgência Média por Tipo de Vegetação")

        urgencia_por_tipo = {}

        for dados in dados_trechos:
            tipo = dados['tipo']

            if tipo not in urgencia_por_tipo:
                urgencia_por_tipo[tipo] = []

            urgencia_por_tipo[tipo].append(dados['status'].urgencia)

        media_por_tipo = {
            k: sum(v) / len(v)
            for k, v in urgencia_por_tipo.items()
        }

        st.bar_chart(media_por_tipo)

    st.markdown("---")

    st.markdown("## 📊 Indicadores Principais")

    col1, col2, col3, col4 = st.columns(4)

    urgencia_media = sum(
        [d['status'].urgencia for d in dados_trechos]
    ) / len(dados_trechos)

    trechos_criticos = len([
        d for d in dados_trechos
        if d['status'].urgencia >= 70
    ])

    with col1:
        st.metric(
            "📊 Urgência Média",
            f"{urgencia_media:.1f}%",
            delta=None
        )

    with col2:
        st.metric(
            "🔴 Trechos Críticos",
            trechos_criticos,
            delta=None
        )

    with col3:
        dias_media = sum(
            [d['status'].dias_desde_manutencao for d in dados_trechos]
        ) / len(dados_trechos)

        st.metric(
            "📅 Dias Médios s/ Manutenção",
            f"{dias_media:.0f}d",
            delta=None
        )

    with col4:
        crescimento_medio = sum(
            [d['status'].crescimento_estimado for d in dados_trechos]
        ) / len(dados_trechos)

        st.metric(
            "📈 Crescimento Médio",
            f"{crescimento_medio:.1f}%",
            delta=None
        )


elif opcao_principal == "📅 Cronograma Semanal":

    st.markdown("## 📅 Cronograma Automático da Semana")

    col1, col2, col3 = st.columns(3)

    with col1:
        num_equipes = st.slider(
            "Número de equipes disponíveis:",
            min_value=1,
            max_value=10,
            value=3
        )

    with col2:
        horas_por_dia = st.slider(
            "Horas de trabalho por dia:",
            min_value=4.0,
            max_value=12.0,
            value=8.0,
            step=0.5
        )

    with col3:
        data_inicio = st.date_input(
            "Data de início:",
            value=datetime.now().date()
        )

    st.markdown("---")

    gerador_temp = gerador.__class__(
        num_equipes=num_equipes,
        horas_por_dia=horas_por_dia
    )

    data_inicio_dt = datetime.combine(
        data_inicio,
        datetime.min.time()
    )

    cronograma = gerador_temp.gerar_cronograma_semana(
        data_inicio_dt
    )

    if cronograma:

        st.markdown("### 📋 Relatório do Cronograma")

        relatorio = gerador_temp.gerar_relatorio_cronograma(
            cronograma
        )

        st.text(relatorio)

        st.markdown("---")

        st.markdown("### 📊 Tabela Detalhada")

        cronograma_lista = gerador_temp.get_cronograma_como_lista(
            cronograma
        )

        df_cronograma = pd.DataFrame(cronograma_lista)

        st.dataframe(
            df_cronograma,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        st.markdown("### 📥 Exportar Dados")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv = df_cronograma.to_csv(
                index=False,
                encoding='utf-8-sig'
            )

            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"cronograma_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col2:
            json_data = json.dumps(
                cronograma_lista,
                indent=2,
                ensure_ascii=False,
                default=str
            )

            st.download_button(
                label="📥 Baixar JSON",
                data=json_data,
                file_name=f"cronograma_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

        with col3:
            st.info(
                "💡 Use o botão acima para exportar os dados em CSV ou JSON"
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📅 Trechos por Dia")

            trechos_por_dia = {}

            for item in cronograma:
                dia = item.data.strftime('%d/%m')
                trechos_por_dia[dia] = (
                    trechos_por_dia.get(dia, 0) + 1
                )

            st.bar_chart(trechos_por_dia)

        with col2:
            st.markdown("### 💰 Custo por Dia")

            custo_por_dia = {}

            for item in cronograma:
                dia = item.data.strftime('%d/%m')
                custo_por_dia[dia] = (
                    custo_por_dia.get(dia, 0)
                    + item.custo_estimado
                )

            st.bar_chart(custo_por_dia)

    else:
        st.info("✅ Nenhuma intervenção necessária nesta semana!")


elif opcao_principal == "🔍 Análise Detalhada":

    st.markdown("## 🔍 Análise Detalhada de Trechos")

    trechos_nomes = [
        f"{t['id']} - {t['nome']}"
        for t in db.get_todos_trechos()
    ]

    trecho_selecionado = st.selectbox(
        "Selecione um trecho:",
        trechos_nomes
    )

    trecho_id = int(trecho_selecionado.split()[0])

    trecho = db.get_trecho(trecho_id)
    status = calc_urgencia.get_status_trecho(trecho_id)

    st.markdown("---")

    st.markdown("### 📍 Informações do Trecho")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Localização",
            f"km {trecho['km_inicio']}-{trecho['km_fim']}"
        )

    with col2:
        st.metric(
            "Tipo de Vegetação",
            trecho['tipo_vegetacao'].upper()
        )

    with col3:
        st.metric(
            "Risco Base",
            f"{trecho['risco_base']*100:.0f}%"
        )

    with col4:
        st.metric(
            "Comprimento",
            f"{trecho['km_fim'] - trecho['km_inicio']:.0f} km"
        )

    st.markdown("---")

    st.markdown("### 📊 Métricas de Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Dias sem Manutenção",
            status.dias_desde_manutencao,
            delta=None
        )

    with col2:
        st.metric(
            "Crescimento Estimado",
            f"{status.crescimento_estimado:.1f}%",
            delta=None
        )

    with col3:
        st.metric(
            "Fator Climático",
            f"{status.fator_clima:.2f}x",
            delta=None
        )

    with col4:
        st.metric(
            "Urgência",
            f"{status.urgencia:.1f}%",
            delta=None
        )

    st.markdown("---")

    st.markdown("### 🎨 Status Visual")

    col1, col2, col3 = st.columns(3)

    with col1:
        if status.cor == "vermelho":
            st.error(
                f"🔴 CRÍTICO - Urgência {status.urgencia:.0f}%"
            )
        elif status.cor == "amarelo":
            st.warning(
                f"🟡 ATENÇÃO - Urgência {status.urgencia:.0f}%"
            )
        else:
            st.success(
                f"🟢 OK - Urgência {status.urgencia:.0f}%"
            )

    with col2:
        if status.risco_atual == "ALTO":
            st.error("🔴 Risco: ALTO")
        elif status.risco_atual == "MÉDIO":
            st.warning("🟡 Risco: MÉDIO")
        else:
            st.success("🟢 Risco: BAIXO")

    with col3:
        st.info(
            f"⏰ Próxima intervenção em "
            f"{status.proxima_intervencao_dias} dias"
        )

    st.markdown("---")

    st.markdown("### 🔧 Histórico de Manutenção")

    manutencoes = db.get_manutencoes_trecho(trecho_id)

    if manutencoes:

        df_manutencoes = pd.DataFrame([
            {
                'Data': m['data'],
                'Tipo': m['tipo'],
                'Duração (dias)': m['dias_duracao'],
                'Custo (R$)': f"R$ {m['custo']:.2f}"
            }
            for m in sorted(
                manutencoes,
                key=lambda x: x['data'],
                reverse=True
            )
        ])

        st.dataframe(
            df_manutencoes,
            use_container_width=True,
            hide_index=True
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total de Manutenções",
                len(manutencoes)
            )

        with col2:
            custo_total = sum(
                m['custo'] for m in manutencoes
            )

            st.metric(
                "Custo Total",
                f"R$ {custo_total:.2f}"
            )

        with col3:
            dias_manutidos = sum(
                m['dias_duracao'] for m in manutencoes
            )

            st.metric(
                "Dias de Trabalho",
                dias_manutidos
            )

    else:
        st.warning(
            "❌ Nenhuma manutenção registrada para este trecho"
        )

    st.markdown("---")

    st.markdown("### 🌤️ Impacto Climático Atual")

    clima = db.get_clima_atual()

    if clima:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Temperatura",
                f"{clima['temperatura_media']}°C"
            )

        with col2:
            st.metric(
                "Chuva",
                f"{clima['chuva_mm']}mm"
            )

        with col3:
            st.metric(
                "Umidade",
                f"{clima['umidade']}%"
            )

        fator = calc_urgencia.calcular_fator_clima(trecho_id)

        if fator > 1.3:
            st.error(
                f"⚠️ Clima ESTÁ ACELERANDO o crescimento ({fator:.2f}x)"
            )
        elif fator > 1.0:
            st.warning(
                f"ℹ️ Clima está levemente acelerando "
                f"o crescimento ({fator:.2f}x)"
            )
        else:
            st.success(
                f"✓ Clima está normal ({fator:.2f}x)"
            )

    st.markdown("---")

    st.markdown("### 💡 Recomendação")

    if status.urgencia >= 70:

        st.error(f"""
        🔴 **INTERVIR IMEDIATAMENTE**

        Este trecho atingiu nível crítico de urgência ({status.urgencia:.0f}%).
        A vegetação precisa ser controlada HOJE.
        """)

    elif status.urgencia >= 40:

        st.warning(f"""
        🟡 **AGENDAR INTERVENÇÃO**

        Este trecho requer atenção. Recomenda-se intervir
        nos próximos {status.proxima_intervencao_dias} dias.

        Urgência atual: {status.urgencia:.0f}%
        """)

    else:

        st.success(f"""
        🟢 **SOB CONTROLE**

        Este trecho está sob controle. Próxima intervenção
        recomendada em {status.proxima_intervencao_dias} dias.

        Urgência atual: {status.urgencia:.0f}%
        """)


elif opcao_principal == "💰 Relatório Financeiro":

    st.markdown("## 💰 Análise de Impacto Financeiro")

    cronograma = gerador.gerar_cronograma_semana()
    analise = gerador.gerar_analise_impacto(cronograma)

    st.markdown("---")

    st.markdown("### 📊 Comparação de Custos")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Custo Mensal (Inteligente)",
            f"R$ {analise['custo_otimizado_mes']:,.2f}",
            delta=None
        )

    with col2:
        st.metric(
            "Custo Mensal (Fixo/Atual)",
            f"R$ {analise['custo_fixo_mes']:,.2f}",
            delta=None
        )

    with col3:
        st.metric(
            "💰 ECONOMIA MENSAL",
            f"R$ {abs(analise['economia_mes']):,.2f}",
            delta=f"{analise['percentual_economia']:.1f}%"
        )

    st.markdown("---")

    st.markdown("### 📈 Análise Semanal")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Cronograma Inteligente (Otimizado)**")
        st.write(
            f"Custo Semanal: "
            f"R$ {analise['custo_otimizado_semana']:.2f}"
        )
        st.write(
            f"Custo Mensal: "
            f"R$ {analise['custo_otimizado_mes']:.2f}"
        )
        st.write(f"Trechos atendidos: {len(cronograma)}")

    with col2:
        st.markdown("**Cronograma Fixo (Situação Atual)**")
        st.write(
            f"Custo Semanal: "
            f"R$ {analise['custo_fixo_semana']:.2f}"
        )
        st.write(
            f"Custo Mensal: "
            f"R$ {analise['custo_fixo_mes']:.2f}"
        )
        st.write(
            f"Todos os {len(db.get_todos_trechos())} trechos sempre"
        )

    st.markdown("---")

    st.markdown("### 📊 Gráfico Comparativo")

    comparacao_data = {
        'Inteligente': analise['custo_otimizado_mes'],
        'Fixo': analise['custo_fixo_mes']
    }

    st.bar_chart(comparacao_data)

    st.markdown("---")

    st.markdown("### 💼 Detalhes Financeiros")

    col1, col2, col3 = st.columns(3)

    with col1:
        economia_anual = analise['economia_mes'] * 12

        st.metric(
            "Economia Anual",
            f"R$ {economia_anual:,.2f}",
            delta=None
        )

    with col2:
        if len(cronograma) > 0:

            custo_por_trecho = (
                analise['custo_otimizado_mes']
                / len(cronograma)
            )

            st.metric(
                "Custo Médio por Trecho",
                f"R$ {custo_por_trecho:,.2f}",
                delta=None
            )

    with col3:
        horas_totais = sum(
            c.tempo_estimado_horas for c in cronograma
        ) * 4

        if horas_totais > 0:

            custo_por_hora = (
                analise['custo_otimizado_mes']
                / horas_totais
            )

            st.metric(
                "Custo por Hora",
                f"R$ {custo_por_hora:,.2f}",
                delta=None
            )

    st.markdown("---")

    st.markdown("### 🎯 Análise de ROI")

    if analise['economia_mes'] > 0:

        st.success(f"""
        ✅ **ECONOMIA POSITIVA**

        Com o sistema inteligente, você economiza:

        • **Mensal:** R$ {analise['economia_mes']:,.2f}
        • **Anual:** R$ {analise['economia_mes']*12:,.2f}
        • **Percentual:** {analise['percentual_economia']:.1f}%

        Além disso, o sistema oferece:
        - ✓ Melhor segurança nas rodovias
        - ✓ Redução de emergências
        - ✓ Maior eficiência operacional
        - ✓ Planejamento melhor das equipes
        """)

    else:

        st.warning(f"""
        ⚠️ **NOTA IMPORTANTE**

        O sistema otimizado custa mais esta semana porque:
        - Há muitos trechos críticos que precisam intervenção
        - Melhor gastar agora para evitar problemas futuros

        A economia aumentará conforme os trechos forem mantidos.
        """)

    st.markdown("---")

    st.markdown("### 📋 Recomendações")

    st.info("""
    **Para maximizar economia:**

    1. **Manutenção Preventiva**: Intervir nos trechos ANTES do pico crítico
    2. **Monitoramento Contínuo**: Acompanhar urgência regularmente
    3. **Planejamento**: Usar o cronograma para alocar equipes eficientemente
    4. **Equipes Multitarefa**: Ter equipes bem treinadas reduz tempo de intervenção

    **Próximas Ações:**
    - Revisar dados de trechos críticos
    - Gerar cronograma para próxima semana
    - Comunicar cronograma às equipes
    - Monitorar cumprimento
    """)


elif opcao_principal == "⚙️ Configurações":

    st.markdown("## ⚙️ Configurações do Sistema")

    st.markdown("---")

    st.markdown("### 🔧 Parâmetros de Cálculo")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"""
        **Parâmetros Atuais:**

        - **Ciclo Ideal:** {calc_urgencia.CICLO_IDEAL_DIAS} dias
        - **Taxa Agressiva:** {calc_urgencia.TAXA_CRESCIMENTO['agressiva']}% por dia
        - **Taxa Moderada:** {calc_urgencia.TAXA_CRESCIMENTO['moderada']}% por dia
        - **Taxa Baixa:** {calc_urgencia.TAXA_CRESCIMENTO['baixa']}% por dia
        """)

    with col2:
        st.warning(f"""
        **Limites de Urgência:**

        - 🟢 **Verde (OK):** 0 - {calc_urgencia.LIMITE_AMARELO}%
        - 🟡 **Amarelo (Atenção):** {calc_urgencia.LIMITE_AMARELO} - {calc_urgencia.LIMITE_VERMELHO}%
        - 🔴 **Vermelho (Urgente):** {calc_urgencia.LIMITE_VERMELHO} - 100%
        """)

    st.markdown("---")

    st.markdown("### 📊 Dados Carregados")

    col1, col2, col3 = st.columns(3)

    with col1:
        trechos = db.get_todos_trechos()
        st.metric("Trechos", len(trechos))

    with col2:
        st.metric("Manutenções", len(db.manutencoes))

    with col3:
        st.metric("Dados Climáticos", len(db.clima))

    st.markdown("---")

    st.markdown("### 🌿 Distribuição de Trechos por Tipo")

    tipos_count = {}

    for trecho in trechos:
        tipo = trecho['tipo_vegetacao']
        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1

    df_tipos = pd.DataFrame([
        {'Tipo': tipo, 'Quantidade': qty}
        for tipo, qty in tipos_count.items()
    ])

    st.dataframe(
        df_tipos,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    st.markdown("### 📥 Exportar Base de Dados")

    col1, col2, col3 = st.columns(3)

    with col1:
        trechos_json = json.dumps(
            db.get_todos_trechos(),
            indent=2,
            ensure_ascii=False
        )

        st.download_button(
            label="📥 Exportar Trechos",
            data=trechos_json,
            file_name="trechos.json",
            mime="application/json"
        )

    with col2:
        manutencoes_json = json.dumps(
            db.manutencoes,
            indent=2,
            ensure_ascii=False
        )

        st.download_button(
            label="📥 Exportar Manutenções",
            data=manutencoes_json,
            file_name="manutencoes.json",
            mime="application/json"
        )

    with col3:
        clima_json = json.dumps(
            db.clima,
            indent=2,
            ensure_ascii=False
        )

        st.download_button(
            label="📥 Exportar Clima",
            data=clima_json,
            file_name="clima.json",
            mime="application/json"
        )

    st.markdown("---")

    st.markdown("### ℹ️ Informações do Sistema")

    st.write(
        f"**Data/Hora Atual:** "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    st.write("**Versão:** 1.0.0")
    st.write("**Status:** ✅ Funcionando normalmente")
    st.write(
        f"**Última Atualização:** "
        f"{db.get_clima_atual()['data']}"
    )

    st.markdown("---")

    st.markdown("### 📚 Sobre o Projeto")

    st.markdown("""
    **Dashboard Inteligente - Motiva CCR**

    Sistema de gerenciamento automático de vegetação em rodovias.

    **Desenvolvido com:**
    - Python 3.9+
    - Streamlit (Frontend)
    - Pandas (Análise de dados)

    **Tecnologias Implementadas:**
    - ✓ Lógica de cálculo de urgência (Machine Learning-ready)
    - ✓ Gerador automático de cronogramas
    - ✓ Análise de impacto financeiro
    - ✓ Dashboard visual em tempo real
    - ✓ Exportação de dados

    **Contato/Suporte:**
    - Equipe Motiva CCR
    - 2024/2026
    """)


st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🚗 **Motiva CCR** - Desafio de Inovação")

with col2:
    st.caption(
        f"📊 Última atualização: "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

with col3:
    st.caption("✨ Dashboard v1.0 - 2026")