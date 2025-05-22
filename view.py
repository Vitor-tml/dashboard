# view.py (com estilo retrô aprimorado)
import streamlit as st
from streamlit_autorefresh import st_autorefresh

def render_dashboard(data):
    st.set_page_config(
        page_title="Dashboard de Processos",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # --- CSS Retrô Aprimorado ---
    st.markdown("""
        <style>
        /* Fundo e texto base */
        html, body, [class*="css"] {
            background-color: #000000 !important; /* Fundo preto puro */
            color: #00FF00 !important; /* Verde vibrante */
            font-family: "Courier New", monospace; /* Fonte monoespaçada clássica */
            text-shadow: 0 0 5px #00FF00; /* Efeito de brilho */
        }

        /* Efeito de scanlines (linhas de varredura de monitor CRT) */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                repeating-linear-gradient(
                    0deg, 
                    rgba(0, 0, 0, 0.15), 
                    rgba(0, 0, 0, 0.15) 1px, 
                    transparent 1px, 
                    transparent 2px
                );
            pointer-events: none; /* Garante que não interfere com cliques */
            z-index: 9999; /* Garante que as linhas fiquem por cima */
        }
        
        /* Barra de progresso (CPU, Memória) */
        .stProgress > div > div > div > div {
            background-color: #00FF00;
            box-shadow: 0 0 8px #00FF00; /* Mais brilho na barra */
        }
        
        /* Contêiner principal e remoção de margem padrão */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Caixas de estatísticas (CPU, Memória, Processos) */
        .stats-box {
            border: 2px solid #00FF00;
            padding: 15px;
            border-radius: 0px; /* Bordas retas */
            margin-bottom: 20px;
            box-shadow: 0 0 10px #00FF00; /* Efeito de brilho ao redor das caixas */
            background-color: rgba(0, 50, 0, 0.1); /* Um leve fundo verde translúcido */
        }

        /* Títulos */
        h1, h2, h3, h4, h5, h6 {
            color: #00FF00 !important;
            text-shadow: 0 0 8px #00FF00; /* Mais brilho nos títulos */
            border-bottom: 1px dashed #00FF00; /* Linha tracejada abaixo dos títulos */
            padding-bottom: 5px;
            margin-bottom: 15px;
        }

        /* Texto simples */
        p, .stMarkdown {
            color: #00FF00;
            text-shadow: 0 0 3px #00FF00;
        }

        /* Dataframe (Tabela de Processos) */
        .stDataFrame {
            border: 2px solid #00FF00;
            box-shadow: 0 0 10px #00FF00;
            background-color: rgba(0, 50, 0, 0.1); /* Fundo translúcido */
        }

        .stDataFrame table {
            background-color: transparent !important;
            color: #00FF00 !important;
        }

        .stDataFrame th {
            background-color: #008000 !important; /* Cabeçalho verde mais escuro */
            color: #FFFFFF !important; /* Texto branco no cabeçalho */
            text-shadow: 0 0 5px #FFFFFF;
            border-bottom: 2px solid #00FF00 !important;
        }
        
        .stDataFrame td {
            border-color: #00FF00 !important; /* Linhas da tabela */
        }

        /* Linhas separadoras */
        hr {
            border-top: 2px dashed #00FF00;
            margin-top: 20px;
            margin-bottom: 20px;
        }

        /* Rodapé */
        .stCaption {
            color: #008000 !important; /* Verde mais escuro para o rodapé */
            text-shadow: none;
        }
        
        /* Scrollbar styling (Pode não funcionar em todos os navegadores) */
        ::-webkit-scrollbar {
            width: 12px;
            height: 12px;
        }
        ::-webkit-scrollbar-track {
            background: #001a00; /* Fundo do scrollbar */
            border: 1px solid #00FF00;
        }
        ::-webkit-scrollbar-thumb {
            background-color: #00FF00;
            border: 2px solid #008000;
            border-radius: 0px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background-color: #33FF33;
        }

        /* Remover decoração padrão do Streamlit em alguns elementos */
        .stButton>button {
            background-color: #008000;
            color: #FFFFFF;
            border: 2px solid #00FF00;
            box-shadow: 0 0 8px #00FF00;
            border-radius: 0px;
        }
        .css-fg4lnv { /* Classe específica para o menu do Streamlit, pode variar */
            background-color: black !important;
            color: #00FF00 !important;
        }
        .css-1fv8s86 { /* Container principal da app */
            background-color: black !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("DASHBOARD DE PROCESSOS Pedro & Vitor")

    st_autorefresh(interval=2000, key="atualiza")

    # OBTENDO DADOS DO DICIONÁRIO 'data' RECEBIDO DO CONTROLLER
    uso_cpu = data.get('cpu_usage', 0)
    ocioso_cpu = data.get('cpu_idle', 0)
    mem_info = data.get('mem_info', {})
    total_proc = data.get('total_processes', 0)
    total_thr = data.get('total_threads', 0)
    processes_list = data.get('processes_list', [])

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

    processes_list.sort(key=lambda p: p.pid)

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
        "Usuário": p.user_display,
        "Comando": p.commandCMD
    } for p in processes_list]

    st.dataframe(table, use_container_width=True)

    st.write(f"Total de processos exibidos: {len(processes_list)}")

    st.markdown("---") # Linha de separação

    st.caption("Dashboard de Processos - Sistemas Operacionais UTFPR")