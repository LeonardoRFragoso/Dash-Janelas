import io
import json
import pandas as pd  # 🔹 Adicione esta linha
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from config import CREDENTIALS_PATH, MULTIRIO_FILE_ID, INFO_FILE_ID


def load_spreadsheet(file_id: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    Faz o download de um arquivo do Google Drive (Google Sheets ou Excel)
    e retorna um DataFrame.
    """
    with open(CREDENTIALS_PATH, 'r') as f:
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
    
    # ✅ Tenta carregar o DataFrame
    try:
        df = pd.read_excel(fh, sheet_name=sheet_name)
        if df.empty:
            raise ValueError("Erro: Planilha vazia ou aba não encontrada!")
    except Exception as e:
        raise ValueError(f"Erro ao carregar planilha: {e}")
    
    # ✅ Remover espaços em branco dos nomes das colunas
    df.columns = df.columns.str.strip()
    
    # ✅ Exibe as colunas carregadas para depuração
    print(f"Colunas carregadas: {df.columns.tolist()}")
    
    return df


def load_janelas_multirio_data() -> pd.DataFrame:
    """
    Carrega a planilha do Multirio (Google Sheets) via file_id.
    """
    df = load_spreadsheet(MULTIRIO_FILE_ID)
    
    # 🔹 Ajuste de nomes de colunas para garantir compatibilidade
    df.rename(columns={"JANELAS MULTIRIO": "Horário"}, inplace=True)
    
    # 🔹 Converter Data para formato datetime
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True).dt.date
    
    return df


def load_informacoes_janelas_data() -> pd.DataFrame:
    """
    Carrega a planilha do Rio Brasil Terminal (Google Sheets) via file_id.
    """
    df = load_spreadsheet(INFO_FILE_ID)
    
    # 🔹 Garantir que os nomes das colunas não tenham espaços extras
    df.columns = df.columns.str.strip()
    
    # 🔹 Verificar se a coluna "DATA" existe
    if "DATA" not in df.columns:
        raise KeyError(f"Erro: Coluna 'DATA' não encontrada! Colunas disponíveis: {df.columns.tolist()}")
    
    # 🔹 Renomear colunas para manter consistência no código
    df.rename(columns={"DATA": "Data", "HORA": "Horário"}, inplace=True)
    
    # 🔹 Converter Data para formato datetime
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True).dt.date
    
    return df