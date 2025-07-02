# main.py

import time
import streamlit as st
from controller import executarDashboard
from streamlit_autorefresh import st_autorefresh

# Mova st.set_page_config para o início do main.py
st.set_page_config(page_title="Dashboard de Processos", layout="wide", initial_sidebar_state="collapsed")

if __name__ == "__main__":
    # Configura o autorefresh para re-executar o script a cada 5 segundos (5000 ms)
    # Você pode alterar o valor do 'interval' para controlar a frequência
    st_autorefresh(interval=2000, key="dashboard_autorefresh")

    executarDashboard()
    # A linha time.sleep(2) e o while True devem ser removidos,
    # pois o st_autorefresh já cuida da atualização periódica.
    # time.sleep(2) # REMOVA ESTA LINHA