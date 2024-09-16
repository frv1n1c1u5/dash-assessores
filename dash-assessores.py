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
        # ... (dicionário dos assessores) ...
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
    receita_cliente_assessor = data_selecionada.groupby(['Cliente', 'Nome Assessor'])['Receita no Mês'].sum().reset_index()

    # Identificar o assessor com maior receita para cada cliente
    idx = receita_cliente_assessor.groupby('Cliente')['Receita no Mês'].idxmax()
    clientes_assessor_principal = receita_cliente_assessor.loc[idx]

    # Obter pares únicos de assessor e cliente principal
    unique_clients = clientes_assessor_principal[['Nome Assessor', 'Cliente']]

    # Contar o número de clientes únicos por assessor
    clientes_por_assessor = unique_clients.groupby('Nome Assessor').size().reset_index(name='Número de Clientes')

    # Ordenar os assessores com base no ranking de receita
    clientes_por_assessor['Ordem Receita'] = clientes_por_assessor['Nome Assessor'].map(
        ranking.set_index('Nome Assessor')['Receita no Mês'])
    clientes_por_assessor = clientes_por_assessor.sort_values(by='Ordem Receita', ascending=False)

    # Gráfico de barras para o número de clientes por assessor
    fig_clientes = px.bar(clientes_por_assessor, x='Nome Assessor', y='Número de Clientes',
                          title="Número de Clientes Únicos por Assessor",
                          labels={'Nome Assessor': 'Assessor', 'Número de Clientes': 'Número de Clientes'},
                          text='Número de Clientes')
    fig_clientes.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig_clientes.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_clientes)

    # Analisar dados do assessor com problemas
    dados_assessor_problema = unique_clients[unique_clients['Nome Assessor'] == 'Marcos Moore']
    st.write(f"Análise detalhada dos clientes de {assessor_selecionado}:")
    st.dataframe(dados_assessor_problema)

    # Verificar clientes associados a múltiplos assessores
    clientes_assessores = data_selecionada.groupby('Cliente')['Nome Assessor'].nunique().reset_index()
    clientes_multiplos_assessores = clientes_assessores[clientes_assessores['Nome Assessor'] > 1]
    if not clientes_multiplos_assessores.empty:
        st.warning("Existem clientes associados a múltiplos assessores.")
        st.write(clientes_multiplos_assessores)

    # ... (restante do código para gráficos e exportação) ...

# Função principal
def main():
    """
    Função principal que executa o aplicativo Streamlit.
    """
    # Obter os meses de Maio a Outubro de 2023
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
        with st.spinner('Carregando e processando os dados...'):
            data = carregar_dados(uploaded_files)
            if not data.empty:
                data = processar_dados(data)
                verificar_duplicatas_clientes(data)
                gerar_graficos(data, months)
                st.success('Dados carregados e gráficos gerados com sucesso!')
            else:
                st.warning('Nenhum dado foi carregado.')
    else:
        st.info('Por favor, carregue os arquivos Excel para visualizar o dashboard.')

if __name__ == "__main__":
    main()
