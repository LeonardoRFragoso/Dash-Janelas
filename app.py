import streamlit as st
import io
import json
import pandas as pd
import datetime
from datetime import timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configuração da página
st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

# =============================================================================
# CSS GLOBAL: Estilização, Responsividade, Ícones, Tabelas e Cabeçalhos
# =============================================================================
st.markdown(
    """
    <style>
        /* Estilização do título principal */
        .titulo-dashboard-container {
            background: linear-gradient(135deg, #F37529 0%, #00397F 100%);
            border-radius: 15px;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
            padding: 30px 20px;
            margin-bottom: 25px;
            text-align: center;
        }
        .titulo-dashboard {
            font-size: 48px;
            font-weight: 800;
            color: white;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            margin: 0;
        }
        .subtitulo-dashboard {
            font-size: 20px;
            color: rgba(255, 255, 255, 0.9);
            margin-top: 15px;
        }
        /* Cartões de alerta */
        .card-alert {
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            margin-bottom: 20px;
            transition: transform 0.3s;
        }
        .card-alert:hover {
            transform: translateY(-5px);
        }
        .card-rio {
            background: linear-gradient(to right, #F37529, #FF9B52);
            color: white;
        }
        .card-multirio {
            background: linear-gradient(to right, #00397F, #0052B9);
            color: white;
        }
        /* Estilização das tabelas */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }
        .stDataFrame [data-testid="stDataFrameResizable"] {
            border-radius: 10px;
        }
        .stDataFrame th {
            background-color: #f0f2f6 !important;
            color: #444 !important;
            font-weight: 600 !important;
            padding: 12px 8px !important;
        }
        .stDataFrame td {
            padding: 10px 8px !important;
        }
        /* Cabeçalho dos dias (D, D+1, D+2) */
        .day-header {
            background: linear-gradient(to right, #333, #777);
            color: white;
            padding: 10px 15px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        }
        /* Ícones para a legenda */
        .icon-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .icon {
            width: 24px;
            height: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background-color: rgba(0, 0, 0, 0.1);
            margin-right: 5px;
        }
        /* Responsividade para dispositivos móveis */
        @media (max-width: 768px) {
            .titulo-dashboard {
                font-size: 32px;
            }
            .subtitulo-dashboard {
                font-size: 16px;
            }
            .availability-list {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# SIDEBAR MELHORADA
# =============================================================================
with st.sidebar:
    st.image("/home/dev/Documentos/Dash-Janelas/itracker_logo.png", width=200)
    
    st.markdown(
        """
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <h3 style="margin-top: 0;">Dashboard de Janelas</h3>
            <p style="margin-bottom: 5px;"><b>Torre de Controle</b></p>
            <p style="font-size: 14px; color: #666;">
                Monitore em tempo real a disponibilidade de janelas operacionais nos terminais.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    st.subheader("Filtros")
    terminal_filter = st.multiselect(
        "Terminal:",
        options=["Multirio", "Rio Brasil Terminal"],
        default=["Multirio", "Rio Brasil Terminal"]
    )

# =============================================================================
# TÍTULO PRINCIPAL
# =============================================================================
st.markdown(
    """
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Torre de Controle Itracker - Dashboard de Janelas</h1>
        <p class="subtitulo-dashboard">Monitorando em tempo real as operações das janelas no Porto</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# FUNÇÕES DE CARREGAMENTO DOS DADOS
# =============================================================================
def load_spreadsheet(file_id: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    Faz o download de um arquivo do Google Drive (Google Sheets ou Excel)
    e retorna um DataFrame.
    """
    credentials_path = "/home/dev/Documentos/Dash-Janelas/gdrive_credentials.json"
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
    try:
        parts = row["Horário"].split(" - ")
        end_str = parts[1]
        return int(end_str.split(":")[0])
    except:
        return None

def get_start_hour(row: pd.Series):
    try:
        parts = row["Horário"].split(" - ")
        start_str = parts[0]
        return int(start_str.split(":")[0])
    except:
        return None

def get_window_order(row: pd.Series, current_hour: int):
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
# CARREGAMENTO DOS DADOS COM INDICADOR DE PROGRESSO
# =============================================================================
with st.spinner('Carregando dados das janelas...'):
    try:
        df_multirio = load_janelas_multirio_data()
        df_info = load_informacoes_janelas_data()
    except Exception as e:
        st.error(f"Erro ao carregar os dados das planilhas: {e}")
        st.stop()
st.success('Dados carregados com sucesso!', icon="✅")

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

df_multirio_unified = df_multirio[expected_multirio_cols].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"
df_multirio_unified["Data"] = pd.to_datetime(df_multirio_unified["Data"], errors="coerce", dayfirst=True).dt.date

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
df_unified = df_unified.groupby(["Data", "Horário", "Terminal"], as_index=False).sum()

# Variáveis globais para filtragem por horário
today = datetime.date.today()
current_hour = datetime.datetime.now().hour

# =============================================================================
# FUNÇÕES DE PROCESSAMENTO E ESTILIZAÇÃO
# =============================================================================
def row_has_valid_availability(row: pd.Series) -> bool:
    for col in ["ECH", "EVZ", "RCH", "RVZ", "RCS"]:
        if row.get(col, 0) > 0:
            return True
    return False

def highlight_terminal_mod(row: pd.Series, terminal_value: str) -> list:
    if terminal_value == "Multirio":
        return ["background-color: #00397F; color: white"] * len(row)
    elif terminal_value == "Rio Brasil Terminal":
        return ["background-color: #F37529; color: white"] * len(row)
    return [""] * len(row)

def highlight_availability(val):
    """
    Retorna estilo para os valores de disponibilidade:
      - >= 8: fundo verde e texto em negrito;
      - 3 a 7: fundo amarelo;
      - 0: fundo vermelho claro e texto acinzentado;
      - Outros casos: fundo vermelho.
    """
    try:
        val = int(val)
        if val >= 8:
            return 'background-color: rgba(76, 175, 80, 0.3); font-weight: bold;'
        elif val >= 3:
            return 'background-color: rgba(255, 193, 7, 0.3);'
        elif val == 0:
            return 'background-color: rgba(244, 67, 54, 0.2); color: #999;'
        else:
            return 'background-color: rgba(244, 67, 54, 0.3);'
    except:
        return ''

def get_next_window(df: pd.DataFrame):
    df_today = df[df["Data"] == today].copy()
    if not df_today.empty:
        df_today["Order"] = df_today.apply(lambda row: get_start_hour(row), axis=1)
        df_today = df_today[df_today.apply(lambda row: current_hour < get_start_hour(row), axis=1)]
        df_today.sort_values(by="Order", inplace=True, na_position="last")
        if not df_today.empty:
            return df_today.iloc[0]
    return None

def format_availability(row: pd.Series) -> str:
    return f"""
    Disponibilidade:
    <ul style="margin: 5px 0 0 20px; padding: 0;">
        <li><b>ECH</b>: {int(row.get('ECH', 0))}</li>
        <li><b>EVZ</b>: {int(row.get('EVZ', 0))}</li>
        <li><b>RCH</b>: {int(row.get('RCH', 0))}</li>
        <li><b>RVZ</b>: {int(row.get('RVZ', 0))}</li>
        <li><b>RCS</b>: {int(row.get('RCS', 0))}</li>
    </ul>
    """

# =============================================================================
# CRIAÇÃO DA SEÇÃO DE KPIs
# =============================================================================
# Agregados por terminal
rio_aggregado = df_unified[df_unified["Terminal"] == "Rio Brasil Terminal"].copy()
multirio_aggregado = df_unified[df_unified["Terminal"] == "Multirio"].copy()

def create_kpi_section():
    total_slots_today = len(df_unified[df_unified["Data"] == today])
    total_availability = df_unified[df_unified["Data"] == today][["ECH", "EVZ", "RCH", "RVZ", "RCS"]].sum().sum()
    rio_slots = len(rio_aggregado[rio_aggregado["Data"] == today])
    multirio_slots = len(multirio_aggregado[multirio_aggregado["Data"] == today])
    
    kpi_html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 25px;">
        <div style="flex: 1; min-width: 150px; background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="margin: 0; color: #777; font-size: 14px;">Janelas Disponíveis Hoje</h4>
            <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #00397F;">{total_slots_today}</p>
        </div>
        <div style="flex: 1; min-width: 150px; background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="margin: 0; color: #777; font-size: 14px;">Total Disponibilidade</h4>
            <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #F37529;">{int(total_availability)}</p>
        </div>
        <div style="flex: 1; min-width: 150px; background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="margin: 0; color: #777; font-size: 14px;">Rio Brasil</h4>
            <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #F37529;">{rio_slots}</p>
        </div>
        <div style="flex: 1; min-width: 150px; background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="margin: 0; color: #777; font-size: 14px;">Multirio</h4>
            <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #00397F;">{multirio_slots}</p>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

create_kpi_section()

# =============================================================================
# IDENTIFICAÇÃO DAS PRÓXIMAS JANELAS
# =============================================================================
next_window_rio = get_next_window(rio_aggregado)
next_window_multirio = get_next_window(multirio_aggregado)

# =============================================================================
# EXIBIÇÃO DOS ALERTAS (PRÓXIMAS JANELAS)
# =============================================================================
col_alerts = st.columns(2)
with col_alerts[0]:
    if next_window_rio is not None:
        availability_html_rio = format_availability(next_window_rio)
        st.markdown(
            f"""
            <div class="card-alert card-rio">
                <strong>Próxima janela disponível para Rio Brasil Terminal</strong>: {next_window_rio['Horário']}<br>
                {availability_html_rio}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="card-alert card-rio">
                Não há janelas disponíveis para o restante do dia no Rio Brasil Terminal.
            </div>
            """,
            unsafe_allow_html=True
        )

with col_alerts[1]:
    if next_window_multirio is not None:
        availability_html_multi = format_availability(next_window_multirio)
        st.markdown(
            f"""
            <div class="card-alert card-multirio">
                <strong>Próxima janela disponível para Multirio</strong>: {next_window_multirio['Horário']}<br>
                {availability_html_multi}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="card-alert card-multirio">
                Não há janelas disponíveis para o restante do dia no Multirio.
            </div>
            """,
            unsafe_allow_html=True
        )

# =============================================================================
# CABEÇALHO PARA OS DIAS (D, D+1, D+2)
# =============================================================================
def create_day_header(day_label, date_str):
    return f"""
    <div class="day-header">
        <span style="font-size: 20px;">{day_label}</span><br>
        <span style="font-size: 16px;">{date_str}</span>
    </div>
    """

# =============================================================================
# EXIBIÇÃO DAS TABELAS DIÁRIAS
# =============================================================================
days_list = [today, today + timedelta(days=1), today + timedelta(days=2)]
table_titles = ["D", "D+1", "D+2"]

cols = st.columns(3)
for i, day in enumerate(days_list):
    with cols[i]:
        st.markdown(create_day_header(table_titles[i], day.strftime('%d/%m/%Y')), unsafe_allow_html=True)
        df_day = df_unified[df_unified["Data"] == day].copy()
        
        # Para o dia atual, filtra janelas que ainda não iniciaram
        if day == today:
            df_day = df_day[df_day.apply(lambda row: current_hour < get_start_hour(row), axis=1)].copy()
        
        df_day = df_day[df_day.apply(row_has_valid_availability, axis=1)].copy()
        
        if not df_day.empty:
            df_day["Order"] = df_day.apply(lambda row: get_start_hour(row), axis=1)
            df_day.sort_values(by="Order", inplace=True, na_position="last")
            df_day.drop(columns=["Order"], inplace=True, errors="ignore")
        
        terminal_series = df_day["Terminal"].reset_index(drop=True)
        df_day_display = df_day.drop(columns=["Terminal", "Data"], errors="ignore").reset_index(drop=True)
        
        styled_data = df_day_display.style.apply(
            lambda row: highlight_terminal_mod(row, terminal_series.iloc[row.name]),
            axis=1
        )
        # Aplica o estilo de disponibilidade nos valores numéricos
        styled_data = styled_data.applymap(highlight_availability, subset=["ECH", "EVZ", "RCH", "RVZ", "RCS"])
        
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
# LEGENDA COM ÍCONES
# =============================================================================
legend_html_improved = """
<div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-top: 30px;">
    <h3 style="margin-top: 0; color: #333;">Legenda - Abreviações</h3>
    <div class="icon-container">
        <div class="icon">📥</div><b>ECH</b>: Entrega de cheio
    </div>
    <div class="icon-container">
        <div class="icon">🔄</div><b>EVZ</b>: Entrega de vazio
    </div>
    <div class="icon-container">
        <div class="icon">📤</div><b>RCH</b>: Retirada de cheio
    </div>
    <div class="icon-container">
        <div class="icon">🔃</div><b>RVZ</b>: Retirada de vazio
    </div>
    <div class="icon-container">
        <div class="icon">📦</div><b>RCS</b>: Retirada de carga solta
    </div>
</div>
"""
st.markdown("---")
st.markdown(
    "<b>Legenda - Terminais:</b><br>"
    "<span style='background-color:#00397F; color:white; padding:4px 8px; border-radius:4px;'>Multirio</span>&nbsp;&nbsp;"
    "<span style='background-color:#F37529; color:white; padding:4px 8px; border-radius:4px;'>Rio Brasil Terminal</span>",
    unsafe_allow_html=True
)
st.markdown(legend_html_improved, unsafe_allow_html=True)

# =============================================================================
# HORA DA ÚLTIMA ATUALIZAÇÃO
# =============================================================================
st.markdown(
    f"""
    <div style="text-align: right; font-size: 12px; color: #777; margin-top: 30px;">
        Última atualização: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True,
)
