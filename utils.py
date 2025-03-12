# utils.py

import pandas as pd

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

def row_has_valid_availability(row: pd.Series, disp_cols: list) -> bool:
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
    return ["" for _ in row]
