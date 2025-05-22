from pathlib import Path
import time
import threading # Módulo para trabalhar com threads

class Processo:
    def __init__(self, pid):
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
        self.user_display = '' # Substitui 'user' para exibir o UID

    def cmdLine(self):
        try:
            cmd_path = f'/proc/{self.pid}/cmdline'
            with open(cmd_path, 'r') as f:
                conteudo = f.read()
                self.commandCMD = conteudo.replace('\x00', ' ').strip()
        except FileNotFoundError:
            self.commandCMD = 'NO COMMAND (Processo encerrado)'
        except Exception as e:
            self.commandCMD = f'ERRO: {e}'

    def tempoDeCPU(self):
        path_cpu = f'/proc/{self.pid}/stat'
        try:
            with open(path_cpu, 'r') as f:
                valores = f.read().split()
                if len(valores) > 14: # Verifica se há valores suficientes
                    self.cpuUserTick = int(valores[13])
                    self.cpuSysTick = int(valores[14])
                else:
                    self.cpuUserTick = 0
                    self.cpuSysTick = 0
        except FileNotFoundError:
            self.cpuUserTick = 0
            self.cpuSysTick = 0
        except Exception as e:
            # print(f"Erro ao ler tempo de CPU para PID {self.pid}: {e}") # Descomente para debug
            self.cpuUserTick = 0
            self.cpuSysTick = 0

    def statusProcesso(self):
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
                        self.user_display = str(self.uid) # Exibe o UID ao invés do nome de usuário
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
        except Exception as e:
            # print(f"Erro ao ler status do processo {self.pid}: {e}") # Descomente para debug
            self.name = '[Erro]'
            self.user_display = '[Erro User]'

    def iniciarProcesso(self):
        self.statusProcesso()
        if self.name not in ['[Encerrado]', '[Erro]']: # Só tenta ler CPU e CMD se o processo existir
            self.tempoDeCPU()
            self.cmdLine()

    def __repr__(self):
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
        f"│  Usuário     : {self.user_display}\n" # Usa o campo ajustado
        f"│  Comando     : {self.commandCMD}\n"
        f"└────────────────────────────────────────────"
    )

# --- FUNÇÕES AUXILIARES (AGORA COM TRATAMENTO DE ERROS E AJUSTES PARA THREADING) ---

def uso_cpu_percent_internal(last_total, last_idle):
    """Calcula o uso de CPU percentual baseado em leituras anteriores."""
    def ler_cpu():
        try:
            with open("/proc/stat", "r") as f:
                linha = f.readline()
                campos = list(map(int, linha.strip().split()[1:]))
                total = sum(campos)
                idle = campos[3]
                return total, idle
        except (FileNotFoundError, IndexError, ValueError) as e:
            # print(f"Erro ao ler /proc/stat: {e}") # Descomente para debug
            return 0, 0

    current_total, current_idle = ler_cpu()

    # Se esta é a primeira leitura, inicializa e retorna 0%
    if last_total == 0:
        return 0.0, 100.0, current_total, current_idle

    total_diff = current_total - last_total
    idle_diff = current_idle - last_idle

    if total_diff > 0:
        usage_percent = 100.0 * (total_diff - idle_diff) / total_diff
        idle_percent = 100.0 - usage_percent
        return usage_percent, idle_percent, current_total, current_idle
    return 0.0, 100.0, current_total, current_idle # Retorna 0% se não houver diferença ou erro


def info_memoria():
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
        
        mem_total = info.get('MemTotal', 0)
        mem_livre = info.get('MemFree', 0) + info.get('Buffers', 0) + info.get('Cached', 0)
        mem_usada = mem_total - mem_livre
        mem_percent = 100 * (mem_usada / mem_total) if mem_total > 0 else 0
        livre_percent = 100 - mem_percent

        swap_total = info.get('SwapTotal', 0)
        swap_usada = swap_total - info.get('SwapFree', 0) if swap_total > 0 else 0

        return {
            "mem_total": mem_total,
            "mem_usada": mem_usada,
            "mem_livre_percent": livre_percent,
            "mem_usada_percent": mem_percent,
            "swap_total": swap_total,
            "swap_usada": swap_usada
        }
    except FileNotFoundError:
        # print("Erro: /proc/meminfo não encontrado.") # Descomente para debug
        return {}
    except Exception as e:
        # print(f"Erro ao ler /proc/meminfo: {e}") # Descomente para debug
        return {}


def total_processos_threads():
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
                except FileNotFoundError:
                    continue
                except Exception as e:
                    # print(f"Erro ao ler threads do processo {p.name}: {e}") # Descomente para debug
                    continue
    except Exception as e:
        # print(f"Erro ao listar diretórios em /proc: {e}") # Descomente para debug
        return 0, 0

    return total_processos, total_threads

