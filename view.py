# view.py

import streamlit as st
import pandas as pd
from pathlib import Path
from model import get_process_open_files
from model import get_process_resources
import altair as alt
from datetime import datetime

_swap_history = []
_swap_history_maxlen = 30

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
    # st.set_page_config(page_title="Dashboard de Processos", layout="wide", initial_sidebar_state="collapsed")
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
        # st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        uso_cpu = data.get('cpu_usage', 0)
        st.markdown("### 💻 CPU")
        # st.progress(uso_cpu / 100)
        st.write(f"Uso da CPU: **{uso_cpu:.2f}%**")
        cpu_history = data.get('cpu_history', [uso_cpu])
        cpu_df = pd.DataFrame(cpu_history, columns=["Uso da CPU (%)"])

        # Antigo gráfico
        # st.line_chart(cpu_df, use_container_width=True)

        ###########################################################################

        cpu_df = pd.DataFrame(cpu_history, columns=["Uso da CPU (%)"])
        cpu_df["Tempo"] = list(range(len(cpu_df)))  # eixo X fictício

        line_chart = alt.Chart(cpu_df).mark_line(
            color="#00FF00",
            strokeWidth=2
        ).encode(
            x=alt.X("Tempo", axis=None),
            y=alt.Y("Uso da CPU (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=["Tempo", "Uso da CPU (%)"]
        ).properties(
            width="container",
            height=200,
            background="#000000"
        ).configure_axis(
            grid=True,
            gridColor="#004400",
            gridOpacity=0.3
        ).configure_view(
            stroke=None
        )

        st.altair_chart(line_chart, use_container_width=True)

        ###########################################################################
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        # st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        mem_info = data.get('mem_info', {})
        mem_usada_percent = mem_info.get('mem_usada_percent', 0)
        mem_usada_mb = mem_info.get('mem_usada', 0) / 1024
        mem_total_mb = mem_info.get('MemTotal', 0) / 1024
        st.markdown("### 🧠 Memória RAM")
        # st.progress(mem_usada_percent / 100)
        st.write(f"Usada: **{mem_usada_percent:.2f}%** ({mem_usada_mb:.1f} MB de {mem_total_mb:.1f} MB)")
        global _memory_history
        _memory_history.append({"Usada": mem_usada_percent})
        if len(_memory_history) > _memory_history_maxlen: _memory_history.pop(0)
        mem_hist_df = pd.DataFrame(_memory_history)
        # st.line_chart(mem_hist_df, use_container_width=True)
        # Gráfico retrô de memória RAM
        mem_df = mem_hist_df
        mem_df["Tempo"] = range(len(mem_df))
        mem_chart = alt.Chart(mem_df).mark_line(
            color="#00FFFF",  # Azul neon
            strokeWidth=2
        ).encode(
            x=alt.X("Tempo", axis=alt.Axis(title="", labelColor="#00FF00", tickColor="#004400", gridColor="#004400")),
            y=alt.Y("Usada", axis=alt.Axis(title="Memória (%)", labelColor="#00FF00", tickColor="#004400", gridColor="#004400"))
        ).properties(
            height=200,
            width=500,
            background="#000000"
        ).configure_view(
            stroke=None
        ).configure_axis(
            grid=True,
            gridColor="#004400",
            domain=False
        )

        st.altair_chart(mem_chart, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown("### 📊 Processos e SWAP")

        swap_total_mb = mem_info.get('SwapTotal', 0) / 1024
        swap_usada_mb = mem_info.get('swap_usada', 0) / 1024
        swap_usada_percent = (swap_usada_mb / swap_total_mb * 100) if swap_total_mb > 0 else 0

        st.write(f"SWAP Usado: **{swap_usada_mb:.1f} MB** / **{swap_total_mb:.1f} MB**")

        # Atualiza histórico de uso de SWAP
        global _swap_history
        if 'swap_usada_percent' not in locals():
            swap_usada_percent = 0
        _swap_history.append({"SWAP": swap_usada_percent})
        if len(_swap_history) > _swap_history_maxlen:
            _swap_history.pop(0)
        swap_df = pd.DataFrame(_swap_history)
        swap_df["index"] = range(len(swap_df))

        # Gráfico com Altair no estilo retrô
        swap_chart = alt.Chart(swap_df).mark_line(
            color="#FF00FF",  # Magenta neon
            strokeWidth=2
        ).encode(
            x=alt.X("index", axis=alt.Axis(title="", labelColor="#00FF00", tickColor="#004400", gridColor="#004400")),
            y=alt.Y("SWAP", axis=alt.Axis(title="SWAP (%)", labelColor="#00FF00", tickColor="#004400", gridColor="#004400"))
        ).properties(
            height=200,
            width=500,
            background="#000000"
        ).configure_view(
            stroke=None
        ).configure_axis(
            grid=True,
            gridColor="#004400",
            domain=False
        )

        st.altair_chart(swap_chart, use_container_width=True)
        

    st.markdown("---")
    st.header("📋 Lista de Processos")
    st.write(f"Total de Processos: **{data.get('total_processes', 0)}**")
    st.write(f"Total de Threads: **{data.get('total_threads', 0)}**")

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
            if st.button("Ver Recursos Abertos e Locks", key=f"btn_details_{selected_pid}"):
                st.session_state["processo_expandido"] = selected_pid

            # Se o PID ainda estiver salvo, renderiza
            if st.session_state.get("processo_expandido") == selected_pid:
                with st.spinner("Coletando recursos..."):
                    recursos = get_process_resources(selected_pid)

                    if not any(recursos.values()):
                        st.warning("Este processo não possui recursos acessíveis ou você não tem permissão para inspecioná-los.")
                    else:
                        for categoria, lista in recursos.items():
                            if lista:
                                with st.expander(f"🔹 {categoria} ({len(lista)})", expanded=False):
                                    st.code("\n".join(lista))

def render_filesystem_browser(data):
    st.header("🗄️ Sistema de Arquivos")
    st.subheader("Discos e Pontos de Montagem")
    
    partitions = data.get("partitions", [])
    if not partitions:
        st.warning("Não foi possível carregar as informações das partições.")
    else:
        st.dataframe(partitions, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Navegador de Diretórios")

    # Inicializa o caminho atual no session_state como o diretório raiz
    if 'current_path_fs_pathlib' not in st.session_state:
        # Define o caminho inicial como a raiz do sistema de arquivos
        st.session_state.current_path_fs_pathlib = Path('/')

    current_path = st.session_state.current_path_fs_pathlib

    st.markdown(f"**📍 Caminho Atual:** `{current_path}`")

    # Botão para subir de nível (apenas se não estiver na raiz)
    if current_path != Path('/'):
        if st.button("⬆️ Subir um nível"):
            st.session_state.current_path_fs_pathlib = current_path.parent
            st.rerun()

    # Tenta listar o conteúdo do diretório atual
    if current_path.is_dir():
        try:
            dirs_info = []
            files_info = []
            
            for item in sorted(list(current_path.iterdir()), key=lambda x: x.name.lower()):
                try:
                    if not item.exists():
                        continue

                    if item.is_dir():
                        dirs_info.append({"Nome": item.name + "/", "Path": item.resolve()}) # Armazenar o caminho completo
                    elif item.is_file():
                        stat = item.stat()
                        size_kb = stat.st_size / 1024
                        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        
                        files_info.append({
                            "Nome": item.name,
                            "Tipo": "📄 Arquivo",
                            "Tamanho (KB)": f"{size_kb:.1f}",
                            "Modificação": mod_time
                        })
                except PermissionError:
                    if item.is_dir():
                        dirs_info.append({"Nome": item.name + "/ (Sem Permissão)", "Path": None})
                    else:
                        files_info.append({"Nome": item.name + " (Sem Permissão)", "Tipo": "📄 Arquivo", "Tamanho (KB)": "", "Modificação": ""})
                except Exception as e:
                    st.warning(f"Erro ao processar '{item.name}': {e}")
                    continue

            # Exibe os diretórios como botões clicáveis
            if dirs_info:
                st.subheader("Pastas")
                for dir_item in dirs_info:
                    dir_name = dir_item["Nome"]
                    dir_path = dir_item["Path"]
                    if dir_path: # Apenas cria o botão se o caminho for acessível
                        if st.button(f"📁 {dir_name}", key=f"dir_{dir_path}"):
                            st.session_state.current_path_fs_pathlib = dir_path
                            st.rerun()
                    else:
                        st.markdown(f"📁 {dir_name}") # Apenas exibe o nome se não for acessível
            else:
                st.info("Nenhuma subpasta encontrada neste caminho.")

            # Exibe os arquivos em uma tabela (sem alteração)
            if files_info:
                st.subheader("Arquivos")
                files_df = pd.DataFrame(files_info)
                st.dataframe(files_df, use_container_width=True)
            else:
                st.info("Nenhum arquivo encontrado neste caminho.")

        except PermissionError:
            st.error(f"Permissão negada para acessar o diretório: {current_path}. Tente um caminho diferente.")
        except Exception as e:
            st.error(f"Erro inesperado ao listar o diretório: {e}")
    else:
        st.error("O caminho atual não é um diretório válido ou acessível.")