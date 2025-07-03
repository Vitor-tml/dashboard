from pathlib import Path
import time
import threading
import json
import subprocess

# --- CLASSE Processo ---
class Processo:
    """
    Representa um processo individual do sistema, coletando informações detalhadas
    a partir do sistema de arquivos virtual /proc do Linux.
    """
    def __init__(self, pid):
        """
        Inicializa uma nova instância de Processo.
        """
        self.pid = pid
        self.ppid = 0
        self.name = ''
        self.estado = ''
        self.uid = 0
        self.cpuUserTick = 0
        self.cpuSysTick = 0
        self.threads = 0
        self.commandCMD = ''
        self.memoriaKB = 0
        self.user_display = ''

    def cmdLine(self):
        """
        Lê a linha de comando completa utilizada para iniciar o processo.
        """
        try:
            cmd_path = f'/proc/{self.pid}/cmdline'
            with open(cmd_path, 'r') as f:
                conteudo = f.read()
                self.commandCMD = conteudo.replace('\x00', ' ').strip()
                if not self.commandCMD:
                    self.commandCMD = '[sem comando]'
        except FileNotFoundError:
            self.commandCMD = 'NO COMMAND (Processo encerrado)'
        except Exception as e:
            self.commandCMD = f'ERRO: {e}'

    def tempoDeCPU(self):
        """
        Lê os ticks de CPU gastos pelo processo.
        """
        path_cpu = f'/proc/{self.pid}/stat'
        try:
            with open(path_cpu, 'r') as f:
                valores = f.read().split()
                if len(valores) > 14:
                    self.cpuUserTick = int(valores[13])
                    self.cpuSysTick = int(valores[14])
                else:
                    self.cpuUserTick = 0
                    self.cpuSysTick = 0
        except (FileNotFoundError, ValueError, IndexError):
            self.cpuUserTick = 0
            self.cpuSysTick = 0
        except Exception:
            self.cpuUserTick = 0
            self.cpuSysTick = 0

    def statusProcesso(self):
        """
        Lê informações de status do processo.
        """
        status_path = f'/proc/{self.pid}/status'
        try:
            with open(status_path, 'r') as f:
                for linha in f:
                    if linha.startswith("Name:"):
                        self.name = linha.split()[1]
                    elif linha.startswith("PPid:"):
                        self.ppid = int(linha.split()[1])
                    elif linha.startswith("Uid:"):
                        self.uid = int(linha.split()[1])
                        self.user_display = str(self.uid)
                    elif linha.startswith("State:"):
                        self.estado = linha.split()[1]
                    elif linha.startswith("Threads:"):
                        self.threads = int(linha.split()[1])
                    elif linha.startswith("VmRSS:"):
                        self.memoriaKB = int(linha.split()[1])
        except FileNotFoundError:
            self.name = '[Encerrado]'
            self.estado = 'Z'
            self.ppid = 0
            self.uid = -1
            self.threads = 0
            self.memoriaKB = 0
            self.user_display = '[Desconhecido]'
        except (ValueError, IndexError):
            self.name = '[Erro]'
            self.user_display = '[Erro User]'
        except Exception:
            self.name = '[Erro]'
            self.user_display = '[Erro User]'

    def iniciarProcesso(self):
        """
        Método principal para coletar todas as informações de um processo.
        """
        self.statusProcesso()
        if self.name not in ['[Encerrado]', '[Erro]']:
            self.tempoDeCPU()
            self.cmdLine()

    def __repr__(self):
        """
        Define a representação em string do objeto Processo.
        """
        return (
            f"┌─ Processo PID={self.pid}\n"
            f"│  Nome        : {self.name}\n"
            f"│  Estado      : {self.estado}\n"
            f"│  PPID        : {self.ppid}\n"
            f"│  UID         : {self.uid}\n"
            f"│  Threads     : {self.threads}\n"
            f"│  CPU (User)  : {self.cpuUserTick} ticks\n"
            f"│  CPU (Kernel): {self.cpuSysTick} ticks\n"
            f"│  Memória RAM : {self.memoriaKB} kB\n"
            f"│  Usuário     : {self.user_display}\n"
            f"│  Comando     : {self.commandCMD}\n"
            f"└────────────────────────────────────────────"
        )

