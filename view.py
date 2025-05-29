import streamlit as st
from streamlit_autorefresh import st_autorefresh # Mantido para compatibilidade, mas Streamlit já tem auto-refresh
import pandas as pd

# Função para aplicar o estilo CSS
def set_style():
    with open("retro_style.css", "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

_memory_history = []
_memory_history_maxlen = 30 # Mesmo tamanho do histórico da CPU para consistência

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
    # Streamlit já lida com auto-refresh se os dados do backend mudam,
    # então st_autorefresh não é estritamente necessário aqui, mas pode ser útil para forçar.
    st_autorefresh(interval=2000, key="atualiza_frontend")

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

    # Coleta de dados de memória para o histórico
    mem_usada_percent = mem_info.get('mem_usada_percent', 0)
    mem_livre_percent = mem_info.get('mem_livre_percent', 0)
    
    global _memory_history
    _memory_history.append({"Usada": mem_usada_percent, "Livre": mem_livre_percent})
    if len(_memory_history) > _memory_history_maxlen:
        _memory_history.pop(0)

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
        st.markdown("#### Histórico de Uso da CPU (%)")
        st.line_chart(cpu_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("### 🧠 Memória RAM")
        mem_usada_mb = mem_info.get('mem_usada', 0) / 1024
        mem_total_mb = mem_info.get('MemTotal', 0) / 1024

        st.progress(mem_usada_percent/100)
        st.write(f"Usada: **{mem_usada_percent:.2f}%** ({mem_usada_mb:.1f} MB)")
        st.write(f"Livre: **{mem_livre_percent:.2f}%**")
        st.write(f"Total: **{mem_total_mb:.1f} MB**")
        
        # --- NOVO GRÁFICO DE MEMÓRIA DE LINHAS ---
        st.markdown("#### Histórico de Uso de Memória RAM (%)")
        mem_hist_df = pd.DataFrame(_memory_history)
        st.line_chart(mem_hist_df, use_container_width=True)
        # --- FIM NOVO GRÁFICO ---

        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("### 📊 Processos e SWAP")
        swap_usada_mb = mem_info.get('swap_usada', 0) / 1024
        swap_total_mb = mem_info.get('SwapTotal', 0) / 1024
        
        st.write(f"Total de Processos: **{total_proc}**")
        st.write(f"Total de Threads: **{total_thr}**")
        st.write(f"SWAP Usado: **{swap_usada_mb:.1f} MB** / **{swap_total_mb:.1f} MB**")
        
        # Gráfico de uso de SWAP
        if swap_total_mb > 0:
            swap_usada_percent = (swap_usada_mb / swap_total_mb) * 100
            swap_livre_percent = 100 - swap_usada_percent
            st.markdown("#### Uso de SWAP (%)")
            swap_chart_data = pd.DataFrame({
                'Tipo': ['Usada', 'Livre'],
                'Porcentagem': [swap_usada_percent, swap_livre_percent]
            })
            st.bar_chart(swap_chart_data.set_index('Tipo'), use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---") # Linha de separação

    st.markdown("### 📋 Lista de Processos")
    table = [{
        "PID":          p.pid,
        "Nome":         p.name,
        "Status":       p.estado,
        "PPID":         p.ppid,
        "UID":          p.uid,
        "Threads":      p.threads,
        "CPU (User)":   p.cpuUserTick,
        "CPU (Kernel)": p.cpuSysTick,
        "RAM (KB)":     p.memoriaKB,
        "Usuário":      p.user_display,
        "Comando":      p.commandCMD
    } for p in processes_list]

    st.dataframe(table, use_container_width=True)

    st.write(f"Total de processos exibidos: {len(processes_list)}")

    st.markdown("---") # Linha de separação

    st.caption("Dashboard de Processos - Sistemas Operacionais UTFPR")