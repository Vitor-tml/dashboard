import streamlit as st
from model import listaProcessos, uso_cpu_percent, info_memoria, total_processos_threads
from streamlit_autorefresh import st_autorefresh

# Configurações da página
st.set_page_config(
    page_title="Dashboard de Processos",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS retrô
st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: black !important;
        color: #00FF00 !important;
        font-family: "Courier New", monospace;
    }
    .stProgress > div > div > div > div {
        background-color: #00FF00;
    }
    .block-container {
        padding-top: 1rem;
    }
    .stats-box {
        border: 2px solid #00FF00;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("DASHBOARD DE PROCESSOS Pedro & Vitor")

# ⏱Atualiza a cada 2 segundos
st_autorefresh(interval=2000, key="atualiza")

# Obter informações globais do sistema
uso_cpu, ocioso_cpu = uso_cpu_percent()
mem_info = info_memoria()
total_proc, total_thr = total_processos_threads()

# Layout em colunas para estatísticas do sistema
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="stats-box">', unsafe_allow_html=True)
    st.markdown("### 💻 CPU")
    st.progress(uso_cpu/100)
    st.write(f"Uso da CPU: **{uso_cpu:.2f}%**")
    st.write(f"CPU Ociosa: **{ocioso_cpu:.2f}%**")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="stats-box">', unsafe_allow_html=True)
    st.markdown("### 🧠 Memória")
    st.progress(mem_info['mem_usada_percent']/100)
    st.write(f"Memória Usada: **{mem_info['mem_usada_percent']:.2f}%** ({mem_info['mem_usada']/1024:.1f} MB)")
    st.write(f"Memória Livre: **{mem_info['mem_livre_percent']:.2f}%**")
    st.write(f"Total RAM: **{mem_info['mem_total']/1024:.1f} MB**")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="stats-box">', unsafe_allow_html=True)
    st.markdown("### 📊 Processos")
    st.write(f"Total de Processos: **{total_proc}**")
    st.write(f"Total de Threads: **{total_thr}**")
    st.write(f"SWAP Usado: **{mem_info['swap_usada']/1024:.1f} MB** / **{mem_info['swap_total']/1024:.1f} MB**")
    st.markdown('</div>', unsafe_allow_html=True)

# Adicionar uma linha de separação
st.markdown("---")

# Título da seção de processos
st.markdown("### 📋 Lista de Processos")

# Lista de processos
processes = listaProcessos()
processes.sort(key=lambda p: p.pid)

# Tabela formatada
table = [{
    "PID": p.pid,
    "Nome": p.name,
    "Status": p.estado,
    "PPID": p.ppid,
    "UID": p.uid,
    "Threads": p.threads,
    "CPU (user)": p.cpuUserTick,
    "CPU (kernel)": p.cpuSysTick,
    "RAM (KB)": p.memoriaKB,
    "Usuário": p.user,
    "Comando": p.commandCMD
} for p in processes]

st.dataframe(table, use_container_width=True)

# Adicionar contador de processos
st.write(f"Total de processos exibidos: {len(processes)}")

# Adicionar rodapé
st.markdown("---")
st.caption("Dashboard de Processos - Sistemas Operacionais UTFPR")