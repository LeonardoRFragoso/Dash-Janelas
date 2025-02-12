import streamlit as st
import pandas as pd
import io
import json  # Para converter a string em dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configuração da página para abrir em modo wide
st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

# Função para carregar dados do Google Drive (Google Sheets exportado como XLSX)
@st.cache_data(ttl=60)  # Cache com TTL de 60 segundos
def load_data():
    # Converte a string de credenciais em um dicionário
    credentials_info = json.loads(st.secrets["general"]["CREDENTIALS"])
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    # ID da planilha extraído da URL:
    # https://docs.google.com/spreadsheets/d/1prMkez7J-wbWUGbZp-VLyfHtisSLi-XQ/edit?pli=1&gid=1613900400#gid=1613900400
    file_id = "1prMkez7J-wbWUGbZp-VLyfHtisSLi-XQ"
    
    # Constrói o serviço do Google Drive
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Obtém os metadados do arquivo para identificar o mimeType
    file_metadata = drive_service.files().get(fileId=file_id, fields='mimeType').execute()
    mime_type = file_metadata.get('mimeType')
    
    # Baixa o arquivo para um objeto BytesIO
    fh = io.BytesIO()
    if mime_type == "application/vnd.google-apps.spreadsheet":
        # Se for um Google Sheet nativo, exporta para XLSX
        request = drive_service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        # Se for outro tipo de arquivo (ex.: Excel), baixa diretamente
        request = drive_service.files().get_media(fileId=file_id)
    
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    
    # Ler a planilha (ajuste o sheet_name se necessário)
    df = pd.read_excel(fh, sheet_name='Sheet1')
    return df

# Carrega os dados da planilha original
df = load_data()
if df is None:
    st.error("Não foi possível carregar os dados da planilha.")
    st.stop()

# Estilos personalizados: definindo container para o título com degradê
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
        .dataframe-container {
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Solução 1 - Centralizar a logo usando HTML + CSS
st.markdown(
    """
    <div style="display: flex; justify-content: center; margin-top: 20px; margin-bottom: 20px;">
        <img src="https://drive.google.com/thumbnail?id=1wwRzTvBlg5ejwY_O7xWz4ZDdW77YNh2q&sz=w500" width="200">
    </div>
    """,
    unsafe_allow_html=True,
)

# Exibir o container com o título e subtítulo (barra em degradê)
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

# Botão para atualizar os dados manualmente
if st.button("Atualizar Dados"):
    load_data.clear()       # Limpa o cache da função load_data
    st.experimental_rerun() # Recarrega a página para buscar os dados atualizados

# =============================
# PRIMEIRA TABELA (Planilha Original)
# =============================

# Criar filtros para a primeira tabela (6 colunas específicas)
st.markdown('<div class="filters-container">', unsafe_allow_html=True)
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    di_booking = st.multiselect("Selecione DI / BOOKING / CTE", df["DI / BOOKING / CTE"].unique())
with col2:
    dates = st.multiselect("Selecione a Data", df["Dia"].unique())
with col3:
    types = st.multiselect("Selecione o Tipo", df["Tipo"].unique())
with col4:
    windows = st.multiselect("Selecione a Janela", df["Janela"].unique())
with col5:
    horas_iniciais = st.multiselect("Selecione a Hora Inicial", df["Hora Inicial"].unique())
with col6:
    horas_finais = st.multiselect("Selecione a Hora Final", df["Hora Final"].unique())
st.markdown('</div>', unsafe_allow_html=True)

# Aplicar filtros na primeira tabela
filtered_df = df.copy()
if di_booking:
    filtered_df = filtered_df[filtered_df["DI / BOOKING / CTE"].isin(di_booking)]
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

# Seleção de colunas para exibição na primeira tabela
available_columns = list(filtered_df.columns)
selected_columns = st.multiselect("Selecione as colunas para exibir:", available_columns, default=available_columns)

# Garantir que as colunas "Dia" e "DI / BOOKING / CTE" estejam presentes
if "Dia" not in selected_columns:
    selected_columns.insert(0, "Dia")
if "DI / BOOKING / CTE" not in selected_columns:
    selected_columns.insert(1, "DI / BOOKING / CTE")

# Exibir a primeira tabela com a coluna "Dia" como índice
st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
st.dataframe(filtered_df[selected_columns].set_index("Dia"), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Botão para exportar os dados filtrados da primeira tabela em CSV
csv_data = filtered_df[selected_columns].to_csv(index=False, sep=';', encoding='utf-8-sig')
st.download_button(
    label="📥 Baixar dados filtrados em CSV",
    data=csv_data.encode('utf-8-sig'),
    file_name="janelas_filtradas.csv",
    mime="text/csv"
)

# ==========================================
# SEGUNDA SEÇÃO: Nova Planilha com Dropdown para Filtros
# ==========================================
st.markdown("<h2 style='text-align: center; margin-top: 40px;'>Dados da Nova Planilha (Janelas Multirio Corrigido)</h2>", unsafe_allow_html=True)

try:
    # Carrega a nova planilha utilizando o caminho informado
    df_nova = pd.read_excel(r"C:\Users\leonardo.fragoso\Desktop\Projetos\Dash-Janelas\janelas_multirio_corrigido.xlsx")
except Exception as e:
    st.error(f"Erro ao carregar a nova planilha: {e}")
    st.stop()

# Dropdown para escolher quais colunas deseja filtrar
selected_filter_columns = st.multiselect("Selecione as colunas para aplicar filtro", options=list(df_nova.columns))

# Para cada coluna selecionada, exibe um multiselect com os valores únicos
filters_nova = {}
for col in selected_filter_columns:
    unique_vals = df_nova[col].dropna().unique()
    filters_nova[col] = st.multiselect(f"Selecione os valores para filtrar por '{col}'", options=unique_vals, key=f"filter_{col}")

# Aplicar os filtros na nova planilha
filtered_df_nova = df_nova.copy()
for col, selected_vals in filters_nova.items():
    if selected_vals:
        filtered_df_nova = filtered_df_nova[filtered_df_nova[col].isin(selected_vals)]

# Seleção de colunas para exibição na nova planilha
available_columns_nova = list(filtered_df_nova.columns)
selected_columns_nova = st.multiselect("Selecione as colunas para exibir na Nova Planilha:", available_columns_nova, default=available_columns_nova)

# Exibir a nova tabela. Se a coluna "JANELAS MULTIRIO" estiver presente, utiliza-a como índice.
st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
if "JANELAS MULTIRIO" in selected_columns_nova:
    st.dataframe(filtered_df_nova[selected_columns_nova].set_index("JANELAS MULTIRIO"), use_container_width=True)
else:
    st.dataframe(filtered_df_nova[selected_columns_nova], use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Botão para exportar os dados filtrados da nova planilha em CSV
csv_data_nova = filtered_df_nova[selected_columns_nova].to_csv(index=False, sep=';', encoding='utf-8-sig')
st.download_button(
    label="📥 Baixar dados filtrados da Nova Planilha em CSV",
    data=csv_data_nova.encode('utf-8-sig'),
    file_name="janelas_multirio_corrigido_filtradas.csv",
    mime="text/csv"
)
