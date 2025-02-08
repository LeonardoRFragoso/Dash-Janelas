import streamlit as st
import pandas as pd

# Configuração da página para abrir em modo wide
st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

# Carregar os dados
@st.cache_data
def load_data():
    file_path = "informacoes_janelas2.xlsx"
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    return df

df = load_data()

# Aplicar estilos personalizados
st.markdown(
    """
    <style>
        .titulo-dashboard-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            margin: 0 auto;
            padding: 25px 20px;
            background: linear-gradient(to right, #F37529, rgba(255, 255, 255, 0.8));
            border-radius: 15px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
        }
        .titulo-dashboard {
            font-size: 50px;
            font-weight: bold;
            color: #F37529;
            text-transform: uppercase;
            margin: 0;
        }
        .subtitulo-dashboard {
            font-size: 18px;
            color: #555555;
            margin: 10px 0 0 0;
        }
        .filters-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }
        .filter-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 200px;
        }
        .dataframe-container {
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título do Dashboard
st.markdown(
    """
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Dashboard de Janelas Disponíveis para Agendamento</h1>
        <p class="subtitulo-dashboard">Torre de Controle - Dashboard de Janelas no Porto</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Informar a origem da tabela
st.markdown(
    """
    <div style="text-align: center; margin-top: 20px;">
        <h3>Janelas Disponíveis no Site da Rio Brasil Terminal</h3>
        <p>Consulta realizada no site da Rio Brasil Terminal</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Criar filtros abaixo do título
st.markdown('<div class="filters-container">', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    dates = st.multiselect("Selecione a Data", df["Dia"].unique())
with col2:
    types = st.multiselect("Selecione o Tipo", df["Tipo"].unique())
with col3:
    windows = st.multiselect("Selecione a Janela", df["Janela"].unique())
with col4:
    horas_iniciais = st.multiselect("Selecione a Hora Inicial", df["Hora Inicial"].unique())
with col5:
    horas_finais = st.multiselect("Selecione a Hora Final", df["Hora Final"].unique())

st.markdown('</div>', unsafe_allow_html=True)

# Aplicar filtros
filtered_df = df.copy()
if dates:
    filtered_df = filtered_df[filtered_df["Dia"].isin(dates)]
if types:
    filtered_df = filtered_df[filtered_df["Tipo"].isin(types)]
if windows:
    filtered_df = filtered_df[filtered_df["Janela"].isin(windows)]
if horas_iniciais:
    filtered_df = filtered_df[filtered_df["Hora Inicial"].isin(horas_iniciais)]
if horas_finais:
    filtered_df = filtered_df[filtered_df["Hora Final"].isin(horas_finais)]

# Seleção de colunas para exibição
available_columns = list(filtered_df.columns)
selected_columns = st.multiselect("Selecione as colunas para exibir:", available_columns, default=available_columns)

# Garantir que a coluna "Dia" esteja presente para ser usada como índice
if "Dia" not in selected_columns:
    selected_columns.insert(0, "Dia")

# Exibir tabela estilizada com a coluna "Dia" como índice (removendo o índice padrão)
st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
st.dataframe(filtered_df[selected_columns].set_index("Dia"), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Botão para exportar os dados filtrados em CSV
csv_data = filtered_df[selected_columns].to_csv(index=False, sep=';', encoding='utf-8-sig')
st.download_button(
    label="📥 Baixar dados filtrados em CSV",
    data=csv_data.encode('utf-8-sig'),
    file_name="janelas_filtradas.csv",
    mime="text/csv"
)