# --- FUNÇÕES AUXILIARES ---

def uso_cpu_percent_internal(last_total, last_idle):
    """
    Calcula o uso percentual da CPU do sistema.
    """
    def ler_cpu():
        """Lê os ticks de CPU atuais de /proc/stat."""
        try:
            with open("/proc/stat", "r") as f:
                linha = f.readline()
                campos = list(map(int, linha.strip().split()[1:]))
                total = sum(campos)
                idle = campos[3] if len(campos) > 3 else 0
                return total, idle
        except (FileNotFoundError, IndexError, ValueError):
            return 0, 0

    current_total, current_idle = ler_cpu()

    if last_total == 0:
        return 0.0, 100.0, current_total, current_idle

    total_diff = current_total - last_total
    idle_diff = current_idle - last_idle

    if total_diff > 0:
        usage_percent = 100.0 * (total_diff - idle_diff) / total_diff
        idle_percent = 100.0 - usage_percent
        return usage_percent, idle_percent, current_total, current_idle
    
    return 0.0, 100.0, current_total, current_idle

def info_memoria():
    """
    Coleta informações sobre o uso de memória RAM e SWAP.
    """
    info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for linha in f:
                partes = linha.split()
                if len(partes) > 1:
                    chave = partes[0].rstrip(":")
                    try:
                        valor = int(partes[1])
                        info[chave] = valor
                    except ValueError:
                        continue
        
        # Calcula os valores de memória RAM
        mem_total = info.get('MemTotal', 0)
        mem_livre = info.get('MemFree', 0) + info.get('Buffers', 0) + info.get('Cached', 0)
        mem_usada = mem_total - mem_livre
        mem_percent = 100 * (mem_usada / mem_total) if mem_total > 0 else 0
        livre_percent = 100 - mem_percent

        # Calcula os valores de SWAP
        swap_total = info.get('SwapTotal', 0)
        swap_usada = swap_total - info.get('SwapFree', 0) if swap_total > 0 else 0

        return {
            "MemTotal": mem_total,
            "mem_total": mem_total,
            "mem_usada": mem_usada,
            "mem_livre_percent": livre_percent,
            "mem_usada_percent": mem_percent,
            "SwapTotal": swap_total,
            "swap_total": swap_total,
            "swap_usada": swap_usada
        }
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def total_processos_threads():
    """
    Conta o número total de processos e threads ativas no sistema.
    """
    total_threads = 0
    total_processos = 0

    proc = Path('/proc')
    try:
        for p in proc.iterdir():
            if p.is_dir() and p.name.isdigit():
                total_processos += 1
                try:
                    with open(p / "status", "r") as f:
                        for linha in f:
                            if linha.startswith("Threads:"):
                                total_threads += int(linha.split()[1])
                                break
                except (FileNotFoundError, ValueError, IndexError):
                    continue
                except Exception:
                    continue
    except Exception:
        return 0, 0

    return total_processos, total_threads

def listaProcessos():
    """
    Cria uma lista de objetos Processo.
    """
    lista = []
    proc = Path('/proc')
    try:
        PIDS = [int(p.name) for p in proc.iterdir() if p.is_dir() and p.name.isdigit()]
        
        for pid in PIDS:
            try:
                p = Processo(pid)
                p.iniciarProcesso()
                if p.name != '[Encerrado]':
                    lista.append(p)
            except Exception:
                continue
    except Exception:
        pass
    
    return lista

