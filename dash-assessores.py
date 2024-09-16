import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta

# Definir configurações iniciais da página
st.set_page_config(
    page_title="Dashboard de Receitas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Função para obter os últimos 6 meses, incluindo Outubro e excluindo Abril
def get_last_6_months():
    """
    Retorna uma lista com os nomes dos últimos 6 meses no formato 'Mês Ano',
    incluindo Outubro e excluindo Abril.
    """
    today = datetime.now()
    # Ajustar a data para incluir Outubro
    months = []
    count = 0
    i = -1  # Começar em -1 para incluir o próximo mês (Outubro)
    while count < 6:
        date = today + relativedelta(months=i)
        month_name = calendar.month_name[date.month]
        year = date.year
        if month_name != 'April':
            months.append(f"{month_name} {year}")
            count += 1
        i -= 1
    return months[::-1]  # Inverter a lista para ordem cronológica

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
    data['Cliente'] = data['Cliente'].astype(str).str.strip().str.upper()

    # Remover valores nulos ou vazios em 'Cliente'
    data = data[data['Cliente'] != '']

    # Substituir valores NaN por 0 para somar corretamente as receitas
    colunas_receita = ['Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                       'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']
    data[colunas_receita] = data[colunas_receita].fillna(0)

    return data

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
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", options=months)

    # Filtrar os dados pelo mês selecionado
    data_mes = data[data['Mês'] == mes_selecionado]

    # Verificar se há dados para o mês selecionado
    if data_mes.empty:
        st.warning(f"Não há dados disponíveis para {mes_selecionado}.")
        return

    # Agrupar os dados por assessor e somar as receitas
    colunas_receita = ['Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                       'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']
    receita_por_assessor = data_mes.groupby('Nome Assessor')[colunas_receita].sum().reset_index()

    # Ranking dos assessores por receita no mês
    ranking = receita_por_assessor[['Nome Assessor', 'Receita no Mês']].sort_values(by='Receita no Mês', ascending=False)

    # Selecionar o assessor
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

    # Remover duplicatas de clientes por assessor dentro do mês selecionado
    unique_clients = data_mes[['Nome Assessor', 'Cliente']].drop_duplicates()

    # Contar o número de clientes únicos por assessor
    clientes_por_assessor = unique_clients.groupby('Nome Assessor').size().reset_index(name='Número de Clientes')

    # Ordenar os assessores com base no ranking de receita
    clientes_por_assessor['Ordem Receita'] = clientes_por_assessor['Nome Assessor'].map(
        ranking.set_index('Nome Assessor')['Receita no Mês'])
    clientes_por_assessor = clientes_por_assessor.sort_values(by='Ordem Receita', ascending=False)

    # Gráfico de barras para o número de clientes por assessor
    fig_clientes = px.bar(clientes_por_assessor, x='Nome Assessor', y='Número de Clientes',
                          title="Número de Clientes por Assessor",
                          labels={'Nome Assessor': 'Assessor', 'Número de Clientes': 'Número de Clientes'},
                          text='Número de Clientes')
    fig_clientes.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig_clientes.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_clientes)

    # Filtrar os dados para o assessor selecionado
    dados_assessor = data_mes[data_mes['Nome Assessor'] == assessor_selecionado]

    # Verificar se há dados para o assessor selecionado
    if dados_assessor.empty:
        st.warning(f"O assessor {assessor_selecionado} não possui dados para {mes_selecionado}.")
        return

    # Filtrar os clientes que geraram mais receita
    clientes_por_receita = dados_assessor.groupby('Cliente')['Receita no Mês'].sum().reset_index()

    # Converter o código do cliente para string
    clientes_por_receita['Cliente'] = clientes_por_receita['Cliente'].astype(str)

    # Ordenar os clientes pela receita no mês
    ranking_clientes = clientes_por_receita.sort_values(by='Receita no Mês', ascending=False)

    # Formatar a coluna de receita em BRL
    ranking_clientes['Receita no Mês'] = ranking_clientes['Receita no Mês'].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Exibir ranking dos clientes
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
                receita_por_assessor.to_excel(writer, sheet_name='Receita por Assessor', index=False)
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

# Função principal
def main():
    """
    Função principal que executa o aplicativo Streamlit.
    """
    # Obter os últimos 6 meses incluindo Outubro e excluindo Abril
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
                gerar_graficos(data, months)
                st.success('Dados carregados e gráficos gerados com sucesso!')
            else:
                st.warning('Nenhum dado foi carregado.')
    else:
        st.info('Por favor, carregue os arquivos Excel para visualizar o dashboard.')

if __name__ == "__main__":
    main()
