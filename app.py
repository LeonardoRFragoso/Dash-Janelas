import streamlit as st
import io
import json
import pandas as pd
import datetime
import unidecode  # <--- IMPORTANTE: para remover acentos
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
        "ENTREGA CHEIO Disp.": "ECH",
        "ENTREGA VAZIO Disp.": "EVZ",
        "RETIRADA CHEIO Disp.": "RCH",
        "RETIRADA VAZIO Disp.": "RVZ",
        "RETIRADA CARGA SOLTA Disp.": "RCS"
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
# Função para normalizar texto do "Tipo"
# e identificar se é importação ou exportação
# ======================================================
def parse_import_export(tipo_str: str) -> str:
    """
    Recebe o valor original da coluna "Tipo" e tenta identificar
    se é importação ou exportação. Trata acentos e possíveis abreviações.
    Retorna "importacao", "exportacao" ou "desconhecido".
    """
    # Remove acentos, converte para minúsculas
    tipo_limpo = unidecode.unidecode(str(tipo_str)).strip().lower()
    
    # Se contiver "import" ou "imp", consideramos importação
    if ("import" in tipo_limpo) or ("imp" in tipo_limpo):
        return "importacao"
    # Se contiver "export" ou "exp", consideramos exportação
    elif ("export" in tipo_limpo) or ("exp" in tipo_limpo):
        return "exportacao"
    else:
        return "desconhecido"

# ======================================================
# Processamento dos Dados
# ======================================================

try:
    df_multirio = load_janelas_multirio_data()
    df_info = load_informacoes_janelas_data()
    # Remover as linhas de df_info que não possuem dados essenciais
    df_info = df_info.dropna(subset=["Dia", "Hora Inicial", "Hora Final", "Qtd Veículos Reservados", "Tipo"])
except Exception as e:
    st.error(f"Erro ao carregar os dados das planilhas: {e}")
    st.stop()

# --- Processamento dos dados para cada empresa ---

# Para Multirio: utilizar apenas as colunas com as nomenclaturas mapeadas
mapping_keys = ["ENTREGA CHEIO Disp.", "ENTREGA VAZIO Disp.",
                "RETIRADA CHEIO Disp.", "RETIRADA VAZIO Disp.", "RETIRADA CARGA SOLTA Disp."]
disp_cols = [col for col in df_multirio.columns if col in mapping_keys]
if not disp_cols:
    st.error("Nenhuma coluna de disponibilidade encontrada na planilha do Multirio.")
    st.stop()

cols_multirio = ["Data", "JANELAS MULTIRIO"] + disp_cols
df_multirio_unified = df_multirio[cols_multirio].copy()
df_multirio_unified.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
df_multirio_unified["Terminal"] = "Multirio"

# Para Rio Brasil Terminal:
required_cols = {"Dia", "Hora Inicial", "Hora Final", "Qtd Veículos Reservados", "Tipo"}
if not required_cols.issubset(df_info.columns):
    st.error("Colunas necessárias não encontradas na planilha de informações.")
    st.stop()

df_info_renamed = df_info.rename(columns={"Dia": "Data"})
df_info_renamed["Horário"] = df_info_renamed["Hora Inicial"].astype(str) + " - " + df_info_renamed["Hora Final"].astype(str)

# Converter "Qtd Veículos Reservados" para numérico (garante que valores em branco sejam 0)
df_info_renamed["Qtd Veículos Reservados"] = pd.to_numeric(
    df_info_renamed["Qtd Veículos Reservados"], errors="coerce"
).fillna(0)

# Aplica a função de parse para detectar import/export
df_info_renamed["Tipo_Limpo"] = df_info_renamed["Tipo"].apply(parse_import_export)

# Preenche ECH e RCH de acordo com a detecção
df_info_renamed["ECH"] = df_info_renamed.apply(
    lambda row: float(row["Qtd Veículos Reservados"]) if row["Tipo_Limpo"] == "exportacao" else 0,
    axis=1
)
df_info_renamed["RCH"] = df_info_renamed.apply(
    lambda row: float(row["Qtd Veículos Reservados"]) if row["Tipo_Limpo"] == "importacao" else 0,
    axis=1
)

# Preencher as demais colunas com 0 para manter a estrutura unificada
for col in ["EVZ", "RVZ", "RCS"]:
    df_info_renamed[col] = 0

df_info_unified = df_info_renamed[["Data", "Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"]].copy()
df_info_unified["Terminal"] = "Rio Brasil Terminal"

# Unificar os dados
df_unified = pd.concat([df_multirio_unified, df_info_unified], ignore_index=True)

# Converter Data para datetime (dia/mês/ano) e ordenar
df_unified["Data"] = pd.to_datetime(df_unified["Data"], errors="coerce", dayfirst=True).dt.date
df_unified.sort_values(by=["Data", "Horário"], inplace=True)