def listaProcessos():
    lista = []
    proc = Path('/proc')
    PIDS = [int(p.name) for p in proc.iterdir() if p.is_dir() and p.name.isdigit()]
    
    # Podemos usar um ThreadPoolExecutor aqui para paralelizar a leitura de cada processo
    # Mas para manter a simplicidade e focar na estrutura pedida, vamos manter a iteração
    # Se quiser otimizar MUITO, Threads para CADA processo seria o próximo passo.
    # Por agora, a coleta geral já estará em uma thread separada.
    for pid in PIDS:
        p = Processo(pid)
        p.iniciarProcesso() # Este método já faz as leituras de status, CPU e CMD
        if p.name != '[Encerrado]': # Filtra processos que desapareceram
            lista.append(p)
    return lista

# --- NOVA CLASSE PARA O MODELO GERAL DO SISTEMA (com Threading) ---
class SystemMonitorConsoleModel:
    def __init__(self):
        self._data = {} # Dicionário para armazenar os dados coletados
        self._lock = threading.Lock() # Lock para garantir acesso seguro aos dados
        self._last_cpu_total = 0 # Para cálculo do uso de CPU%
        self._last_cpu_idle = 0  # Para cálculo do uso de CPU%
        
        # Inicializa os valores da CPU na primeira leitura para o cálculo do percentual
        _, _, self._last_cpu_total, self._last_cpu_idle = uso_cpu_percent_internal(0, 0)

    def _collect_all_data(self):
        """
        Este método será executado pela thread em segundo plano e coletará TODOS os dados.
        """
        temp_data = {}

        # Coleta de CPU global
        cpu_usage, cpu_idle, new_total, new_idle = uso_cpu_percent_internal(
            self._last_cpu_total, self._last_cpu_idle
        )
        temp_data["cpu_usage"] = cpu_usage
        temp_data["cpu_idle"] = cpu_idle
        self._last_cpu_total = new_total # Atualiza os últimos valores para a próxima coleta
        self._last_cpu_idle = new_idle

        # Coleta de memória global
        temp_data["mem_info"] = info_memoria()

        # Coleta de total de processos e threads
        temp_data["total_processes"], temp_data["total_threads"] = total_processos_threads()

        # Coleta da lista de processos detalhada
        temp_data["processes_list"] = listaProcessos()

        # Adquire o lock antes de atualizar os dados
        with self._lock:
            self._data = temp_data

    def get_all_data(self):
        """
        Inicia uma thread para coletar os dados e espera por ela,
        depois retorna uma cópia dos dados coletados.
        """
        collection_thread = threading.Thread(target=self._collect_all_data)
        collection_thread.start()
        collection_thread.join() # Espera a thread terminar a coleta

        # Retorna uma cópia dos dados coletados para segurança
        with self._lock:
            return self._data.copy()

# --- FUNÇÃO PRINCIPAL DE EXIBIÇÃO (View) ---
def mostrarInfoGlobal(data):
    """
    Exibe as informações globais do sistema no console, recebendo os dados como argumento.
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
    print(f"│ Memória RAM Total   : {mem.get('mem_total', 0)} kB")
    print(f"│ Memória RAM Usada   : {mem.get('mem_usada', 0)} kB")
    print(f"│ Memória Livre (%)   : {mem.get('mem_livre_percent', 0):.2f}%")
    print(f"│ Memória Usada (%)   : {mem.get('mem_usada_percent', 0):.2f}%")
    print(f"│ SWAP Total          : {mem.get('swap_total', 0)} kB")
    print(f"│ SWAP Usada          : {mem.get('swap_usada', 0)} kB")
    print("╚════════════════════════════════════════════════════════════════════╝")

def mostrarListaProcessos(processes_list):
    """
    Exibe a lista detalhada de processos no console.
    """
    print("\n[ PROCESSOS ATIVOS ]\n")
    # Garante que a lista de processos esteja ordenada (opcional, mas bom para consistência)
    processes_list.sort(key=lambda p: p.pid)
    for p in processes_list:
        print(p)

# --- CONTROLADOR (Ajustado para orquestrar a coleta e exibição no console) ---
class ConsoleController:
    def __init__(self):
        self.model = SystemMonitorConsoleModel()

    def run_monitor(self):
        """
        Orquestra a coleta de dados e a exibição no console.
        """
        # 1. Controlador pede os dados ao Modelo.
        collected_data = self.model.get_all_data()

        # 2. Controlador passa os dados para as funções de exibição (View).
        mostrarInfoGlobal(collected_data)
        mostrarListaProcessos(collected_data.get('processes_list', []))

# --- EXECUÇÃO PRINCIPAL DO SCRIPT ---
if __name__ == '__main__':
    controller = ConsoleController()
    while True: # Loop para atualização contínua no console
        controller.run_monitor()
        print("\n--- Atualizando em 2 segundos... ---")
        time.sleep(2) # Intervalo de atualização
        # Limpar a tela para a próxima atualização (opcional, depende do terminal)
        # import os
        # os.system('cls' if os.name == 'nt' else 'clear')