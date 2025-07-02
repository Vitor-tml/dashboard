# main.py

import time
from controller import executarDashboard
import streamlit as st

if __name__ == "__main__":
    while True:
        executarDashboard()
        time.sleep(2)
        # st.rerun() # Esta linha deve ser removida 