# controller.py

from model import SystemMonitorConsoleModel 
from view import render_dashboard
import streamlit as st

st.set_page_config(page_title="Dashboard de Processos", layout="wide", initial_sidebar_state="collapsed")

# Instancia o modelo uma única vez no início
monitor_model = SystemMonitorConsoleModel()

def executarDashboard():
    """
    Função principal que o Streamlit irá chamar.
    Busca os dados principais do modelo e passa para a view.
    """
    # 1. O Controller pede os dados completos ao Modelo
    dashboard_data = monitor_model.get_all_data()

    # 2. O Controller passa os dados para a função da View para renderizar
    render_dashboard(dashboard_data)