# --- INÍCIO: NOVAS FUNÇÕES (PARTE B) ---
def info_particoes_montadas():
    """
    Lista os pontos de montagem das partições de disco e coleta informações de uso
    chamando o programa C 'get_disk_usage'.
    """
    particoes = []
    
    # Caminho para o executável C. Assumimos que ele está na mesma pasta do script Python.
    # Se estiver em outro lugar, ajuste este caminho.
    c_executable_path = Path(__file__).parent / "get_disk_usage" 

    try:
        # Lê /proc/mounts para obter os pontos de montagem
        mounts_path = Path("/proc/mounts")
        for linha in mounts_path.read_text().splitlines():
            partes = linha.split()
            if len(partes) < 3: # Garante que a linha tenha informações suficientes
                continue

            device = partes[0]
            ponto_montagem = partes[1]
            tipo_fs = partes[2]

            # Filtra para mostrar apenas dispositivos de bloco reais e tipos de sistema de arquivos relevantes
            if device.startswith("/dev/") and tipo_fs not in ("sysfs", "proc", "devtmpfs", "tmpfs", "cgroup", "squashfs", "debugfs", "fusectl", "pstore", "none", "mqueue", "hugetlbfs"):
                
                total_gb = "N/A"
                usado_gb = "N/A"
                livre_gb = "N/A"
                percent_uso = "N/A"

                try:
                    # Chama o programa C para obter as estatísticas de uso
                    # capture_output=True para capturar stdout e stderr
                    # text=True para decodificar a saída como texto
                    result = subprocess.run([str(c_executable_path), ponto_montagem], capture_output=True, text=True, check=True)
                    
                    # Parsear a saída JSON do programa C
                    disk_stats = json.loads(result.stdout)

                    if "error" in disk_stats:
                        total_gb = disk_stats["error"]
                        usado_gb = disk_stats["error"]
                        livre_gb = disk_stats["error"]
                        percent_uso = disk_stats["error"]
                    else:
                        total_gb = disk_stats["total_bytes"] / (1024**3)
                        usado_gb = disk_stats["used_bytes"] / (1024**3)
                        livre_gb = disk_stats["free_bytes"] / (1024**3)
                        percent_uso = disk_stats["percent_used"]

                except subprocess.CalledProcessError as e:
                    # O programa C retornou um erro (código de saída diferente de 0)
                    total_gb = f"Erro ao executar C: {e.stderr.strip()}"
                    usado_gb = total_gb
                    livre_gb = total_gb
                    percent_uso = total_gb
                except json.JSONDecodeError:
                    total_gb = "Erro JSON C"
                    usado_gb = total_gb
                    livre_gb = total_gb
                    percent_uso = total_gb
                except FileNotFoundError:
                    total_gb = "Executável C não encontrado!"
                    usado_gb = total_gb
                    livre_gb = total_gb
                    percent_uso = total_gb
                except Exception as e:
                    total_gb = f"Erro inesperado: {e}"
                    usado_gb = total_gb
                    livre_gb = total_gb
                    percent_uso = total_gb

                particoes.append({
                    "Dispositivo": device,
                    "Ponto de Montagem": ponto_montagem,
                    "Tipo FS": tipo_fs,
                    "Total (GB)": f"{total_gb:.2f}" if isinstance(total_gb, float) else total_gb,
                    "Usado (GB)": f"{usado_gb:.2f}" if isinstance(usado_gb, float) else usado_gb,
                    "Livre (GB)": f"{livre_gb:.2f}" if isinstance(livre_gb, float) else livre_gb,
                    "Uso (%)": f"{percent_uso:.2f}%" if isinstance(percent_uso, float) else percent_uso
                })
    except (FileNotFoundError, Exception) as e:
        # Erro ao ler /proc/mounts
        particoes.append({"Erro": f"Não foi possível ler /proc/mounts: {e}"})
        return [] # Retorna vazio ou com erro se a fonte primária falhar
    return particoes

