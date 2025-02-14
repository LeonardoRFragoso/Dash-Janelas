import streamlit as st
import io
import json
import pandas as pd
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ======================================================
# Funções para carregar os dados das planilhas do Google Drive
# ======================================================

def load_spreadsheet(file_id: str, sheet_name: str = 0) -> pd.DataFrame:
    credentials_path = r"C:\Users\leona\OneDrive\Documentos\Dash-Janelas\gdrive_credentials.json"
    with open(credentials_path, 'r') as f:
        credentials_info = json.load(f)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    drive_service = build('drive', 'v3', credentials=credentials)
    file_metadata = drive_service.files().get(fileId=file_id, fields='mimeType').execute()
    mime_type = file_metadata.get('mimeType')
    
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
    file_id = "1Eh58MkuHwyHpYCscMPD9X1r_83dbHV63"
    return load_spreadsheet(file_id)

def load_informacoes_janelas_data() -> pd.DataFrame:
    file_id = "1prMkez7J-wbWUGbZp-VLyfHtisSLi-XQ"
    return load_spreadsheet(file_id)

# ======================================================
# Configuração da página
# ======================================================

st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

# ======================================================
# Sidebar: Logo e Título
# ======================================================

with st.sidebar:
    st.image("https://drive.google.com/thumbnail?id=1wwRzTvBlg5ejwY_O7xWz4ZDdW77YNh2q&sz=w500", width=200)
    st.title("Dashboard de Janelas")
    st.markdown("**Torre de Controle - Dashboard de Janelas no Porto**")

# ======================================================
# Processamento dos Dados
# ======================================================

try:
    df_multirio = load_janelas_multirio_data()
    df_info = load_informacoes_janelas_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados das planilhas: {e}")
    st.stop()

# Filtrar colunas relevantes para Multirio
disp_cols = [col for col in df_multirio.columns if col.strip().endswith("Disp.")]
if "ENTREGA CHEIO DL" in df_multirio.columns:
    disp_cols.append("ENTREGA CHEIO DL")
if not disp_cols:
    st.error("Nenhuma coluna com 'Disp.' encontrada na planilha janelas_multirio_corrigido.xlsx")
    st.stop()

cols_multirio = ["Data", "JANELAS MULTIRIO"] + disp_cols
df_multirio_unified = df_multirio[cols_multirio].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"

# Filtrar colunas relevantes para Rio Brasil Terminal
required_cols = {"Dia", "Hora Inicial", "Hora Final", "Qtd Veículos Reservados"}
if not required_cols.issubset(df_info.columns):
    st.error("Colunas necessárias não encontradas na planilha informacoes_janelas.xlsx")
    st.stop()

df_info_renamed = df_info.rename(columns={"Dia": "Data"})
df_info_renamed["Horário"] = df_info_renamed["Hora Inicial"].astype(str) + " - " + df_info_renamed["Hora Final"].astype(str)
df_info_unified = df_info_renamed[["Data", "Horário", "Qtd Veículos Reservados"]].copy()
df_info_unified["Terminal"] = "Rio Brasil Terminal"

# Unificar e converter a coluna Data para o tipo date
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)
df_unified["Data"] = pd.to_datetime(df_unified["Data"], errors="coerce", dayfirst=True).dt.date
df_unified.sort_values(by=["Data", "Horário"], inplace=True)

# ======================================================
# Exibição das Tabelas Lado a Lado para 3 dias (D, D+1 e D+2)
# ======================================================

# Função modificada de destaque que utiliza os valores da série "terminal_aux"
def highlight_terminal_mod(row, terminal_aux):
    idx = row.name
    term = terminal_aux.loc[idx]
    if term == "Multirio":
        return ['background-color: #00397F; color: white'] * len(row)
    elif term == "Rio Brasil Terminal":
        return ['background-color: #F37529; color: white'] * len(row)
    else:
        return [''] * len(row)

unique_dates = sorted(df_unified["Data"].dropna().unique())
if len(unique_dates) < 3:
    st.warning("Menos de 3 dias disponíveis. Exibindo as datas disponíveis.")

cols_display = st.columns(3)
today = datetime.date.today()
current_hour = datetime.datetime.now().hour

# Títulos personalizados para cada tabela
table_titles = ["D", "D+1", "D+2"]

for i in range(3):
    if i < len(unique_dates):
        data = unique_dates[i]
        df_data = df_unified[df_unified["Data"] == data].copy()
        # Remover a coluna "Data" para exibição
        df_data = df_data.drop(columns=["Data"], errors="ignore")
        
        # Filtrar linhas com soma dos valores numéricos diferente de 0
        numeric_cols = df_data.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            df_data = df_data[df_data[numeric_cols].fillna(0).sum(axis=1) != 0]
        
        # Se for o dia atual, filtrar para mostrar apenas horários a partir da hora atual
        if data == today and 'Horário' in df_data.columns:
            try:
                df_data['StartHour'] = (
                    df_data['Horário']
                    .str.split(" - ")
                    .str[0]
                    .str.extract(r'(\d{1,2})')[0]
                    .astype(float)
                )
                df_data = df_data[df_data['StartHour'] >= current_hour]
                df_data = df_data.drop(columns=['StartHour'])
            except Exception as e:
                st.error(f"Erro ao filtrar horários do dia atual: {e}")
        
        # Remover as colunas de índice 9 e 10, se existirem, preservando "Terminal"
        cols_to_drop = []
        for idx in [9, 10]:
            if idx < df_data.shape[1]:
                col_name = df_data.columns[idx]
                if col_name != "Terminal":
                    cols_to_drop.append(col_name)
        if cols_to_drop:
            df_data = df_data.drop(columns=cols_to_drop, errors="ignore")
        
        # Recalcular as colunas numéricas após a remoção
        numeric_cols = df_data.select_dtypes(include=['number']).columns
        
        with cols_display[i]:
            title = table_titles[i]
            st.markdown(f"<h3 style='text-align: center; color: black;'>{title}</h3>", unsafe_allow_html=True)
            
            if df_data.empty:
                st.write("Sem dados para exibição")
            else:
                # Salvar a coluna "Terminal" para uso na lógica de destaque
                if "Terminal" in df_data.columns:
                    terminal_aux = df_data["Terminal"].copy()
                    # Remover a coluna "Terminal" do DataFrame exibido
                    df_data = df_data.drop(columns=["Terminal"])
                else:
                    terminal_aux = pd.Series([""] * len(df_data), index=df_data.index)
                
                # Aplicar a função de estilo utilizando a série auxiliar
                styled_data = df_data.style.apply(lambda row: highlight_terminal_mod(row, terminal_aux), axis=1)
                if not numeric_cols.empty:
                    styled_data = styled_data.format("{:.0f}", subset=numeric_cols)
                
                st.dataframe(styled_data, use_container_width=True, hide_index=True)
    else:
        with cols_display[i]:
            st.markdown(f"<h3 style='text-align: center; color: black;'>{table_titles[i]}</h3>", unsafe_allow_html=True)
            st.write("Sem dados")

# ======================================================
# Legenda
# ======================================================

st.markdown("---")
st.markdown(
    "<b>Legenda:</b><br>"
    "<span style='background-color:#00397F; color:white; padding:4px 8px; border-radius:4px;'>Multirio</span>&nbsp;&nbsp;"
    "<span style='background-color:#F37529; color:white; padding:4px 8px; border-radius:4px;'>Rio Brasil Terminal</span>",
    unsafe_allow_html=True
)
