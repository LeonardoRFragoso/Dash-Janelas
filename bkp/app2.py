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
    credentials_path = r"C:\Users\leonardo.fragoso\Desktop\Projetos\Dash-Janelas\gdrive_credentials.json"
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
# Função para abreviar os nomes das colunas (para exibição)
# ======================================================

def abbreviate_column(col_name):
    mapping = {
        "RETIRADA CHEIO Disp.": "CH",
        "RETIRADA VAZIO Disp.": "VZ",
        "RETIRADA CARGA SOLTA Disp.": "CS"
    }
    if col_name in mapping:
        return mapping[col_name]
    return col_name

# ======================================================
# Configuração da página
# ======================================================

st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

# ======================================================
# Sidebar: Logo e Título
# ======================================================

with st.sidebar:
    st.image(r"C:\Users\leonardo.fragoso\Desktop\Projetos\Dash-Janelas\itracker_logo.png", width=250)
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

# --- Processamento dos dados para cada empresa ---

# Para Multirio: usar apenas as colunas específicas de disponibilidade
disp_cols = [col for col in df_multirio.columns if col in [
    "RETIRADA CHEIO Disp.",
    "RETIRADA VAZIO Disp.",
    "RETIRADA CARGA SOLTA Disp."
]]
if not disp_cols:
    st.error("Nenhuma coluna específica de disponibilidade encontrada na planilha do Multirio.")
    st.stop()

cols_multirio = ["Data", "JANELAS MULTIRIO"] + disp_cols
df_multirio_unified = df_multirio[cols_multirio].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"

# Para Rio Brasil Terminal: usar as colunas "Dia", "Hora Inicial", "Hora Final", "Qtd Veículos Reservados"
required_cols = {"Dia", "Hora Inicial", "Hora Final", "Qtd Veículos Reservados"}
if not required_cols.issubset(df_info.columns):
    st.error("Colunas necessárias não encontradas na planilha de informações.")
    st.stop()

df_info_renamed = df_info.rename(columns={"Dia": "Data"})
df_info_renamed["Horário"] = df_info_renamed["Hora Inicial"].astype(str) + " - " + df_info_renamed["Hora Final"].astype(str)
df_info_unified = df_info_renamed[["Data", "Horário", "Qtd Veículos Reservados"]].copy()
df_info_unified["Terminal"] = "Rio Brasil Terminal"

# Unificar os dados
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)
df_unified["Data"] = pd.to_datetime(df_unified["Data"], errors="coerce", dayfirst=True).dt.date
df_unified.sort_values(by=["Data", "Horário"], inplace=True)

# ======================================================
# Função para filtrar linhas com dados válidos conforme o terminal
# ======================================================

def row_has_valid_availability(row):
    # Para Rio Brasil Terminal, considere válida se "Qtd Veículos Reservados" for numérico e diferente de 0.
    if row["Terminal"] == "Rio Brasil Terminal":
        try:
            val = float(row["Qtd Veículos Reservados"])
        except:
            val = 0
        return pd.notna(row["Qtd Veículos Reservados"]) and val != 0
    # Para Multirio, considere válida se ao menos uma das colunas de disponibilidade tiver valor numérico diferente de 0.
    elif row["Terminal"] == "Multirio":
        for col in disp_cols:
            if col in row:
                try:
                    val = float(row[col])
                except:
                    val = 0
                if pd.notna(row[col]) and str(row[col]).strip().lower() not in ["", "none"] and val != 0:
                    return True
        return False
    else:
        return False

# ======================================================
# Alerta Fixo: Próxima janela disponível e disponibilidade desta janela
# ======================================================

today = datetime.date.today()
current_hour = datetime.datetime.now().hour
df_today = df_unified[df_unified["Data"] == today].copy()

