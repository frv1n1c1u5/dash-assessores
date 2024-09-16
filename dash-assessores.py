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
@st.cache
def carregar_dados(uploaded_files):
    """
    Carrega e concatena os dados dos arquivos Excel fornecidos.

    Parameters:
    uploaded_files (dict): Dicionário com os meses e arquivos correspondentes.

    Returns:
    pd.DataFrame: DataFrame concatenado com os dados de todos os meses.
    """
    all_data = []
    colunas_necessarias = ['Assessor', 'Cliente', 'Sexo', 'Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                           'Receita RF Privados', 'Receita RF Públicos', 'Nascimento', 'Receita no Mês']

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

    # Processar coluna 'Sexo'
    data['Sexo'] = data['Sexo'].str.strip().str.capitalize()
    data['Sexo'] = data['Sexo'].replace({'M': 'Masculino', 'F': 'Feminino'})

    # Processar coluna 'Nascimento' para calcular a idade
    data['Nascimento'] = pd.to_datetime(data['Nascimento'], errors='coerce')
    today = pd.to_datetime('today')
    data['Idade'] = data['Nascimento'].apply(lambda x: today.year - x.year - ((today.month, today.day) < (x.month, x.day)) if pd.notnull(x) else None)

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
    meses_selecionados = st.sidebar.multiselect("Selecione o(s) Mês(es) para Receitas", options=months, default=months)
    assessor_selecionado = st.sidebar.selectbox("Selecione um Assessor", options=sorted(data['Nome Assessor'].unique()))

    # Filtrar os dados pelos meses selecionados para receitas
    data_selecionada = data[data['Mês'].isin(meses_selecionados)]

    # Filtrar dados pelo assessor selecionado
    data_assessor = data[data['Nome Assessor'] == assessor_selecionado]

    # Verificar se há dados para o assessor selecionado
    if data_assessor.empty:
        st.warning(f"O assessor {assessor_selecionado} não possui dados.")
        return

    st.title(f"Dashboard de Receitas e Perfil de Clientes - {assessor_selecionado}")

    # Gráficos de Receitas (mesmo que antes)
    # Agrupar os dados por assessor e somar as receitas
    colunas_receita = ['Receita Bovespa', 'Receita Futuros', 'Receita RF Bancários',
                       'Receita RF Privados', 'Receita RF Públicos', 'Receita no Mês']
    receita_por_assessor = data_selecionada.groupby('Nome Assessor')[colunas_receita].sum().reset_index()

    # Ranking dos assessores por receita
    ranking = receita_por_assessor[['Nome Assessor', 'Receita no Mês']].sort_values(by='Receita no Mês', ascending=False)

    # Gráfico de barras para o ranking de assessores
    fig_ranking = px.bar(ranking, x='Nome Assessor', y='Receita no Mês',
                         title=f"Ranking de Assessores",
                         labels={'Nome Assessor': 'Assessor', 'Receita no Mês': 'Receita (R$)'},
                         text='Receita no Mês')
    fig_ranking.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_ranking.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_ranking)

    # Gráfico de Radar de Receitas por Produto para o Assessor Selecionado
    dados_assessor_receita = data_selecionada[data_selecionada['Nome Assessor'] == assessor_selecionado]
    valores = dados_assessor_receita[colunas_receita[:-1]].sum().values

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=valores,
        theta=colunas_receita[:-1],
        fill='toself',
        name=assessor_selecionado
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True)
        ),
        showlegend=True,
        title=f"Receita por Produto de {assessor_selecionado}"
    )

    st.plotly_chart(fig_radar)

    # Análise de Gênero
    genero_counts = data_assessor[['Cliente', 'Sexo']].drop_duplicates()['Sexo'].value_counts().reset_index()
    genero_counts.columns = ['Sexo', 'Contagem']

    fig_genero = px.pie(genero_counts, values='Contagem', names='Sexo',
                        title='Distribuição por Gênero')
    st.plotly_chart(fig_genero)

    # Análise de Idade
    idade_bins = [0, 18, 25, 35, 45, 55, 65, 100]
    labels = ['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    data_assessor['Faixa Etária'] = pd.cut(data_assessor['Idade'], bins=idade_bins, labels=labels, right=False)

    faixa_etaria_counts = data_assessor[['Cliente', 'Faixa Etária']].drop_duplicates()['Faixa Etária'].value_counts().sort_index().reset_index()
    faixa_etaria_counts.columns = ['Faixa Etária', 'Contagem']

    fig_idade = px.bar(faixa_etaria_counts, x='Faixa Etária', y='Contagem',
                       title='Distribuição por Faixa Etária',
                       labels={'Faixa Etária': 'Faixa Etária', 'Contagem': 'Número de Clientes'},
                       text='Contagem')
    fig_idade.update_traces(textposition='outside')
    st.plotly_chart(fig_idade)

    # Exibir tabela de clientes com gênero e idade
    st.subheader(f"Clientes de {assessor_selecionado}")
    clientes_info = data_assessor[['Cliente', 'Sexo', 'Idade']].drop_duplicates()
    st.dataframe(clientes_info)

    # Funcionalidade para exportar os dados filtrados
    st.sidebar.title("Exportar Dados")
    export_format = st.sidebar.selectbox("Selecione o Formato", ['Excel', 'CSV'])

    if st.sidebar.button("Exportar"):
        if export_format == 'Excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                clientes_info.to_excel(writer, sheet_name='Clientes', index=False)
            output.seek(0)
            st.sidebar.download_button(
                label="Download Excel",
                data=output,
                file_name=f'clientes_{assessor_selecionado}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif export_format == 'CSV':
            csv = clientes_info.to_csv(index=False)
            st.sidebar.download_button(
                label="Download CSV",
                data=csv,
                file_name=f'clientes_{assessor_selecionado}.csv',
                mime='text/csv',
            )

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
                gerar_graficos(data, months)
                st.success('Dados carregados e gráficos gerados com sucesso!')
            else:
                st.warning('Nenhum dado foi carregado.')
    else:
        st.info('Por favor, carregue os arquivos Excel para visualizar o dashboard.')

if __name__ == "__main__":
    main()
