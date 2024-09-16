import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
import unidecode

# Definir configurações iniciais da página
st.set_page_config(
    page_title="Dashboard de Receitas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Função para obter os meses de Maio a Outubro de 2023, excluindo Abril
def get_last_6_months():
    """
    Retorna uma lista com os nomes dos meses de Maio a Outubro de 2023, excluindo Abril.
    """
    months = ['May 2023', 'June 2023', 'July 2023', 'August 2023', 'September 2023', 'October 2023']
    return months

# Função para carregar dados dos arquivos Excel
@st.cache_data
def carregar_dados(uploaded_files):
    """
    Carrega e concatena os dados dos arquivos Excel fornecidos.

    Parameters:
    uploaded_files (dict): Dicionário com os meses e arquivos correspondentes.

    Returns:
    pd.DataFrame: DataFrame concatenado com os dados de todos os meses.
    """
    all_data = []
    colunas_necessarias = ['Assessor', 'Cliente', 'Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                           'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']

    for month, file in uploaded_files.items():
        try:
            data = pd.read_excel(file)
            if not set(colunas_necessarias).issubset(data.columns):
                st.error(f"O arquivo para {month} não contém todas as colunas necessárias.")
                continue
            data['Mês'] = month  # Adicionar uma coluna com o mês
            all_data.append(data)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo para {month}: {e}")
            continue

    if all_data:
        data = pd.concat(all_data, ignore_index=True)
        return data
    else:
        return pd.DataFrame()

# Função para processar os dados
def processar_dados(data):
    """
    Processa os dados carregados, incluindo mapeamento de assessores e preenchimento de valores nulos.

    Parameters:
    data (pd.DataFrame): DataFrame com os dados carregados.

    Returns:
    pd.DataFrame: DataFrame processado.
    """
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
    data['Assessor'] = data['Assessor'].astype(str)
    data['Nome Assessor'] = data['Assessor'].map(assessores_dict)
    data['Nome Assessor'] = data['Nome Assessor'].fillna('Assessor Desconhecido')

    # Padronizar os identificadores de clientes
    data['Cliente'] = data['Cliente'].astype(str)
    data['Cliente'] = data['Cliente'].str.strip()
    data['Cliente'] = data['Cliente'].str.upper()
    data['Cliente'] = data['Cliente'].apply(unidecode.unidecode)
    data['Cliente'] = data['Cliente'].str.replace('[^A-Za-z0-9]', '', regex=True)

    # Remover valores nulos ou vazios em 'Cliente'
    data = data[data['Cliente'] != '']

    # Remover linhas duplicadas
    data = data.drop_duplicates()

    # Substituir valores NaN por 0 para somar corretamente as receitas
    colunas_receita = ['Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                       'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']
    data[colunas_receita] = data[colunas_receita].fillna(0)

    return data

# Função para verificar duplicatas nos clientes
def verificar_duplicatas_clientes(data):
    clientes_contagem = data['Cliente'].value_counts()
    clientes_duplicados = clientes_contagem[clientes_contagem > 1]
    if not clientes_duplicados.empty:
        st.write("Clientes com possíveis duplicações nos identificadores:")
        st.write(clientes_duplicados)
    else:
        st.write("Não foram encontradas duplicações nos identificadores de clientes.")

# Função para gerar gráficos
def gerar_graficos(data, months):
    """
    Gera os gráficos e elementos da interface do usuário.

    Parameters:
    data (pd.DataFrame): DataFrame com os dados processados.
    months (list): Lista de meses disponíveis.
    """
    # Sidebar para selecionar filtros
    st.sidebar.title("Filtros")
    meses_selecionados = st.sidebar.multiselect("Selecione o(s) Mês(es)", options=months, default=months)

    # Filtrar os dados pelos meses selecionados
    data_selecionada = data[data['Mês'].isin(meses_selecionados)]

    # Verificar se há dados para os meses selecionados
    if data_selecionada.empty:
        st.warning(f"Não há dados disponíveis para os meses selecionados.")
        return

    # Agrupar os dados por assessor e somar as receitas
    colunas_receita = ['Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                       'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']
    receita_por_assessor = data_selecionada.groupby('Nome Assessor')[colunas_receita].sum().reset_index()

    # Ranking dos assessores por receita
    ranking = receita_por_assessor[['Nome Assessor', 'Receita no Mês']].sort_values(by='Receita no Mês', ascending=False)

    # Selecionar o assessor
    assessor_selecionado = st.sidebar.selectbox("Selecione um Assessor", options=ranking['Nome Assessor'])

    st.title(f"Dashboard de Receitas - Meses Selecionados")

    # Gráfico de barras para o ranking de assessores
    fig_ranking = px.bar(ranking, x='Nome Assessor', y='Receita no Mês',
                         title=f"Ranking de Assessores",
                         labels={'Nome Assessor': 'Assessor', 'Receita no Mês': 'Receita (R$)'},
                         text='Receita no Mês')
    fig_ranking.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_ranking.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_ranking)

    # Contar clientes únicos por assessor considerando o assessor com maior receita para cada cliente
    # Calcular a receita total por cliente e assessor
    receita_cliente_assessor = data_selecionada