def get_process_open_files(pid):
    """
    Lista os arquivos abertos por um processo específico usando pathlib.
    """
    arquivos_abertos = []
    fd_path = Path(f'/proc/{pid}/fd')
    try:
        if fd_path.is_dir():
            for fd_link in fd_path.iterdir():
                try:
                    # Path.readlink() para resolver o link simbólico
                    destino = fd_link.readlink()
                    arquivos_abertos.append(f"{fd_link.name} -> {destino}")
                except (FileNotFoundError, OSError):
                    arquivos_abertos.append(f"{fd_link.name} -> [acesso negado ou link quebrado]")
                    continue
    except (PermissionError, FileNotFoundError):
         return ["Não foi possível acessar os arquivos (permissão negada ou processo encerrado)."]
    except Exception as e:
        return [f"Erro ao ler arquivos: {e}"]

    return arquivos_abertos if arquivos_abertos else ["Nenhum arquivo aberto encontrado ou acessível."]

def get_process_resources(pid):
    """
    Coleta e classifica os recursos abertos por um processo.
    Categoriza descritores: arquivos, sockets, pipes, anon, etc.
    Inclui locks ativos.
    """
    fd_path = Path(f'/proc/{pid}/fd')
    recursos = {
        "Arquivos": [],
        "Sockets": [],
        "Pipes": [],
        "Anon": [],
        "Erros": [],
        "Locks": []
    }

    # Categorizar descritores abertos
    try:
        if fd_path.is_dir():
            for fd in fd_path.iterdir():
                try:
                    destino = str(fd.readlink())
                    if destino.startswith("socket:"):
                        recursos["Sockets"].append(f"{fd.name} → {destino}")
                    elif destino.startswith("pipe:"):
                        recursos["Pipes"].append(f"{fd.name} → {destino}")
                    elif destino.startswith("[") or "anon_inode" in destino:
                        recursos["Anon"].append(f"{fd.name} → {destino}")
                    elif Path(destino).exists():
                        recursos["Arquivos"].append(f"{fd.name} → {destino}")
                    else:
                        recursos["Erros"].append(f"{fd.name} → {destino}")
                except Exception as e:
                    recursos["Erros"].append(f"{fd.name} → ERRO: {e}")
    except PermissionError:
        recursos["Erros"].append("Permissão negada para acessar descritores.")
    except Exception as e:
        recursos["Erros"].append(f"Erro ao ler fd/: {e}")

    # Tentar ler locks
    try:
        locks_path = Path(f'/proc/{pid}/locks')
        if locks_path.exists():
            with open(locks_path, 'r') as f:
                recursos["Locks"] = [linha.strip() for linha in f if linha.strip()]
    except FileNotFoundError:
        pass
    except Exception as e:
        recursos["Locks"].append(f"Erro ao ler locks: {e}")

    return recursos