# ======================================================
# Função para filtrar linhas com dados válidos conforme o terminal
# ======================================================

def row_has_valid_availability(row):
    # Para Rio Brasil Terminal: válida se ECH ou RCH for diferente de 0
    if row["Terminal"] == "Rio Brasil Terminal":
        try:
            val_ech = float(row.get("ECH", 0)) if row.get("ECH", 0) not in [None, "", "NaN"] else 0
            val_rch = float(row.get("RCH", 0)) if row.get("RCH", 0) not in [None, "", "NaN"] else 0
            return (val_ech != 0 or val_rch != 0)
        except:
            # Se houver qualquer erro de conversão, não filtra a linha
            return True
    # Para Multirio: válida se alguma das colunas de disponibilidade tiver valor numérico diferente de 0
    elif row["Terminal"] == "Multirio":
        for col in disp_cols:
            try:
                val = float(row.get(col, 0)) if row.get(col, 0) not in [None, "", "NaN"] else 0
                if val != 0:
                    return True
            except:
                # Se erro, ignora e segue
                continue
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
    df_today['StartHour'] = (
        df_today['Horário']
        .str.split(" - ")
        .str[0]
        .str.extract(r'(\d{1,2})')[0]
        .astype(float, errors='ignore')  # se der erro, vira NaN
    )
    df_next = df_today[df_today['StartHour'] >= current_hour].sort_values(by='StartHour', na_position='last')
    if not df_next.empty:
        next_window = df_next.iloc[0]
        if next_window['Terminal'] == "Rio Brasil Terminal":
            availability_str = f"ECH: {next_window.get('ECH', 0)}, RCH: {next_window.get('RCH', 0)}"
        elif next_window['Terminal'] == "Multirio":
            avail_list = []
            for col in disp_cols:
                abbr = abbreviate_column(col)
                avail_list.append(f"{abbr}: {next_window.get(col, 0)}")
            availability_str = ", ".join(avail_list)
        else:
            availability_str = "N/A"
        st.info(
            f"Próxima janela disponível: {next_window['Horário']} - Terminal: {next_window['Terminal']}.\n"
            f"Disponibilidade nesta janela: {availability_str}"
        )
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
        
        # Filtrar linhas com disponibilidade válida
        df_data = df_data[df_data.apply(row_has_valid_availability, axis=1)]
        
        numeric_cols = df_data.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            # Filtra linhas cujo somatório é 0, se quiser realmente ocultar as que não têm nada
            df_data = df_data[df_data[numeric_cols].fillna(0).sum(axis=1) != 0]
        
        # Se for o dia atual, filtrar apenas janelas futuras
        if data == today and 'Horário' in df_data.columns:
            try:
                df_data['StartHour'] = (
                    df_data['Horário']
                    .str.split(" - ")
                    .str[0]
                    .str.extract(r'(\d{1,2})')[0]
                    .astype(float, errors='ignore')
                )
                df_data = df_data[df_data['StartHour'] >= current_hour]
                df_data.drop(columns=['StartHour'], inplace=True, errors='ignore')
            except Exception as e:
                st.error(f"Erro ao filtrar horários do dia atual: {e}")
        
        # Obter a informação do terminal antes de descartar a coluna
        if "Terminal" in df_data.columns:
            terminal_aux = df_data["Terminal"].copy()
        else:
            terminal_aux = pd.Series([""] * len(df_data), index=df_data.index)
        
        # Abreviar os nomes das colunas e filtrar para manter apenas as colunas desejadas:
        df_data = df_data.rename(columns=lambda col: abbreviate_column(col))
        cols_to_keep = [col for col in df_data.columns if col in ["Horário", "ECH", "EVZ", "RCH", "RVZ", "RCS"]]
        df_data = df_data[cols_to_keep]
        
        # Garantir que os índices e as colunas sejam únicos:
        df_data = df_data.reset_index(drop=True)
        df_data = df_data.loc[:, ~df_data.columns.duplicated()]
        terminal_aux = terminal_aux.reset_index(drop=True)
        
        with cols_display[i]:
            title = table_titles[i]
            st.markdown(f"<h3 style='text-align: center; color: black;'>{title}</h3>", unsafe_allow_html=True)
            
            if df_data.empty:
                st.write("Sem dados para exibição")
            else:
                styled_data = df_data.style.apply(lambda row: highlight_terminal_mod(row, terminal_aux), axis=1)
                # Formatação para colunas numéricas
                num_cols = df_data.select_dtypes(include=['number']).columns
                if not num_cols.empty:
                    styled_data = styled_data.format("{:.0f}", subset=num_cols)
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
