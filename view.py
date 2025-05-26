# view.py (com estilo retrô aprimorado)
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# Função para aplicar o estilo CSS
# O CSS deve ser salvo em um arquivo chamado "retro_style.css" no mesmo diretório
def set_style():
    with open("retro_style.css", "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_dashboard(data):
    # Configurações da página
    st.set_page_config(
        page_title="Dashboard de Processos",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # APLICANDO O CSS
    set_style()
    st.title("DASHBOARD DE PROCESSOS Pedro & Vitor")
    st_autorefresh(interval=2000, key="atualiza")

    # Lógica da View
    # OBTENDO DADOS DO DICIONÁRIO 'data' RECEBIDO DO CONTROLLER
    uso_cpu    = data.get('cpu_usage', 0)
    ocioso_cpu = data.get('cpu_idle', 0)
    mem_info   = data.get('mem_info', {})
    total_proc = data.get('total_processes', 0)
    total_thr  = data.get('total_threads', 0)

    # Recebe e ordena a lista de processos
    processes_list = data.get('processes_list', [])
    processes_list.sort(key=lambda p: p.pid)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("### 💻 CPU")
        st.progress(uso_cpu/100)
        st.write(f"Uso da CPU: **{uso_cpu:.2f}%**")
        st.write(f"CPU Ociosa: **{ocioso_cpu:.2f}%**")
        # Gráfico de uso de CPU com legenda
        cpu_history = data.get('cpu_history', [uso_cpu])
        cpu_df = pd.DataFrame(cpu_history, columns=["Uso da CPU (%)"])
        st.markdown("#### Gráfico de Uso da CPU (%)")  # Legenda/título acima do gráfico
        st.line_chart(cpu_df)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("### 🧠 Memória")
        mem_usada_percent = mem_info.get('mem_usada_percent', 0)
        mem_usada_mb = mem_info.get('mem_usada', 0) / 1024
        mem_livre_percent = mem_info.get('mem_livre_percent', 0)
        mem_total_mb = mem_info.get('mem_total', 0) / 1024

        st.progress(mem_usada_percent/100)
        st.write(f"Memória Usada: **{mem_usada_percent:.2f}%** ({mem_usada_mb:.1f} MB)")
        st.write(f"Memória Livre: **{mem_livre_percent:.2f}%**")
        st.write(f"Total RAM: **{mem_total_mb:.1f} MB**")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("### 📊 Processos")
        swap_usada_mb = mem_info.get('swap_usada', 0) / 1024
        swap_total_mb = mem_info.get('swap_total', 0) / 1024
        
        st.write(f"Total de Processos: **{total_proc}**")
        st.write(f"Total de Threads: **{total_thr}**")
        st.write(f"SWAP Usado: **{swap_usada_mb:.1f} MB** / **{swap_total_mb:.1f} MB**")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---") # Linha de separação

    st.markdown("### 📋 Lista de Processos")
    table = [{
        "PID":      p.pid,
        "Nome":     p.name,
        "Status":   p.estado,
        "PPID":     p.ppid,
        "UID":      p.uid,
        "Threads":  p.threads,
        "CPU (user)":   p.cpuUserTick,
        "CPU (kernel)": p.cpuSysTick,
        "RAM (KB)": p.memoriaKB,
        "Usuário":  p.user_display,
        "Comando":  p.commandCMD
    } for p in processes_list]

    st.dataframe(table, use_container_width=True)

    st.write(f"Total de processos exibidos: {len(processes_list)}")

    st.markdown("---") # Linha de separação

    st.caption("Dashboard de Processos - Sistemas Operacionais UTFPR")