import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
import calendar

# Função para obter os últimos 6 meses
def get_last_6_months():
    today = datetime.now()
    months = []
    for i in range(7):
        date = today - timedelta(days=30*i)
        month_name = calendar.month_name[date.month]
        year = date.year
        months.append(f"{month_name} {year}")
    return months

# Obter os últimos 6 meses
months = get_last_6_months()

# Criar um dicionário para armazenar os arquivos carregados
uploaded_files = {}

# Criar espaços de upload para cada mês
st.title("Carregue os arquivos Excel para cada mês")
for month in months:
    uploaded_file = st.file_uploader(f"Arquivo para {month}", type="xlsx", key=month)
    if uploaded_file:
        uploaded_files[month] = uploaded_file

if uploaded_files:
    # Lista para armazenar os dataframes de cada arquivo
    all_data = []

    for month, file in uploaded_files.items():
        # Carregar os dados do arquivo Excel
        data = pd.read_excel(file)
        data['Mês'] = month  # Adicionar uma coluna com o mês
        all_data.append(data)

    # Concatenar todos os dataframes
    data = pd.concat(all_data, ignore_index=True)

    # Dicionário de assessores (códigos para nomes)
    assessores_dict = {
        '74930': 'Renato Parentoni',
        '67717': 'Marcos Moore',
        '20257': 'Eduardo Campos',
        '29187': 'Ronny Mikyo',
        '24264': 'Geison Evangelista',
        '67704': 'Augusto Cesar',
        '29045': 'Paulo Ricardo',
        '73453': 'Pedro Jeha',
        '74036': 'Balby',
        '72295': 'Luiz Santos',
        '31610': 'Lucas Sampaio',
        '74232': 'Paulo Ribeiro',
        '31027': 'Lucas Coutinho',
        '74339': 'Ronaldy Abdon',
        '26553': 'Flavio PiGari',
        '74780': 'Marcio Leça',
        '32763': 'Eduardo Chemale',
        '30313': 'Gabriel Gianini',
        '32348': 'Victor Anfranzio',
        '27277': 'Tuli',
        '33115': 'Eduardo Carvalho',
        '37303': 'Johan',
        '71097': 'Vinicius',
        '29428': 'Fred',
        '31704': 'Ander'
    }

    # Adicionar coluna com nomes dos assessores
    data['Nome Assessor'] = data['Assessor'].astype(str).map(assessores_dict)

    # Substituir valores NaN por 0 para somar corretamente as receitas
    colunas_receita = ['Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários', 'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']
    data[colunas_receita] = data[colunas_receita].fillna(0)

    # Sidebar para selecionar filtros
    st.sidebar.title("Filtros")
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", options=months)

    # Filtrar os dados pelo mês selecionado
    data_mes = data[data['Mês'] == mes_selecionado]

    # Agrupar os dados por assessor e somar as receitas
    receita_por_assessor = data_mes.groupby('Nome Assessor')[colunas_receita].sum().reset_index()

    # Ranking dos assessores por receita no mês
    ranking = receita_por_assessor[['Nome Assessor', 'Receita no Mês']].sort_values(by='Receita no Mês', ascending=False)

    # Selecionar o assessor (movido para a barra lateral)
    assessor_selecionado = st.sidebar.selectbox("Selecione um Assessor", options=ranking['Nome Assessor'])

    st.title(f"Dashboard de Receitas - {mes_selecionado}")

    # Gráfico de barras para o ranking de assessores
    fig_ranking = px.bar(ranking, x='Nome Assessor', y='Receita no Mês', 
                         title=f"Ranking de Assessores - {mes_selecionado}",
                         labels={'Nome Assessor': 'Assessor', 'Receita no Mês': 'Receita (R$)'},
                         text='Receita no Mês')
    fig_ranking.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_ranking.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_ranking)

    # Filtrar os dados para o assessor selecionado
    dados_assessor = data_mes[data_mes['Nome Assessor'] == assessor_selecionado]

    # Filtrar os clientes que geraram mais receita
    clientes_por_receita = dados_assessor.groupby('Cliente')['Receita no Mês'].sum().reset_index()

    # Converter o código do cliente para string
    clientes_por_receita['Cliente'] = clientes_por_receita['Cliente'].astype(str)

    # Ordenar os clientes pela receita no mês
    ranking_clientes = clientes_por_receita.sort_values(by='Receita no Mês', ascending=False)

    # Formatar a coluna de receita em BRL
    ranking_clientes['Receita no Mês'] = ranking_clientes['Receita no Mês'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Exibir ranking dos clientes em ordem decrescente
    st.subheader(f"Ranking de Clientes - {assessor_selecionado} - {mes_selecionado}")
    st.dataframe(ranking_clientes)

    # Gráfico de Radar
    categorias = colunas_receita[:-1]
    valores = dados_assessor[categorias].sum().values
    
    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name=assessor_selecionado
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True)
        ),
        showlegend=True,
        title=f"Gráfico de Radar - Receita por Produto de {assessor_selecionado}"
    )

    st.plotly_chart(fig_radar)

    # Funcionalidade para exportar os dados filtrados
    st.sidebar.title("Exportar Dados")
    export_format = st.sidebar.selectbox("Selecione o Formato", ['Excel', 'CSV'])

    if st.sidebar.button("Exportar"):
        if export_format == 'Excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                receita_por_assessor.to_excel(writer, sheet_name='Sheet1', index=False)
            output.seek(0)
            st.sidebar.download_button(
                label="Download Excel",
                data=output,
                file_name=f'dados_filtrados_{mes_selecionado}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif export_format == 'CSV':
            csv = receita_por_assessor.to_csv(index=False)
            st.sidebar.download_button(
                label="Download CSV",
                data=csv,
                file_name=f'dados_filtrados_{mes_selecionado}.csv',
                mime='text/csv',
            )

    # Definir tema escuro
    st.markdown(
        """
        <style>
        .css-18e3th9 {
            background-color: #0e1117;
            color: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.write("Por favor, carregue pelo menos um arquivo Excel para visualizar os dados.")
