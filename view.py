# view.py

import streamlit as st
import pandas as pd
from pathlib import Path
from model import get_process_open_files

def set_style():
    try:
        with open("retro_style.css", "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo 'retro_style.css' não encontrado.")

_memory_history = []
_memory_history_maxlen = 30

def render_dashboard(data):
    st.set_page_config(page_title="Dashboard de Processos", layout="wide", initial_sidebar_state="collapsed")
    set_style()
    st.title("DASHBOARD DE PROCESSOS E SISTEMAS - Pedro & Vitor")

    # O resto do código da view permanece exatamente o mesmo
    tab1, tab2 = st.tabs(["📊 Monitor de Recursos", "🗄️ Sistema de Arquivos"])
    with tab1:
        render_resource_monitor(data)
    with tab2:
        render_filesystem_browser(data)

def render_resource_monitor(data):
    st.header("Visão Geral do Sistema")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        uso_cpu = data.get('cpu_usage', 0)
        st.markdown("### 💻 CPU")
        st.progress(uso_cpu / 100)
        st.write(f"Uso da CPU: **{uso_cpu:.2f}%**")
        cpu_history = data.get('cpu_history', [uso_cpu])
        cpu_df = pd.DataFrame(cpu_history, columns=["Uso da CPU (%)"])
        st.line_chart(cpu_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        mem_info = data.get('mem_info', {})
        mem_usada_percent = mem_info.get('mem_usada_percent', 0)
        mem_usada_mb = mem_info.get('mem_usada', 0) / 1024
        mem_total_mb = mem_info.get('MemTotal', 0) / 1024
        st.markdown("### 🧠 Memória RAM")
        st.progress(mem_usada_percent / 100)
        st.write(f"Usada: **{mem_usada_percent:.2f}%** ({mem_usada_mb:.1f} MB de {mem_total_mb:.1f} MB)")
        global _memory_history
        _memory_history.append({"Usada": mem_usada_percent})
        if len(_memory_history) > _memory_history_maxlen: _memory_history.pop(0)
        mem_hist_df = pd.DataFrame(_memory_history)
        st.line_chart(mem_hist_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("### 📊 Processos e SWAP")
        st.write(f"Total de Processos: **{data.get('total_processes', 0)}**")
        st.write(f"Total de Threads: **{data.get('total_threads', 0)}**")
        swap_usada_mb = mem_info.get('swap_usada', 0) / 1024
        swap_total_mb = mem_info.get('SwapTotal', 0) / 1024
        st.write(f"SWAP Usado: **{swap_usada_mb:.1f} MB** / **{swap_total_mb:.1f} MB**")
        if swap_total_mb > 0:
            st.progress((swap_usada_mb / swap_total_mb))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.header("📋 Lista de Processos")

    processes_list = data.get('processes_list', [])
    processes_list.sort(key=lambda p: p.pid)
    
    table_data = [{
        "PID":          p.pid, "Nome":         p.name, "Status":       p.estado,
        "PPID":         p.ppid, "UID":          p.uid, "Threads":      p.threads,
        "CPU (User)":   p.cpuUserTick, "CPU (Kernel)": p.cpuSysTick, "RAM (KB)":     p.memoriaKB,
        "Usuário":      p.user_display, "Comando":      p.commandCMD
    } for p in processes_list]

    st.dataframe(table_data, use_container_width=True)
    st.markdown("---")
    st.header("🔍 Inspecionar Processo e Recursos de E/S")

    process_options = [f"PID: {p.pid} - Nome: {p.name}" for p in processes_list]
    
    st.selectbox(
        "Selecione um processo para ver os detalhes:",
        options=["Nenhum"] + process_options,
        key='selected_process_option'
    )

    if st.session_state.selected_process_option != "Nenhum":
        selected_pid = int(st.session_state.selected_process_option.split(" ")[1])
        selected_process = next((p for p in processes_list if p.pid == selected_pid), None)
        if selected_process:
            st.markdown(f"#### Detalhes do PID: {selected_process.pid}")
            st.code(f"""
Nome         : {selected_process.name}
Comando      : {selected_process.commandCMD}
Status       : {selected_process.estado}
PPID         : {selected_process.ppid}
Threads      : {selected_process.threads}
Uso de RAM   : {selected_process.memoriaKB} KB
            """)
            if st.button("Ver Arquivos e Sockets Abertos", key=f"btn_details_{selected_pid}"):
                with st.spinner("Buscando recursos..."):
                    open_files = get_process_open_files(selected_pid)
                    st.markdown("##### Descritores de Arquivos Abertos:")
                    st.code('\n'.join(open_files))

def render_filesystem_browser(data):
    st.header("Sistema de Arquivos")
    st.subheader("Discos e Pontos de Montagem")
    partitions = data.get("partitions", [])
    if not partitions:
        st.warning("Não foi possível carregar as informações das partições.")
    else:
        st.dataframe(partitions, use_container_width=True)
    st.markdown("---")
    st.subheader("Navegador de Diretórios")

    if 'current_path' not in st.session_state:
        st.session_state.current_path = "/"
    path_str = st.text_input("Caminho Atual", st.session_state.current_path)
    current_path = Path(path_str)

    if current_path.is_dir():
        st.session_state.current_path = str(current_path.resolve())
        if current_path.parent != current_path:
            if st.button("⬆️ Subir para o diretório pai"):
                st.rerun()
        try:
            items_list = []
            for item in sorted(current_path.iterdir(), key=lambda f: f.name.lower()):
                if item.is_dir():
                    if st.button(f"📁 {item.name}", key=f"dir_{item.name}"):
                        st.session_state.current_path = str(item.resolve())
                        st.rerun()
                elif item.is_file():
                    try:
                        size_kb = item.stat().st_size / 1024
                        items_list.append(f"📄 {item.name:<50} {size_kb:8.2f} KB")
                    except FileNotFoundError:
                        items_list.append(f"📄 {item.name} (arquivo movido)")
            if items_list:
                st.markdown("##### Arquivos no diretório:")
                st.code("\n".join(items_list))
        except PermissionError:
            st.error(f"Permissão negada para acessar o diretório: {current_path}")
        except Exception as e:
            st.error(f"Erro ao listar diretório: {e}")
    else:
        st.error("O caminho inserido não é um diretório válido.")