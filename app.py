import streamlit as st
import io
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ======================================================
# Funções para carregar os dados das planilhas do Google Drive
# ======================================================

def load_spreadsheet(file_id: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    Carrega um arquivo do Google Drive como planilha e retorna um DataFrame do Pandas.
    
    Parâmetros:
      - file_id: ID do arquivo no Google Drive.
      - sheet_name: Nome ou índice da aba da planilha a ser lida (padrão: 0 – primeira aba).
    
    Retorna:
      - DataFrame com os dados da planilha.
    """
    credentials_path = r"C:\Users\leonardo.fragoso\Desktop\Projetos\Dash-Janelas\gdrive_credentials.json"
    with open(credentials_path, 'r') as f:
        credentials_info = json.load(f)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Obtém os metadados para identificar o mimeType
    file_metadata = drive_service.files().get(fileId=file_id, fields='mimeType').execute()
    mime_type = file_metadata.get('mimeType')
    
    # Baixa o arquivo para um objeto BytesIO
    fh = io.BytesIO()
    if mime_type == "application/vnd.google-apps.spreadsheet":
        request = drive_service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        request = drive_service.files().get_media(fileId=file_id)
    
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    
    df = pd.read_excel(fh, sheet_name=sheet_name)
    return df

def load_janelas_multirio_data() -> pd.DataFrame:
    """
    Carrega os dados da planilha 'janelas_multirio_corrigido.xlsx'.
    
    URL: https://docs.google.com/spreadsheets/d/1Eh58MkuHwyHpYCscMPD9X1r_83dbHV63/edit?gid=927178025#gid=927178025
    """
    file_id = "1Eh58MkuHwyHpYCscMPD9X1r_83dbHV63"
    return load_spreadsheet(file_id)

def load_informacoes_janelas_data() -> pd.DataFrame:
    """
    Carrega os dados da planilha 'informacoes_janelas.xlsx'.
    
    URL: https://docs.google.com/spreadsheets/d/1prMkez7J-wbWUGbZp-VLyfHtisSLi-XQ/edit?gid=1452739125#gid=1452739125
    """
    file_id = "1prMkez7J-wbWUGbZp-VLyfHtisSLi-XQ"
    return load_spreadsheet(file_id)

# ======================================================
# Configuração da página e exibição da logo e título
# ======================================================

st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="display: flex; justify-content: center; margin-top: 20px; margin-bottom: 20px;">
        <img src="https://drive.google.com/thumbnail?id=1wwRzTvBlg5ejwY_O7xWz4ZDdW77YNh2q&sz=w500" width="200">
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Dashboard de Janelas Disponíveis para Agendamento</h1>
        <p class="subtitulo-dashboard">Torre de Controle - Dashboard de Janelas no Porto</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ======================================================
# Processamento dos Dados
# ======================================================

# Carrega os dados de ambas as planilhas
try:
    df_multirio = load_janelas_multirio_data()
    df_info = load_informacoes_janelas_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados das planilhas: {e}")
    st.stop()

# --- Processamento dos dados da planilha janelas_multirio_corrigido.xlsx ---
# Seleciona os campos originais:
# - "Data" e "JANELAS MULTIRIO" (que será renomeada para "Horário")
# - Todas as colunas cujo nome (após remover espaços) termina com "Disp."
# - Se existir, também inclui a coluna "ENTREGA CHEIO DL"
disp_cols = [col for col in df_multirio.columns if col.strip().endswith("Disp.")]
if "ENTREGA CHEIO DL" in df_multirio.columns:
    disp_cols.append("ENTREGA CHEIO DL")

if not disp_cols:
    st.error("Nenhuma coluna com 'Disp.' encontrada na planilha janelas_multirio_corrigido.xlsx")
    st.stop()

# Cria um DataFrame contendo os campos originais para a Multirio
cols_multirio = ["Data", "JANELAS MULTIRIO"] + disp_cols
df_multirio_unified = df_multirio[cols_multirio].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"

# --- Processamento dos dados da planilha informacoes_janelas.xlsx ---
# Verifica se as colunas necessárias existem
required_cols = {"Dia", "Hora Inicial", "Hora Final", "Qtd Veículos Reservados"}
if not required_cols.issubset(df_info.columns):
    st.error("Colunas necessárias não encontradas na planilha informacoes_janelas.xlsx")
    st.stop()

# Renomeia "Dia" para "Data" e cria o campo "Horário"
df_info_renamed = df_info.rename(columns={"Dia": "Data"})
df_info_renamed["Horário"] = df_info_renamed["Hora Inicial"].astype(str) + " - " + df_info_renamed["Hora Final"].astype(str)

# Seleciona os campos originais para o Rio Brasil Terminal
df_info_unified = df_info_renamed[["Data", "Horário", "Qtd Veículos Reservados"]].copy()
df_info_unified["Terminal"] = "Rio Brasil Terminal"

# --- Consolidação ---
# A união será feita pela união das colunas (o DataFrame resultante terá todas as colunas presentes)
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)
df_unified.sort_values(by=["Data", "Horário"], inplace=True)

# ======================================================
# Estilização da Tabela Unificada (Cor das Linhas)
# ======================================================

def highlight_terminal(row):
    """
    Aplica cor de fundo à linha com base no terminal.
      - Laranja (#FFA500) para Multirio.
      - Azul (#87CEFA) para Rio Brasil Terminal.
    """
    if row["Terminal"] == "Multirio":
        return ['background-color: #FFA500'] * len(row)
    elif row["Terminal"] == "Rio Brasil Terminal":
        return ['background-color: #87CEFA'] * len(row)
    else:
        return [''] * len(row)

# ======================================================
# Exibição das Tabelas Lado a Lado para 3 dias (D, D+1 e D+2)
# ======================================================

# Obtém os dias únicos (assumindo que a coluna "Data" contenha datas em formato compatível)
unique_dates = sorted(df_unified["Data"].unique())

if len(unique_dates) < 3:
    st.warning("Menos de 3 dias disponíveis. Exibindo as datas disponíveis.")

# Cria 3 colunas para exibição lado a lado
cols_display = st.columns(3)
for i in range(3):
    if i < len(unique_dates):
        data = unique_dates[i]
        df_data = df_unified[df_unified["Data"] == data].copy()
        # Reinicia o índice para garantir unicidade
        df_data = df_data.reset_index(drop=True)
        # Reordena as colunas para que "Data" seja a primeira coluna
        col_order = ["Data"] + [col for col in df_data.columns if col != "Data"]
        df_data = df_data[col_order]
        # Obtém as colunas numéricas para formatação
        num_cols = df_data.select_dtypes(include=['number']).columns
        # Aplica a estilização, formata os números como inteiros e oculta o índice
        styled_data = (
            df_data.style
            .apply(highlight_terminal, axis=1)
            .format({col: "{:.0f}" for col in num_cols})
            .hide(axis='index')
        )
        with cols_display[i]:
            st.markdown(f"### Data: {data}")
            st.dataframe(styled_data, use_container_width=True, hide_index=True)
    else:
        with cols_display[i]:
            st.markdown("### Data: N/A")
            st.write("Sem dados")
