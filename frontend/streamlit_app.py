import streamlit as st
import sys
sys.path.append('../backend')

from logic import calc_urgencia
from scheduler import gerador
from database import db
import pandas as pd
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Dashboard Motiva CCR",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Dashboard Inteligente - Motiva CCR")
st.subtitle("Gerenciamento Inteligente de Vegetação em Rodovias")

# Sidebar
st.sidebar.header("📊 Opções")
opcao = st.sidebar.radio(
    "Selecione uma visualização:",
    ["Dashboard Principal", "Cronograma", "Análise Detalhada", "Relatório"]
)

# ============ DASHBOARD PRINCIPAL ============
if opcao == "Dashboard Principal":
    
    st.header("Status dos Trechos")
    
    # Calcular status de todos os trechos
    dados_trechos = []
    for trecho in db.trechos:
        status = calc_urgencia.get_status_trecho(trecho['id'])
        dados_trechos.append({
            'ID': trecho['id'],
            'Trecho': trecho['nome'],
            'Dias sem manutenção': status.dias_desde_manutencao,
            'Crescimento': f"{status.crescimento_estimado}%",
            'Urgência': f"{status.urgencia}%",
            'Risco': status.risco_atual,
            'Cor': status.cor
        })
    
    df = pd.DataFrame(dados_trechos)
    
    # Visualizar como cards coloridos
    cols = st.columns(len(db.trechos))
    
    for idx, trecho in enumerate(db.trechos):
        status = calc_urgencia.get_status_trecho(trecho['id'])
        
        with cols[idx]:
            # Cor baseada na urgência
            if status.cor == "vermelho":
                cor_bg = "🔴"
            elif status.cor == "amarelo":
                cor_bg = "🟡"
            else:
                cor_bg = "🟢"
            
            st.metric(
                label=f"{cor_bg} {trecho['nome'][:20]}",
                value=f"{status.urgencia:.0f}%",
                delta=f"{status.risco_atual}"
            )
    
    st.divider()
    
    # Tabela detalhada
    st.subheader("Detalhes dos Trechos")
    st.dataframe(df, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição de Risco")
        
        risco_counts = {
            'ALTO': len([d for d in dados_trechos if d['Risco'] == 'ALTO']),
            'MÉDIO': len([d for d in dados_trechos if d['Risco'] == 'MÉDIO']),
            'BAIXO': len([d for d in dados_trechos if d['Risco'] == 'BAIXO'])
        }
        
        st.bar_chart(risco_counts)
    
    with col2:
        st.subheader("Urgência Média por Tipo de Vegetação")
        
        # Agrupar por tipo de vegetação
        urgencia_por_tipo = {}
        for trecho in db.trechos:
            status = calc_urgencia.get_status_trecho(trecho['id'])
            tipo = trecho['tipo_vegetacao']
            
            if tipo not in urgencia_por_tipo:
                urgencia_por_tipo[tipo] = []
            
            urgencia_por_tipo[tipo].append(status.urgencia)
        
        # Calcular média
        media_por_tipo = {
            k: sum(v) / len(v) 
            for k, v in urgencia_por_tipo.items()
        }
        
        st.bar_chart(media_por_tipo)

# ============ CRONOGRAMA ============
elif opcao == "Cronograma":
    
    st.header("📅 Cronograma Semanal Automático")
    
    # Gerar cronograma
    cronograma = gerador.gerar_cronograma_semana()
    
    if cronograma:
        # Mostrar relatório
        relatorio = gerador.gerar_relatorio_cronograma(cronograma)
        st.text(relatorio)
        
        # Tabela do cronograma
        st.subheader("Detalhes do Cronograma")
        
        cronograma_df = pd.DataFrame([
            {
                'Data': item.data.strftime('%d/%m/%Y'),
                'Trecho': item.nome_trecho,
                'Equipe': item.equipe_id,
                'Prioridade': item.prioridade,
                'Tempo (h)': item.tempo_estimado_horas,
                'Custo (R$)': item.custo_estimado
            }
            for item in cronograma
        ])
        
        st.dataframe(cronograma_df, use_container_width=True)
        
        # Download do cronograma
        csv = cronograma_df.to_csv(index=False)
        st.download_button(
            label="Baixar Cronograma (CSV)",
            data=csv,
            file_name=f"cronograma_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    
    else:
        st.info("✅ Todos os trechos estão sob controle. Nenhuma intervenção necessária nesta semana.")

# ============ ANÁLISE DETALHADA ============
elif opcao == "Análise Detalhada":
    
    st.header("🔍 Análise Detalhada de Trechos")
    
    # Seletor de trecho
    trechos_nomes = [f"{t['id']} - {t['nome']}" for t in db.trechos]
    trecho_selecionado = st.selectbox("Selecione um trecho:", trechos_nomes)
    
    trecho_id = int(trecho_selecionado.split()[0])
    trecho = db.get_trecho(trecho_id)
    status = calc_urgencia.get_status_trecho(trecho_id)
    
    # Informações do trecho
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tipo de Vegetação", trecho['tipo_vegetacao'].upper())
    with col2:
        st.metric("Risco Base", f"{trecho['risco_base']*100:.0f}%")
    with col3:
        st.metric("Km", f"{trecho['km_inicio']} a {trecho['km_fim']}")
    
    st.divider()
    
    # Métricas de status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Dias sem Manutenção",
            status.dias_desde_manutencao
        )
    with col2:
        st.metric(
            "Crescimento",
            f"{status.crescimento_estimado:.1f}%"
        )
    with col3:
        st.metric(
            "Fator Clima",
            f"{status.fator_clima:.2f}x"
        )
    with col4:
        st.metric(
            "Urgência",
            f"{status.urgencia:.1f}%"
        )
    
    st.divider()
    
    # Última manutenção
    ultima_manutencao = db.get_ultima_manutencao(trecho_id)
    
    if ultima_manutencao:
        st.subheader("Última Manutenção")
        st.info(
            f"📅 Data: {ultima_manutencao['data']}\n\n"
            f"Tipo: {ultima_manutencao['tipo']}\n\n"
            f"Custo: R$ {ultima_manutencao['custo']}"
        )
    else:
        st.warning("❌ Nenhuma manutenção registrada para este trecho")
    
    # Recomendação
    st.subheader("Recomendação")
    
    if status.urgencia >= 70:
        st.error(f"🔴 INTERVIR IMEDIATAMENTE - Urgência {status.urgencia:.0f}%")
    elif status.urgencia >= 40:
        st.warning(f"🟡 AGENDAR INTERVENÇÃO - Urgência {status.urgencia:.0f}% (próximos {status.proxima_intervencao_dias} dias)")
    else:
        st.success(f"🟢 SOB CONTROLE - Urgência {status.urgencia:.0f}% (intervir em {status.proxima_intervencao_dias} dias)")

# ============ RELATÓRIO ============
elif opcao == "Relatório":
    
    st.header("📊 Relatório Analítico")
    
    # Análise de trechos críticos
    st.subheader("Trechos Críticos (Alta Recorrência)")
    
    trechos_criticos = []
    for trecho in db.trechos:
        status = calc_urgencia.get_status_trecho(trecho['id'])
        if status.urgencia > 70:
            trechos_criticos.append({
                'Trecho': trecho['nome'],
                'Urgência': f"{status.urgencia:.1f}%",
                'Dias s/ Manutenção': status.dias_desde_manutencao,
                'Crescimento': f"{status.crescimento_estimado:.1f}%",
                'Recomendação': 'Aumentar frequência de manutenção'
            })
    
    if trechos_criticos:
        st.dataframe(pd.DataFrame(trechos_criticos), use_container_width=True)
    else:
        st.info("✅ Nenhum trecho crítico identificado")
    
    # Previsão para próximas semanas
    st.subheader("Previsão para Próximas 4 Semanas")
    
    previsao_semanas = []
    for semana in range(1, 5):
        data_inicio_semana = datetime.now() + timedelta(weeks=semana-1)
        cronograma_semana = gerador.gerar_cronograma_semana(data_inicio_semana)
        
        previsao_semanas.append({
            'Semana': semana,
            'Trechos a Intervir': len(cronograma_semana),
            'Custo Estimado': sum(item.custo_estimado for item in cronograma_semana)
        })
    
    st.dataframe(pd.DataFrame(previsao_semanas), use_container_width=True)
    
    # Economia estimada
    st.subheader("Análise de Impacto Financeiro")
    
    col1, col2, col3 = st.columns(3)
    
    # Custo sem otimização (cronograma fixo)
    custo_sem_otimizacao = len(db.trechos) * 30 * 150  # 30 dias × custo fixo
    
    # Custo com otimização
    cronograma_otimizado = gerador.gerar_cronograma_semana()
    custo_com_otimizacao = sum(item.custo_estimado for item in cronograma_otimizado) * 4  # 4 semanas
    
    economia = custo_sem_otimizacao - custo_com_otimizacao
    percentual = (economia / custo_sem_otimizacao) * 100
    
    with col1:
        st.metric("Custo Mensal (Sem Otimização)", f"R$ {custo_sem_otimizacao:,.0f}")
    with col2:
        st.metric("Custo Mensal (Com Otimização)", f"R$ {custo_com_otimizacao:,.0f}")
    with col3:
        st.metric("Economia", f"R$ {economia:,.0f} ({percentual:.1f}%)")

# Footer
st.divider()
st.caption("Challenge CCR Motiva - 2024 | Dashboard Inteligente de Vegetação")