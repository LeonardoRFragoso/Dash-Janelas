import streamlit as st
import datetime
import pandas as pd

from data_loader import load_janelas_multirio_data, load_informacoes_janelas_data
from utils import abbreviate_column, merge_duplicate_columns
from layout import set_page_config, sidebar, header, legend

# -------------------------------------------------------------------
# Função auxiliar para normalizar colunas de data
# -------------------------------------------------------------------
def normalize_date_column(df, possible_names, target_name="Data"):
    for name in possible_names:
        if name in df.columns:
            df[target_name] = pd.to_datetime(df[name], errors="coerce", dayfirst=True).dt.date
            return df
    st.error(f"Nenhuma coluna de data encontrada. Esperava uma das colunas: {possible_names}.")
    st.stop()
    return df

# -------------------------------------------------------------------
# Função auxiliar para normalizar colunas de horário
# -------------------------------------------------------------------
def normalize_time_column(df, possible_names, target_name="Horário"):
    for name in possible_names:
        if name in df.columns:
            df[target_name] = df[name]
            return df
    st.error(f"Nenhuma coluna de horário encontrada. Esperava uma das colunas: {possible_names}.")
    st.stop()
    return df

# -------------------------------------------------------------------
# Configuração da página
# -------------------------------------------------------------------
set_page_config()
sidebar()
header()

# -------------------------------------------------------------------
# Carregamento dos dados
# -------------------------------------------------------------------
try:
    df_multirio = load_janelas_multirio_data()
    df_info = load_informacoes_janelas_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados das planilhas: {e}")
    st.stop()

# -------------------------------------------------------------------
# Limpeza dos nomes das colunas
# -------------------------------------------------------------------
df_multirio.columns = df_multirio.columns.str.strip()
df_info.columns = df_info.columns.str.strip()

# -------------------------------------------------------------------
# Normaliza colunas de data e horário
# -------------------------------------------------------------------
df_multirio = normalize_date_column(df_multirio, ["Data", "DATA", "data"])
df_info = normalize_date_column(df_info, ["DATA", "Data", "data"])

df_multirio = normalize_time_column(df_multirio, ["JANELAS MULTIRIO"], target_name="Horário")
df_info = normalize_time_column(df_info, ["HORA"], target_name="Horário")

# -------------------------------------------------------------------
# Filtragem por datas D, D+1, D+2
# -------------------------------------------------------------------
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
day_after_tomorrow = today + datetime.timedelta(days=2)

df_multirio_today = df_multirio[df_multirio["Data"] == today]
df_multirio_tomorrow = df_multirio[df_multirio["Data"] == tomorrow]
df_multirio_day_after = df_multirio[df_multirio["Data"] == day_after_tomorrow]

df_rio_brasil_today = df_info[df_info["Data"] == today]
df_rio_brasil_tomorrow = df_info[df_info["Data"] == tomorrow]
df_rio_brasil_day_after = df_info[df_info["Data"] == day_after_tomorrow]

# -------------------------------------------------------------------
# Exibição das tabelas
# -------------------------------------------------------------------
st.subheader("Janelas Disponíveis")
dates = [today, tomorrow, day_after_tomorrow]
titles = ["D", "D+1", "D+2"]

cols = st.columns(3)

for i, (date, title) in enumerate(zip(dates, titles)):
    with cols[i]:
        st.markdown(f"### {title}")
        
        if date == today:
            df_concat = pd.concat([df_multirio_today.assign(Terminal="Multirio"), df_rio_brasil_today], ignore_index=True)
        elif date == tomorrow:
            df_concat = pd.concat([df_multirio_tomorrow.assign(Terminal="Multirio"), df_rio_brasil_tomorrow], ignore_index=True)
        else:
            df_concat = pd.concat([df_multirio_day_after.assign(Terminal="Multirio"), df_rio_brasil_day_after], ignore_index=True)

        if df_concat.empty:
            st.write("Nenhuma janela disponível.")
            continue

        # Filtrar apenas janelas disponíveis
        if "STATUS" in df_concat.columns:
            df_concat = df_concat[df_concat["STATUS"] == "DISPONÍVEL"]

        # Ordenar por horário, convertendo para datetime
        if "Horário" in df_concat.columns:
            df_concat["HoraInicial"] = pd.to_datetime(
                df_concat["Horário"].str.split(" - ").str[0],
                format="%H:%M",
                errors="coerce"
            )
            df_concat.sort_values("HoraInicial", inplace=True)
            df_concat.drop(columns=["HoraInicial"], inplace=True)

        # Exibir colunas essenciais
        keep_cols = ["Terminal", "Horário", "DISPONÍVEL", "RESERVADA", "UTILIZADA", "NO SHOW", "CANCELADO", "DESCRICAO", "ENTRADA OU SAÍDA", "AREA", "CARGA", "TIPO DE DOCUMENTO"]
        df_display = df_concat[[c for c in keep_cols if c in df_concat.columns]]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# Exibe a legenda
legend()
