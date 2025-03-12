# layout.py

import streamlit as st
from config import LOGO_PATH

def set_page_config():
    st.set_page_config(page_title="Dashboard de Janelas", layout="wide")

def sidebar():
    with st.sidebar:
        st.image(LOGO_PATH, width=250)
        st.title("Dashboard de Janelas")
        st.markdown("**Torre de Controle - Dashboard de Janelas no Porto**")

def header():
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
        """
        <div class="titulo-dashboard-container">
            <h1 class="titulo-dashboard">Torre de Controle Itracker - Dashboard de Janelas</h1>
            <p class="subtitulo-dashboard">Monitorando em tempo real as operações das janelas no Porto</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

def legend():
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
