import streamlit as st
import io
import json
import pandas as pd
import datetime
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
        # Se for Google Sheets, exporta como XLSX
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
# FUNÇÃO AUXILIAR DE RENOMEAÇÃO DAS COLUNAS (para Multirio)
# =============================================================================
def abbreviate_column(col_name: str) -> str:
    """
    Retorna a abreviação da coluna, se existir; caso contrário, retorna o nome original.
    """
    mapping = {
        "ENTREGA CHEIO Disp.": "ECH",
        "ENTREGA VAZIO Disp.": "EVZ",
        "RETIRADA CHEIO Disp.": "RCH",
        "RETIRADA VAZIO Disp.": "RVZ",
        "RETIRADA CARGA SOLTA Disp.": "RCS"
    }
    return mapping.get(col_name, col_name)


# =============================================================================
# FUNÇÃO PARA COMBINAR COLUNAS DUPLICADAS (caso apareçam após merges)
# =============================================================================
def merge_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada coluna duplicada, combina os valores pegando o primeiro valor não nulo.
    Retorna um DataFrame com colunas únicas.
    """
    combined = {}
    for col in df.columns.unique():
        dup = df.loc[:, df.columns == col]
        if dup.shape[1] > 1:
            combined[col] = dup.bfill(axis=1).iloc[:, 0]
        else:
            combined[col] = dup.iloc[:, 0]
    return pd.DataFrame(combined)


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
        /* Container e estilo do título principal */
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
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            margin-bottom: 20px;
        }
        .logo-container img {
            max-width: 200px;
            height: auto;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
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

# 1) ----------------- DADOS DO MULTIRIO -----------------
# Principais colunas de disponibilidade
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

df_multirio_unified = df_multirio[expected_multirio_cols].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"


# 2) ----------------- DADOS DO RIO BRASIL TERMINAL -----------------
required_cols_rio = {
    "DATA", "HORA", "DESCRICAO", "DISPONÍVEL", "RESERVADA"
}
if not required_cols_rio.issubset(df_info.columns):
    st.error(
        "A planilha Rio Brasil Terminal não possui as colunas mínimas esperadas: "
        "DATA, HORA, DESCRICAO, DISPONÍVEL, RESERVADA."
    )
    st.stop()

df_info_renamed = df_info.copy()
df_info_renamed.rename(columns={"DATA": "Data", "HORA": "Horário"}, inplace=True)

# Converte para numérico e garante zero se vazio
for col in ["DISPONÍVEL", "RESERVADA"]:
    df_info_renamed[col] = pd.to_numeric(df_info_renamed[col], errors="coerce").fillna(0)

# Cria as colunas ECH, EVZ, RCH, RVZ, RCS
df_info_renamed["ECH"] = 0
df_info_renamed["EVZ"] = 0
df_info_renamed["RCH"] = 0
df_info_renamed["RVZ"] = 0
df_info_renamed["RCS"] = 0

# Mapeamento de DESCRICAO → coluna final
desc_to_col = {
    "EXPORTAÇÃO CHEIO": "ECH",
    "IMPORTAÇÃO CHEIO": "RCH",
    "EXPORTAÇÃO VAZIO": "EVZ",
    "IMPORTAÇÃO VAZIO": "RVZ",
    "ENTREGA CARGA SOLTA": "RCS"
}

# Preenche a coluna correspondente com (DISPONÍVEL - RESERVADA)
for desc, col_alvo in desc_to_col.items():
    mask = df_info_renamed["DESCRICAO"] == desc
    df_info_renamed.loc[mask, col_alvo] = df_info_renamed.loc[mask, "DISPONÍVEL"] - df_info_renamed.loc[mask, "RESERVADA"]

df_info_renamed["Terminal"] = "Rio Brasil Terminal"

# Fica só com as colunas iguais às do Multirio + Terminal
df_info_unified = df_info_renamed[[
    "Data", "Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"
]].copy()
df_info_unified["Terminal"] = "Rio Brasil Terminal"


# 3) ----------------- UNIFICAÇÃO E ORDENAÇÃO -----------------
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)

# Converter "Data" para datetime
df_unified["Data"] = pd.to_datetime(df_unified["Data"], errors="coerce", dayfirst=True).dt.date
df_unified.sort_values(by=["Data", "Horário"], inplace=True)


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


# =============================================================================
# ALERTA: PRÓXIMA JANELA DISPONÍVEL PARA HOJE
# =============================================================================
today = datetime.date.today()
current_hour = datetime.datetime.now().hour

df_today = df_unified[df_unified["Data"] == today].copy()
if not df_today.empty:
    # Extrai a hora inicial (Ex: "23:00 - 23:59" → "23")
    df_today["StartHour"] = (
        df_today["Horário"]
        .astype(str)
        .str.split(" - ")
        .str[0]
        .str.extract(r'(\d{1,2})')[0]
        .astype(float, errors="ignore")
    )
    # Filtra somente linhas >= hora atual
    df_next = df_today[df_today["StartHour"] >= current_hour].sort_values(by="StartHour", na_position="last")
    
    if not df_next.empty:
        next_window = df_next.iloc[0]
        # Exibe a quantidade em cada coluna ECH, EVZ, RCH, RVZ, RCS
        availability_str = (
            f"ECH: {int(next_window.get('ECH', 0))}, "
            f"EVZ: {int(next_window.get('EVZ', 0))}, "
            f"RCH: {int(next_window.get('RCH', 0))}, "
            f"RVZ: {int(next_window.get('RVZ', 0))}, "
            f"RCS: {int(next_window.get('RCS', 0))}"
        )
        st.info(
            f"**Próxima janela disponível**: {next_window['Horário']} - Terminal: {next_window['Terminal']}.\n"
            f"Disponibilidade: {availability_str}"
        )
    else:
        st.info("Não há janelas disponíveis para o restante do dia.")
else:
    st.info("Não há dados para o dia de hoje.")


# =============================================================================
# EXIBIÇÃO DAS TABELAS (D, D+1, D+2)
# =============================================================================
unique_dates = sorted(df_unified["Data"].dropna().unique())
if len(unique_dates) < 3:
    st.warning("Menos de 3 dias disponíveis. Exibindo as datas que existirem na planilha.")

cols_display = st.columns(3)
table_titles = ["D", "D+1", "D+2"]

for i in range(3):
    with cols_display[i]:
        st.markdown(f"<h3 style='text-align: center; color: black;'>{table_titles[i]}</h3>", unsafe_allow_html=True)
        
        if i < len(unique_dates):
            date_x = unique_dates[i]
            df_data = df_unified[df_unified["Data"] == date_x].copy()
            
            # Filtra apenas janelas com disponibilidade > 0 em ECH, EVZ, RCH, RVZ, RCS
            df_data = df_data[df_data.apply(row_has_valid_availability, axis=1)].copy()
            
            # Se for hoje, mostra apenas horários >= hora atual
            if date_x == today:
                df_data["StartHour"] = (
                    df_data["Horário"]
                    .astype(str)
                    .str.split(" - ")
                    .str[0]
                    .str.extract(r'(\d{1,2})')[0]
                    .astype(float, errors="ignore")
                )
                df_data = df_data[df_data["StartHour"] >= current_hour].copy()
                df_data.drop(columns=["StartHour"], inplace=True, errors="ignore")
            
            # Retira "Data" e Terminal para tratar índices separadamente
            df_data.drop(columns=["Data"], inplace=True, errors="ignore")
            terminal_aux = df_data["Terminal"].copy()
            df_data.drop(columns=["Terminal"], inplace=True)
            
            # Renomeia possíveis colunas do Multirio (ENTREGA CHEIO Disp. → ECH, etc.)
            df_data.rename(columns=abbreviate_column, inplace=True)
            
            # Combina colunas duplicadas, se existirem
            df_data = merge_duplicate_columns(df_data)
            
            # Mantém só as colunas: Horário, ECH, EVZ, RCH, RVZ, RCS
            keep_cols = ["Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"]
            df_data = df_data[[c for c in keep_cols if c in df_data.columns]]
            
            # Agora **resetamos** o índice de ambos para evitar KeyError no Styler
            df_data.reset_index(drop=True, inplace=True)
            terminal_aux.reset_index(drop=True, inplace=True)
            
            # Estilização por terminal (usa .iloc[row.name])
            styled_data = df_data.style.apply(
                lambda row: highlight_terminal_mod(row, terminal_aux.iloc[row.name]),
                axis=1
            )
            # Formata as colunas numéricas
            num_cols = df_data.select_dtypes(include=["number"]).columns
            styled_data = styled_data.format("{:.0f}", subset=num_cols)
            
            if df_data.empty:
                st.write("Sem janelas disponíveis.")
            else:
                st.dataframe(styled_data, use_container_width=True, hide_index=True)
        else:
            st.write("Sem dados")


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
