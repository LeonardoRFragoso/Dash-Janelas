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
    file_id = "1Eh58MkuHwyHpYCscMPD9X1r_83dbHV63"  # Ajuste para o ID real
    return load_spreadsheet(file_id)


def load_informacoes_janelas_data() -> pd.DataFrame:
    """
    Carrega a planilha do Rio Brasil Terminal (Google Sheets) via file_id.
    """
    file_id = "1prMkez7J-wbWUGbZp-VLyfHtisSLi-XQ"  # ID informado
    return load_spreadsheet(file_id)


# =============================================================================
# FUNÇÃO AUXILIAR DE RENOMEAÇÃO DAS COLUNAS
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
# FUNÇÃO PARA COMBINAR COLUNAS DUPLICADAS
# =============================================================================
def merge_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada coluna duplicada, combina os valores pegando o primeiro valor não nulo.
    Retorna um DataFrame com colunas únicas.
    """
    combined = {}
    for col in df.columns.unique():
        # Se houver duplicatas, pega todas e preenche para pegar o primeiro não-nulo
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

# ----------------- Dados do Multirio -----------------
mapping_keys = [
    "ENTREGA CHEIO Disp.",
    "ENTREGA VAZIO Disp.",
    "RETIRADA CHEIO Disp.",
    "RETIRADA VAZIO Disp.",
    "RETIRADA CARGA SOLTA Disp."
]

# Seleciona as colunas de disponibilidade e valida a existência
disp_cols = [col for col in df_multirio.columns if col in mapping_keys]
if not disp_cols:
    st.error("Nenhuma coluna de disponibilidade encontrada na planilha do Multirio.")
    st.stop()

expected_multirio_cols = ["Data", "JANELAS MULTIRIO"] + disp_cols
if not set(expected_multirio_cols).issubset(df_multirio.columns):
    st.error("A planilha Multirio não tem as colunas esperadas (Data, JANELAS MULTIRIO, etc.).")
    st.stop()

# Cria um DataFrame unificado para o Multirio
df_multirio_unified = df_multirio[expected_multirio_cols].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"


# ----------------- Dados do Rio Brasil Terminal -----------------
required_cols_rio = {"Dia", "Hora Inicial", "Hora Final", "ECH", "RCH"}
if not required_cols_rio.issubset(df_info.columns):
    st.error("A planilha Rio Brasil Terminal não possui as colunas esperadas.")
    st.stop()

df_info_renamed = df_info.rename(columns={"Dia": "Data"})
df_info_renamed["Horário"] = (
    df_info_renamed["Hora Inicial"].astype(str) +
    " - " +
    df_info_renamed["Hora Final"].astype(str)
)
# Converte valores numéricos e garante que as colunas existam
df_info_renamed["ECH"] = pd.to_numeric(df_info_renamed["ECH"], errors="coerce").fillna(0)
df_info_renamed["RCH"] = pd.to_numeric(df_info_renamed["RCH"], errors="coerce").fillna(0)
for col in ["EVZ", "RVZ", "RCS"]:
    if col not in df_info_renamed.columns:
        df_info_renamed[col] = 0

df_info_unified = df_info_renamed[["Data", "Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"]].copy()
df_info_unified["Terminal"] = "Rio Brasil Terminal"


# ----------------- Unificação e ordenação dos dados -----------------
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)
df_unified["Data"] = pd.to_datetime(df_unified["Data"], errors="coerce", dayfirst=True).dt.date
df_unified.sort_values(by=["Data", "Horário"], inplace=True)


# =============================================================================
# FUNÇÕES DE PROCESSAMENTO E ESTILIZAÇÃO
# =============================================================================
def row_has_valid_availability(row: pd.Series) -> bool:
    """
    Verifica se a linha possui disponibilidade válida (> 0) de acordo com o Terminal.
    """
    if row["Terminal"] == "Rio Brasil Terminal":
        return (row.get("ECH", 0) != 0 or row.get("RCH", 0) != 0)
    elif row["Terminal"] == "Multirio":
        for col in disp_cols:
            try:
                if float(row.get(col, 0)) != 0:
                    return True
            except (ValueError, TypeError):
                continue
        return False
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
    df_today["StartHour"] = (
        df_today["Horário"]
        .str.split(" - ")
        .str[0]
        .str.extract(r'(\d{1,2})')[0]
        .astype(float, errors="ignore")
    )
    df_next = df_today[df_today["StartHour"] >= current_hour].sort_values(by="StartHour", na_position="last")
    
    if not df_next.empty:
        next_window = df_next.iloc[0]
        if next_window["Terminal"] == "Rio Brasil Terminal":
            availability_str = f"ECH: {next_window.get('ECH', 0)}, RCH: {next_window.get('RCH', 0)}"
        elif next_window["Terminal"] == "Multirio":
            disp_list = [f"{abbreviate_column(col)}: {next_window.get(col, 0)}" for col in disp_cols]
            availability_str = ", ".join(disp_list)
        else:
            availability_str = "N/A"
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
    st.warning("Menos de 3 dias disponíveis. Exibindo as datas disponíveis.")

cols_display = st.columns(3)
table_titles = ["D", "D+1", "D+2"]

for i in range(3):
    with cols_display[i]:
        st.markdown(f"<h3 style='text-align: center; color: black;'>{table_titles[i]}</h3>", unsafe_allow_html=True)
        if i < len(unique_dates):
            date_x = unique_dates[i]
            df_data = df_unified[df_unified["Data"] == date_x].copy()
            # Remove a coluna 'Data' para exibição
            df_data.drop(columns=["Data"], inplace=True, errors="ignore")
            
            # Filtra as linhas com disponibilidade válida
            df_data = df_data[df_data.apply(row_has_valid_availability, axis=1)].copy()
            
            # Para hoje, filtra apenas horários a partir da hora atual
            if date_x == today and "Horário" in df_data.columns:
                df_data["StartHour"] = (
                    df_data["Horário"]
                    .str.split(" - ")
                    .str[0]
                    .str.extract(r'(\d{1,2})')[0]
                    .astype(float, errors="ignore")
                )
                df_data = df_data[df_data["StartHour"] >= current_hour].copy()
                df_data.drop(columns=["StartHour"], inplace=True, errors="ignore")
            
            # Reseta o índice para garantir que seja único
            df_data.reset_index(drop=True, inplace=True)
            
            # Armazena a coluna 'Terminal' separadamente e remove-a do DataFrame
            if "Terminal" in df_data.columns:
                terminal_aux = df_data["Terminal"].copy()
                df_data.drop(columns=["Terminal"], inplace=True)
            else:
                terminal_aux = pd.Series([""] * len(df_data), index=df_data.index)
            
            # Renomeia as colunas usando a função de abreviação
            df_data.rename(columns=abbreviate_column, inplace=True)
            keep_cols = ["Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"]
            df_data = df_data[[col for col in keep_cols if col in df_data.columns]]
            
            # Se após a renomeação houver duplicidade nas colunas, combine-as
            df_data = merge_duplicate_columns(df_data)
            
            # Aplica a estilização usando a série terminal_aux (pelo índice da linha)
            styled_data = df_data.style.apply(
                lambda row: highlight_terminal_mod(row, terminal_aux.loc[row.name]),
                axis=1
            )
            # Formata as colunas numéricas sem casas decimais
            num_cols = df_data.select_dtypes(include=["number"]).columns
            styled_data = styled_data.format("{:.0f}", subset=num_cols)
            st.dataframe(styled_data, use_container_width=True, hide_index=True)
        else:
            st.write("Sem dados")


# =============================================================================
# LEGENDA
# =============================================================================
legend_html = """
<b>Legenda - Abreviações</b><br>
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
