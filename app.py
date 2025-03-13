import streamlit as st
import io
import json
import pandas as pd
import datetime
from datetime import timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# =============================================================================
# FUNÇÕES DE CARREGAMENTO DOS DADOS
# =============================================================================
def load_spreadsheet(file_id: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    Faz o download de um arquivo do Google Drive (Google Sheets ou Excel)
    e retorna um DataFrame.
    """
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
    """
    Carrega a planilha do Multirio (Google Sheets) via file_id.
    """
    file_id = "1gzqhOADx-VJstLHvM7VVm3iuGUuz3Vgu"  # ID da planilha janelas_multirio_corrigido.xlsx
    return load_spreadsheet(file_id)

def load_informacoes_janelas_data() -> pd.DataFrame:
    """
    Carrega a planilha do Rio Brasil Terminal (Google Sheets) via file_id.
    """
    file_id = "1fMeKSdRvZod7FkvWLKXwsZV32W6iSmbI"  # ID da nova planilha data.xlsx
    return load_spreadsheet(file_id)

# =============================================================================
# FUNÇÕES AUXILIARES PARA TRATAR OS HORÁRIOS
# =============================================================================
def get_end_hour(row: pd.Series):
    """
    Extrai a hora final (inteiro) do intervalo presente na coluna "Horário".
    Exemplo: para "00:00 - 23:00", retorna 23.
    """
    try:
        parts = row["Horário"].split(" - ")
        end_str = parts[1]
        end_hour = int(end_str.split(":")[0])
        return end_hour
    except:
        return None

def get_start_hour(row: pd.Series):
    """
    Extrai a hora inicial (inteiro) do intervalo presente na coluna "Horário".
    Exemplo: para "03:30 - 04:30", retorna 3.
    """
    try:
        parts = row["Horário"].split(" - ")
        start_str = parts[0]
        start_hour = int(start_str.split(":")[0])
        return start_hour
    except:
        return None

def get_window_order(row: pd.Series, current_hour: int):
    """
    Define um valor de ordenação para a janela:
    - Se a janela ainda não começou, usa a hora de início.
    - Se já está em andamento (current_hour >= start e current_hour < end), usa current_hour.
    - Caso contrário, retorna um valor alto (24).
    """
    try:
        start_hour = get_start_hour(row)
        end_hour = get_end_hour(row)
        if start_hour is None or end_hour is None:
            return 24
        if current_hour < start_hour:
            return start_hour
        elif current_hour < end_hour:
            return current_hour
        else:
            return 24
    except:
        return 24

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA E SIDEBAR
# =============================================================================
st.set_page_config(page_title="Dashboard de Janelas", layout="wide")
with st.sidebar:
    st.image(r"C:\Users\leonardo.fragoso\Desktop\Projetos\Dash-Janelas\itracker_logo.png", width=250)
    st.title("Dashboard de Janelas")
    st.markdown("**Torre de Controle - Dashboard de Janelas no Porto**")

# =============================================================================
# ESTILIZAÇÃO E EXIBIÇÃO DO TÍTULO PRINCIPAL
# =============================================================================
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
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Torre de Controle Itracker - Dashboard de Janelas</h1>
        <p class="subtitulo-dashboard">Monitorando em tempo real as operações das janelas no Porto</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# =============================================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS
# =============================================================================
try:
    df_multirio = load_janelas_multirio_data()
    df_info = load_informacoes_janelas_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados das planilhas: {e}")
    st.stop()

# =============================================================================
# MAPEAMENTO DE COLUNAS PARA A PLANILHA DA MULTIRIO
# =============================================================================
disp_cols = [
    "ENTREGA CHEIO Disp.",
    "ENTREGA VAZIO Disp.",
    "RETIRADA CHEIO Disp.",
    "RETIRADA VAZIO Disp.",
    "RETIRADA CARGA SOLTA Disp."
]
expected_multirio_cols = ["Data", "JANELAS MULTIRIO"] + disp_cols

if not set(expected_multirio_cols).issubset(df_multirio.columns):
    st.error("A planilha Multirio não tem as colunas esperadas (Data, JANELAS MULTIRIO, etc.).")
    st.stop()

# Ajusta o DataFrame da Multirio
df_multirio_unified = df_multirio[expected_multirio_cols].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"
df_multirio_unified["Data"] = pd.to_datetime(df_multirio_unified["Data"], errors="coerce", dayfirst=True).dt.date

# Mapeia as colunas de disponibilidade para as siglas esperadas
rename_map_multirio = {
    "ENTREGA CHEIO Disp.": "ECH",
    "ENTREGA VAZIO Disp.": "EVZ",
    "RETIRADA CHEIO Disp.": "RCH",
    "RETIRADA VAZIO Disp.": "RVZ",
    "RETIRADA CARGA SOLTA Disp.": "RCS"
}
df_multirio_unified.rename(columns=rename_map_multirio, inplace=True)

# =============================================================================
# PROCESSAMENTO DA PLANILHA DO RIO BRASIL TERMINAL
# =============================================================================
required_cols_rio = {"DATA", "HORA", "DESCRICAO", "DISPONÍVEL", "RESERVADA"}
if not required_cols_rio.issubset(df_info.columns):
    st.error(
        "A planilha Rio Brasil Terminal não possui as colunas mínimas esperadas: "
        "DATA, HORA, DESCRICAO, DISPONÍVEL, RESERVADA."
    )
    st.stop()

df_info_renamed = df_info.copy()
df_info_renamed.rename(columns={"DATA": "Data", "HORA": "Horário"}, inplace=True)

for col in ["DISPONÍVEL", "RESERVADA"]:
    df_info_renamed[col] = pd.to_numeric(df_info_renamed[col], errors="coerce").fillna(0)

# Cria as colunas de disponibilidade para o Rio
df_info_renamed["ECH"] = 0
df_info_renamed["EVZ"] = 0
df_info_renamed["RCH"] = 0
df_info_renamed["RVZ"] = 0
df_info_renamed["RCS"] = 0

desc_to_col = {
    "EXPORTAÇÃO CHEIO": "ECH",
    "IMPORTAÇÃO CHEIO": "RCH",
    "EXPORTAÇÃO VAZIO": "EVZ",
    "IMPORTAÇÃO VAZIO": "RVZ",
    "ENTREGA CARGA SOLTA": "RCS"
}

for desc, col_alvo in desc_to_col.items():
    mask = df_info_renamed["DESCRICAO"] == desc
    df_info_renamed.loc[mask, col_alvo] = df_info_renamed.loc[mask, "DISPONÍVEL"] - df_info_renamed.loc[mask, "RESERVADA"]

df_info_renamed["Terminal"] = "Rio Brasil Terminal"
df_info_renamed["Data"] = pd.to_datetime(df_info_renamed["Data"], errors="coerce", dayfirst=True).dt.date

df_info_unified = df_info_renamed[["Data", "Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS", "Terminal"]].copy()

# =============================================================================
# UNIFICAÇÃO DOS DOIS DATAFRAMES E AGRUPAMENTO
# =============================================================================
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)
# Agrupa por Data, Horário e Terminal, somando as colunas numéricas
df_unified = df_unified.groupby(["Data", "Horário", "Terminal"], as_index=False).sum()

# =============================================================================
# VARIÁVEIS GLOBAIS PARA FILTRAGEM POR HORÁRIO
# =============================================================================
today = datetime.date.today()
current_hour = datetime.datetime.now().hour

# =============================================================================
# FUNÇÕES DE PROCESSAMENTO E ESTILIZAÇÃO
# =============================================================================
def row_has_valid_availability(row: pd.Series) -> bool:
    """
    Verifica se a linha possui disponibilidade (> 0) em alguma das colunas ECH, EVZ, RCH, RVZ, RCS.
    """
    for col in ["ECH", "EVZ", "RCH", "RVZ", "RCS"]:
        if row.get(col, 0) > 0:
            return True
    return False

def highlight_terminal_mod(row: pd.Series, terminal_value: str) -> list:
    """
    Retorna a formatação de estilo para a linha com base no valor do Terminal.
    """
    if terminal_value == "Multirio":
        return ["background-color: #00397F; color: white"] * len(row)
    elif terminal_value == "Rio Brasil Terminal":
        return ["background-color: #F37529; color: white"] * len(row)
    return [""] * len(row)

def get_next_window(df: pd.DataFrame):
    """
    Retorna a próxima janela disponível do dia atual, considerando que a janela
    está disponível se a hora atual for menor que o horário final.
    Ordena as janelas usando a função get_window_order.
    """
    df_today = df[df["Data"] == today].copy()
    if not df_today.empty:
        df_today["Order"] = df_today.apply(lambda row: get_window_order(row, current_hour), axis=1)
        # Filtra janelas que ainda não terminaram: current_hour < horário final
        df_today = df_today[df_today.apply(lambda row: current_hour < get_end_hour(row), axis=1)]
        df_today.sort_values(by="Order", inplace=True, na_position="last")
        if not df_today.empty:
            return df_today.iloc[0]
    return None

# =============================================================================
# EXIBIÇÃO DAS PRÓXIMAS JANELAS (RIO E MULTIRIO)
# =============================================================================
next_window_rio = get_next_window(df_info_unified)
next_window_multirio = get_next_window(df_multirio_unified)

if next_window_rio is not None:
    availability_str = (
        f"ECH: {int(next_window_rio.get('ECH', 0))}, "
        f"EVZ: {int(next_window_rio.get('EVZ', 0))}, "
        f"RCH: {int(next_window_rio.get('RCH', 0))}, "
        f"RVZ: {int(next_window_rio.get('RVZ', 0))}, "
        f"RCS: {int(next_window_rio.get('RCS', 0))}"
    )
    st.info(
        f"**Próxima janela disponível para Rio Brasil Terminal**: {next_window_rio['Horário']}.\n"
        f"Disponibilidade: {availability_str}"
    )
else:
    st.info("Não há janelas disponíveis para o restante do dia no Rio Brasil Terminal.")

if next_window_multirio is not None:
    availability_str = (
        f"ECH: {int(next_window_multirio.get('ECH', 0))}, "
        f"EVZ: {int(next_window_multirio.get('EVZ', 0))}, "
        f"RCH: {int(next_window_multirio.get('RCH', 0))}, "
        f"RVZ: {int(next_window_multirio.get('RVZ', 0))}, "
        f"RCS: {int(next_window_multirio.get('RCS', 0))}"
    )
    st.info(
        f"**Próxima janela disponível para Multirio**: {next_window_multirio['Horário']}.\n"
        f"Disponibilidade: {availability_str}"
    )
else:
    st.info("Não há janelas disponíveis para o restante do dia no Multirio.")

# =============================================================================
# EXIBIÇÃO DAS TABELAS (D, D+1, D+2) - TABELA ÚNICA POR DIA
# =============================================================================
days_list = [today, today + timedelta(days=1), today + timedelta(days=2)]
table_titles = ["D", "D+1", "D+2"]

for i, day in enumerate(days_list):
    st.markdown(f"### {table_titles[i]} - {day.strftime('%d/%m/%Y')}")
    # Filtra todas as linhas do dia
    df_day = df_unified[df_unified["Data"] == day].copy()
    
    # Para o dia atual, filtra janelas que ainda não terminaram (current_hour < horário final)
    if day == today:
        df_day = df_day[df_day.apply(lambda row: current_hour < get_end_hour(row), axis=1)].copy()
    
    # Mantém apenas linhas com disponibilidade válida
    df_day = df_day[df_day.apply(row_has_valid_availability, axis=1)].copy()
    
    if not df_day.empty:
        # Ordena usando uma coluna auxiliar
        df_day["Order"] = df_day.apply(lambda row: get_window_order(row, current_hour), axis=1)
        df_day.sort_values(by="Order", inplace=True, na_position="last")
        df_day.drop(columns=["Order"], inplace=True, errors="ignore")
    
    # Extrai a coluna "Terminal" para estilização e, em seguida, remove-a da exibição
    terminal_series = df_day["Terminal"].reset_index(drop=True).copy()
    df_day_display = df_day.drop(columns=["Terminal"]).reset_index(drop=True)
    
    # Aplica a estilização utilizando a série auxiliar
    styled_data = df_day_display.style.apply(
        lambda row: highlight_terminal_mod(row, terminal_series.iloc[row.name]),
        axis=1
    )
    
    # Define a ordem de exibição desejada
    display_cols = ["Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"]
    df_day_display = df_day_display[[c for c in display_cols if c in df_day_display.columns]]
    df_day_display.reset_index(drop=True, inplace=True)
    
    num_cols = df_day_display.select_dtypes(include=["number"]).columns
    styled_data = styled_data.format("{:.0f}", subset=num_cols)
    
    if df_day_display.empty:
        st.write("Sem janelas disponíveis.")
    else:
        st.dataframe(styled_data, use_container_width=True, hide_index=True)

# =============================================================================
# LEGENDA
# =============================================================================
legend_html = """
<b>Legenda - Abreviações (Multirio)</b><br>
<ul style="list-style: none; padding-left: 0;">
    <li><b>ECH</b>: entrega de cheio</li>
    <li><b>EVZ</b>: entrega de vazio</li>
    <li><b>RCH</b>: retirada de cheio</li>
    <li><b>RVZ</b>: retirada de vazio</li>
    <li><b>RCS</b>: retirada de carga solta</li>
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