# --- CLASSE PARA O MODELO GERAL DO SISTEMA ---
class SystemMonitorConsoleModel:
    """
    Responsável por coletar e gerenciar todos os dados do sistema.
    """
    def __init__(self):
        """
        Inicializa o modelo.
        """
        self._data = {}
        self._lock = threading.Lock()
        self._last_cpu_total = 0
        self._last_cpu_idle = 0
        self.cpu_history = []
        self.cpu_history_maxlen = 30
        
        # Inicialização da CPU
        _, _, self._last_cpu_total, self._last_cpu_idle = uso_cpu_percent_internal(0, 0)

    def _collect_all_data(self):
        """
        Coleta todas as informações do sistema.
        """
        temp_data = {}

        # Coleta de CPU global
        cpu_usage, cpu_idle, new_total, new_idle = uso_cpu_percent_internal(
            self._last_cpu_total, self._last_cpu_idle
        )
        temp_data["cpu_usage"] = cpu_usage
        temp_data["cpu_idle"] = cpu_idle
        self._last_cpu_total = new_total
        self._last_cpu_idle = new_idle

        # Atualiza o histórico de uso de CPU
        self.cpu_history.append(cpu_usage)
        if len(self.cpu_history) > self.cpu_history_maxlen:
            self.cpu_history.pop(0)
        temp_data["cpu_history"] = list(self.cpu_history)

        # Coleta de memória global
        temp_data["mem_info"] = info_memoria()

        # Coleta de total de processos e threads
        temp_data["total_processes"], temp_data["total_threads"] = total_processos_threads()

        # Coleta da lista de processos detalhada
        temp_data["processes_list"] = listaProcessos()

        temp_data["partitions"] = info_particoes_montadas()

        # Atualiza os dados de forma thread-safe
        with self._lock:
            self._data = temp_data

    def get_all_data(self):
        """
        Inicia uma thread para coletar os dados e retorna uma cópia dos dados.
        """
        collection_thread = threading.Thread(target=self._collect_all_data)
        collection_thread.start()
        collection_thread.join()  # Espera a thread terminar para garantir dados atualizados
        
        with self._lock:
            return self._data.copy()

# --- FUNÇÕES DE EXIBIÇÃO ---
def mostrarInfoGlobal(data):
    """
    Exibe as informações globais do sistema no console.
    """
    uso = data.get('cpu_usage', 0)
    ocioso = data.get('cpu_idle', 0)
    mem = data.get('mem_info', {})
    total_proc = data.get('total_processes', 0)
    total_threads = data.get('total_threads', 0)
    
    print("\n╔══════════════════ INFORMAÇÕES GLOBAIS DO SISTEMA ══════════════════╗")
    print(f"│ Uso total da CPU    : {uso:.2f}%")
    print(f"│ CPU ociosa          : {ocioso:.2f}%")
    print(f"│ Total de processos  : {total_proc}")
    print(f"│ Total de threads    : {total_threads}")
    print(f"│ Memória RAM Total   : {mem.get('MemTotal', 0)} kB")
    print(f"│ Memória RAM Usada   : {mem.get('mem_usada', 0)} kB")
    print(f"│ Memória Livre (%)   : {mem.get('mem_livre_percent', 0):.2f}%")
    print(f"│ Memória Usada (%)   : {mem.get('mem_usada_percent', 0):.2f}%")
    print(f"│ SWAP Total          : {mem.get('SwapTotal', 0)} kB")
    print(f"│ SWAP Usada          : {mem.get('swap_usada', 0)} kB")
    print("╚════════════════════════════════════════════════════════════════════╝")

def mostrarListaProcessos(processes_list):
    """
    Exibe a lista detalhada de processos no console.
    """
    print("\n[ PROCESSOS ATIVOS ]\n")
    processes_list.sort(key=lambda p: p.pid)
    for p in processes_list:
        print(p)

# --- CONTROLADOR ---
class ConsoleController:
    """
    Controlador da aplicação console.
    """
    def __init__(self):
        """
        Inicializa o controlador.
        """
        self.model = SystemMonitorConsoleModel()

    def run_monitor(self):
        """
        Orquestra o ciclo de coleta e exibição dos dados.
        """
        collected_data = self.model.get_all_data()
        mostrarInfoGlobal(collected_data)
        mostrarListaProcessos(collected_data.get('processes_list', []))

# # --- EXECUÇÃO PRINCIPAL ---
# if __name__ == '__main__':
#     """
#     Execução principal do script.
#     """
#     controller = ConsoleController()
#     try:
#         while True:
#             # Limpa a tela do console usando escape sequences ANSI
#             print("\033[2J\033[H", end="")
            
#             controller.run_monitor()
#             print("\n--- Atualizando em 2 segundos... (Ctrl+C para sair) ---")
#             time.sleep(2)
#     except KeyboardInterrupt:
#         print("\n\nMonitoramento interrompido pelo usuário.")
#         print("Encerrando...")