if not df_today.empty:
    # Extrair a hora inicial a partir da coluna "Horário"
    df_today['StartHour'] = df_today['Horário'].str.split(" - ").str[0].str.extract(r'(\d{1,2})')[0].astype(float)
    df_next = df_today[df_today['StartHour'] >= current_hour].sort_values(by='StartHour')
    if not df_next.empty:
        next_window = df_next.iloc[0]
        if next_window['Terminal'] == "Rio Brasil Terminal":
            available = next_window['Qtd Veículos Reservados']
            availability_str = f"{available}"
        elif next_window['Terminal'] == "Multirio":
            # Para Multirio, exibe a disponibilidade de cada coluna separadamente.
            avail_list = []
            for col in disp_cols:
                abbr = abbreviate_column(col)
                avail_list.append(f"{abbr}: {next_window[col]}")
            availability_str = ", ".join(avail_list)
        else:
            availability_str = "N/A"
        st.info(f"Próxima janela disponível: {next_window['Horário']} - Terminal: {next_window['Terminal']}.\n"
                f"Disponibilidade nesta janela: {availability_str}")
    else:
        st.info("Não há janelas disponíveis para o restante do dia.")
else:
    st.info("Não há dados para o dia de hoje.")

# ======================================================
# Função para estilizar as linhas conforme o terminal
# ======================================================

def highlight_terminal_mod(row, terminal_aux):
    idx = row.name
    term = terminal_aux.loc[idx]
    if term == "Multirio":
        return ['background-color: #00397F; color: white'] * len(row)
    elif term == "Rio Brasil Terminal":
        return ['background-color: #F37529; color: white'] * len(row)
    return [''] * len(row)

# ======================================================
# Exibição das Tabelas Lado a Lado para 3 dias (D, D+1 e D+2)
# ======================================================

unique_dates = sorted(df_unified["Data"].dropna().unique())
if len(unique_dates) < 3:
    st.warning("Menos de 3 dias disponíveis. Exibindo as datas disponíveis.")

cols_display = st.columns(3)
table_titles = ["D", "D+1", "D+2"]

for i in range(3):
    if i < len(unique_dates):
        data = unique_dates[i]
        df_data = df_unified[df_unified["Data"] == data].copy()
        df_data = df_data.drop(columns=["Data"], errors="ignore")
        
        # Aplicar filtragem de linhas válidas somente para disponibilidade:
        df_data = df_data[df_data.apply(row_has_valid_availability, axis=1)]
        
        numeric_cols = df_data.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            df_data = df_data[df_data[numeric_cols].fillna(0).sum(axis=1) != 0]
        
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
        
        # Para manter a informação do terminal para a estilização
        if "Terminal" in df_data.columns:
            terminal_aux = df_data["Terminal"].copy()
        else:
            terminal_aux = pd.Series([""] * len(df_data), index=df_data.index)
        
        # Abreviar os nomes das colunas para exibição e filtrar apenas as colunas desejadas:
        df_data = df_data.rename(columns=lambda col: abbreviate_column(col))
        cols_to_keep = [col for col in df_data.columns if col in ["Horário", "CH", "VZ", "CS"]]
        df_data = df_data[cols_to_keep]
        
        with cols_display[i]:
            title = table_titles[i]
            st.markdown(f"<h3 style='text-align: center; color: black;'>{title}</h3>", unsafe_allow_html=True)
            
            if df_data.empty:
                st.write("Sem dados para exibição")
            else:
                styled_data = df_data.style.apply(lambda row: highlight_terminal_mod(row, terminal_aux), axis=1)
                # Formatação para colunas numéricas, se houver
                numeric_cols = df_data.select_dtypes(include=['number']).columns
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

legend_html = """
<b>Legenda - Abreviações</b><br>
<ul style="list-style: none; padding-left: 0;">
    <li><b>CH</b>: RETIRADA CHEIO Disp.</li>
    <li><b>VZ</b>: RETIRADA VAZIO Disp.</li>
    <li><b>CS</b>: RETIRADA CARGA SOLTA Disp.</li>
</ul>
"""

st.markdown("---")
st.markdown(
    "<b>Legenda - Terminais:</b><br>"
    "<span style='background-color:#00397F; color:white; padding:4px 8px; border-radius:4px;'>Multirio</span>&nbsp;&nbsp;"
    "<span style='background-color:#F37529; color:white; padding:4px 8px; border-radius:4px;'>Rio Brasil Terminal</span>",
    unsafe_allow_html=True
)
st.markdown(legend_html, unsafe_allow_html=True)
