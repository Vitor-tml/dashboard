from pathlib import Path # Módulo para manipulação de caminhos de arquivo de forma orientada a objetos
import time # Módulo para funcionalidades relacionadas a tempo, como pausas (sleep)
import threading # Módulo essencial para trabalhar com threads, permitindo execução paralela de tarefas

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
        self.pid = pid # Identificador único do processo
        self.ppid = 0 # ID do processo pai 
        self.name = '' # Nome do processo
        self.estado = '' # Estado atual do processo
        self.uid = 0 # ID do usuário (User ID) que é dono do processo
        self.cpuUserTick = 0 # Tempo de CPU gasto no modo usuário 
        self.cpuSysTick = 0 # Tempo de CPU gasto no modo kernel
        self.threads = 0 # Número de threads associadas a este processo
        self.commandCMD = '' # Linha de comando que iniciou o processo
        self.memoriaKB = 0 # Consumo de memória RAM em Kilobytes
        self.user_display = '' # Campo para exibir o UID

    def cmdLine(self):
        """
        Lê a linha de comando completa utilizada para iniciar o processo a partir de /proc/[pid]/cmdline.
        Trata caracteres nulos ('\x00') que separam os argumentos da linha de comando.
        """
        try:
            cmd_path = f'/proc/{self.pid}/cmdline'
            with open(cmd_path, 'r') as f:
                conteudo = f.read()
                # Substitui os caracteres nulos por espaços e remove espaços extras
                self.commandCMD = conteudo.replace('\x00', ' ').strip()
        except FileNotFoundError:
            # Caso o processo termine antes da leitura, o arquivo cmdline desaparece
            self.commandCMD = 'NO COMMAND (Processo encerrado)'
        except Exception as e:
            # Captura outras exceções inesperadas durante a leitura
            self.commandCMD = f'ERRO: {e}'

    def tempoDeCPU(self):
        """
        Lê os ticks de CPU gastos pelo processo no modo usuário e kernel a partir de /proc/[pid]/stat.
        Esses ticks são usados para calcular o uso de CPU percentual do processo ao longo do tempo.
        """
        path_cpu = f'/proc/{self.pid}/stat'
        try:
            with open(path_cpu, 'r') as f:
                valores = f.read().split() # Lê e divide a linha em uma lista de strings
                if len(valores) > 14: # Os ticks de CPU estão nas posições 13 (utime) e 14 (stime)
                    self.cpuUserTick = int(valores[13])
                    self.cpuSysTick = int(valores[14])
                else:
                    # Se não há valores suficientes, inicializa com zero para evitar erros
                    self.cpuUserTick = 0
                    self.cpuSysTick = 0
        except FileNotFoundError:
            # Processo pode ter sido encerrado
            self.cpuUserTick = 0
            self.cpuSysTick = 0
        except Exception as e:
            # Captura e trata outros erros, como permissão negada
            # print(f"Erro ao ler tempo de CPU para PID {self.pid}: {e}") # Apenas um debug
            self.cpuUserTick = 0
            self.cpuSysTick = 0

    def statusProcesso(self):
        """
        Lê várias informações de status do processo a partir de /proc/[pid]/status,
        como nome, PPID, UID, estado, número de threads e uso de memória.
        """
        status_path = f'/proc/{self.pid}/status'
        try:
            with open(status_path, 'r') as f:
                for linha in f: # Itera sobre cada linha do arquivo
                    if linha.startswith("Name:"):
                        self.name = linha.split()[1]
                    elif linha.startswith("PPid:"):
                        self.ppid = int(linha.split()[1])
                    elif linha.startswith("Uid:"):
                        self.uid = int(linha.split()[1])
                        self.user_display = str(self.uid) # Armazena o UID como string para exibição
                    elif linha.startswith("State:"):
                        self.estado = linha.split()[1]
                    elif linha.startswith("Threads:"):
                        self.threads = int(linha.split()[1])
                    elif linha.startswith("VmRSS:"): # VmRSS representa a memória RAM física usada
                        self.memoriaKB = int(linha.split()[1])
        except FileNotFoundError:
            # Define valores padrão para processos que não existem mais ou não podem ser lidos
            self.name = '[Encerrado]'
            self.estado = 'Z' # Zumbi
            self.ppid = 0
            self.uid = -1
            self.threads = 0
            self.memoriaKB = 0
            self.user_display = '[Desconhecido]'
        except Exception as e:
            # print(f"Erro ao ler status do processo {self.pid}: {e}") # Apenas um debug
            self.name = '[Erro]'
            self.user_display = '[Erro User]'

    def iniciarProcesso(self):
        """
        Método principal para coletar todas as informações de um processo.
        Primeiro coleta o status, e só então tenta coletar CPU e CMD se o processo ainda existir.
        """
        self.statusProcesso()
        # Só tenta ler CPU e CMD se o processo não estiver marcado como encerrado ou com erro de leitura de status
        if self.name not in ['[Encerrado]', '[Erro]']:
            self.tempoDeCPU()
            self.cmdLine()

    def __repr__(self):
        """
        Define a representação em string do objeto Processo, útil para imprimir detalhes
        do processo de forma formatada.
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
        f"│  Usuário     : {self.user_display}\n" # Exibe o UID do usuário
        f"│  Comando     : {self.commandCMD}\n"
        f"└────────────────────────────────────────────"
    )

# --- FUNÇÕES AUXILIARES ---

def uso_cpu_percent_internal(last_total, last_idle):
    """
    Calcula o uso percentual da CPU do sistema inteiro.
    Baseia-se na leitura do arquivo /proc/stat, que contém estatísticas globais da CPU.
    Para calcular a porcentagem, compara as leituras atuais com as leituras anteriores.

    Args:
        last_total (int): Total de ticks de CPU da leitura anterior.
        last_idle (int): Total de ticks ociosos de CPU da leitura anterior.

    Returns:
        tuple: (uso_cpu_percent, cpu_ociosa_percent, current_total_ticks, current_idle_ticks)
    """
    def ler_cpu():
        """Função aninhada para ler os ticks de CPU atuais de /proc/stat."""
        try:
            with open("/proc/stat", "r") as f:
                linha = f.readline()
                # Os campos de interesse são os ticks de CPU, que são inteiros
                campos = list(map(int, linha.strip().split()[1:]))
                total = sum(campos) # Soma todos os ticks (user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice)
                idle = campos[3] # O quarto campo (índice 3) é o tempo ocioso (idle)
                return total, idle
        except (FileNotFoundError, IndexError, ValueError) as e:
            # print(f"Erro ao ler /proc/stat: {e}") # Descomente para debug
            return 0, 0 # Retorna zero em caso de erro

    current_total, current_idle = ler_cpu()

    # Se last_total é 0, significa que é a primeira leitura, então não há mudança para calcular
    if last_total == 0:
        return 0.0, 100.0, current_total, current_idle

    # Calcula a diferença de ticks entre as leituras
    total_diff = current_total - last_total
    idle_diff = current_idle - last_idle

    if total_diff > 0:
        # Fórmula para calcular o uso da CPU: 100 * (tempo_total_usado - tempo_ocioso_usado) / tempo_total_usado
        usage_percent = 100.0 * (total_diff - idle_diff) / total_diff
        idle_percent = 100.0 - usage_percent
        return usage_percent, idle_percent, current_total, current_idle
    # Se não houver diferença ou total_diff for zero, retorna 0% de uso
    return 0.0, 100.0, current_total, current_idle


def info_memoria():
    """
    Coleta informações detalhadas sobre o uso de memória RAM e SWAP a partir de /proc/meminfo.

    Returns:
        dict: Um dicionário contendo o total, usado e percentuais de memória RAM e SWAP.
              Retorna um dicionário vazio em caso de erro.
    """
    info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for linha in f:
                partes = linha.split()
                if len(partes) > 1:
                    chave = partes[0].rstrip(":") # Remove os dois pontos do final da chave
                    try:
                        valor = int(partes[1]) # O valor é sempre um número inteiro
                        info[chave] = valor
                    except ValueError:
                        continue # Pula linhas que não possuem um valor numérico válido
        
        # Calcula os valores de memória RAM
        mem_total = info.get('MemTotal', 0)
        # Memória livre é geralmente MemFree + Buffers + Cached para uma visão mais real
        mem_livre = info.get('MemFree', 0) + info.get('Buffers', 0) + info.get('Cached', 0)
        mem_usada = mem_total - mem_livre
        mem_percent = 100 * (mem_usada / mem_total) if mem_total > 0 else 0
        livre_percent = 100 - mem_percent

        # Calcula os valores de SWAP
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
    """
    Conta o número total de processos e threads ativas no sistema,
    iterando sobre os diretórios numéricos em /proc.

    Returns:
        tuple: (total_de_processos, total_de_threads)
    """
    total_threads = 0
    total_processos = 0

    proc = Path('/proc') # Objeto Path para o diretório /proc
    try:
        for p in proc.iterdir(): # Itera sobre os itens dentro de /proc
            # Verifica se é um diretório e se o nome é um número (indicando um PID)
            if p.is_dir() and p.name.isdigit():
                total_processos += 1
                try:
                    # Abre o arquivo status para contar as threads de cada processo
                    with open(p / "status", "r") as f:
                        for linha in f:
                            if linha.startswith("Threads:"):
                                total_threads += int(linha.split()[1])
                                break # Já encontrou a linha de threads, pode ir para o próximo processo
                except FileNotFoundError:
                    continue # O processo pode ter terminado enquanto estávamos iterando
                except Exception as e:
                    # print(f"Erro ao ler threads do processo {p.name}: {e}") # Descomente para debug
                    continue
    except Exception as e:
        # print(f"Erro ao listar diretórios em /proc: {e}") # Descomente para debug
        return 0, 0 # Retorna zero em caso de erro na listagem de /proc

    return total_processos, total_threads

def listaProcessos():
    """
    Cria uma lista de objetos Processo, cada um contendo informações detalhadas
    de um processo ativo no sistema.

    Returns:
        list: Uma lista de objetos Processo.
    """
    lista = []
    proc = Path('/proc')
    # Coleta todos os PIDs (diretórios numéricos) em /proc
    PIDS = [int(p.name) for p in proc.iterdir() if p.is_dir() and p.name.isdigit()]
    
    # Itera sobre cada PID para criar e inicializar um objeto Processo
    for pid in PIDS:
        p = Processo(pid)
        p.iniciarProcesso() # Coleta todas as informações do processo
        if p.name != '[Encerrado]': # Adiciona à lista apenas processos que ainda estão ativos
            lista.append(p)
    return lista

# --- CLASSE PARA O MODELO GERAL DO SISTEMA (com Threading) ---
class SystemMonitorConsoleModel:
    """
    Responsável por coletar e gerenciar todos os dados do sistema.
    Utiliza threading para realizar a coleta de dados em segundo plano,
    garantindo que a interface principal possa ser atualizada sem travamentos.
    """
    def __init__(self):
        """
        Inicializa o modelo, incluindo estruturas para armazenar dados e um lock para segurança de threads.
        """
        self._data = {}             # Dicionário para armazenar os dados coletados (uso de CPU, memória, processos, etc.)
        self._lock = threading.Lock() # Um Lock é usado para proteger o acesso a _data, garantindo que
                                      # apenas uma thread possa modificar ou ler _data por vez, evitando corrupção de dados.
        self._last_cpu_total = 0    # Armazena o total de ticks de CPU da última leitura para cálculo percentual
        self._last_cpu_idle = 0     # Armazena o total de ticks ociosos da última leitura para cálculo percentual
        self.cpu_history = []       # Lista para armazenar o histórico de uso de CPU (para gráficos/tendências)
        self.cpu_history_maxlen = 30# Define o tamanho máximo do histórico de CPU
        
        # Realiza uma primeira leitura da CPU para inicializar _last_cpu_total e _last_cpu_idle.
        # Isso é importante para que o primeiro cálculo de porcentagem de CPU seja válido.
        _, _, self._last_cpu_total, self._last_cpu_idle = uso_cpu_percent_internal(0, 0)

    def _collect_all_data(self):
        """
        Este método é o "core" da coleta de dados. Ele será executado em uma thread separada.
        Coleta todas as informações do sistema e armazena-as em um dicionário temporário,
        para depois transferi-las para self._data de forma segura.
        """
        temp_data = {} # Usa um dicionário temporário para armazenar os dados coletados

        # Coleta de CPU global
        cpu_usage, cpu_idle, new_total, new_idle = uso_cpu_percent_internal(
            self._last_cpu_total, self._last_cpu_idle
        )
        temp_data["cpu_usage"] = cpu_usage
        temp_data["cpu_idle"] = cpu_idle
        # Atualiza os valores da última leitura para o próximo cálculo de CPU
        self._last_cpu_total = new_total
        self._last_cpu_idle = new_idle

        # Atualiza o histórico de uso de CPU
        self.cpu_history.append(cpu_usage)
        if len(self.cpu_history) > self.cpu_history_maxlen:
            self.cpu_history.pop(0) # Remove o elemento mais antigo se o histórico exceder o tamanho máximo
        temp_data["cpu_history"] = list(self.cpu_history)  # Copia o histórico para o dicionário de dados

        # Coleta de memória global
        temp_data["mem_info"] = info_memoria()

        # Coleta de total de processos e threads
        temp_data["total_processes"], temp_data["total_threads"] = total_processos_threads()

        # Coleta da lista de processos detalhada
        temp_data["processes_list"] = listaProcessos()

        # Adquire o lock antes de atualizar self._data. Isso garante que a thread principal
        # não tente ler _data enquanto esta thread está atualizando-o.
        with self._lock:
            self._data = temp_data # Atomicamente atualiza os dados gerais

    def get_all_data(self):
        """
        Inicia uma thread para coletar os dados e retorna uma cópia dos dados coletados
        assim que a coleta estiver (provavelmente) em andamento ou completa.
        Não espera explicitamente a thread terminar (non-blocking call para a thread),
        o que permite que a interface principal possa ser atualizada mesmo que a coleta
        demore um pouco mais.

        Returns:
            dict: Uma cópia dos dados do sistema coletados.
        """
        collection_thread = threading.Thread(target=self._collect_all_data)
        collection_thread.start() # Inicia a thread de coleta em segundo plano
        """
        # Com o `threading.Thread`, se você não chamar `join()`, a thread continua a executar
        # em segundo plano e esta função retorna imediatamente. A thread principal pode
        # então usar os dados _antigos_ enquanto a nova coleta está em andamento.
        # A próxima chamada a `get_all_data` irá iniciar outra thread de coleta
        # e, quando ela terminar, os dados serão atualizados.
        # Se `collection_thread.join()` fosse descomentado, esta função bloquearia
        # até a coleta de dados ser totalmente concluída pela thread.
        # collection_thread.join() # Se descomentado, esta função esperaria a coleta terminar

        # Retorna uma cópia dos dados mais recentes disponíveis (podem ser os da coleta anterior
        # se a nova thread ainda estiver rodando).
        with self._lock:
            return self._data.copy() # Retorna uma cópia para evitar modificações externas diretas

# --- FUNÇÕES PRINCIPAIS DE EXIBIÇÃO (View) ---
def mostrarInfoGlobal(data):
    """
    Exibe as informações globais do sistema (CPU, memória, processos, threads) no console.

    Args:
        data (dict): Um dicionário contendo todas as informações globais do sistema.
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
    Exibe a lista detalhada de processos no console, um por um.

    Args:
        processes_list (list): Uma lista de objetos Processo.
    """
    print("\n[ PROCESSOS ATIVOS ]\n")
    # Opcional: Garante que a lista de processos esteja ordenada por PID para uma exibição consistente
    processes_list.sort(key=lambda p: p.pid)
    for p in processes_list:
        print(p) # Chama o método __repr__ do objeto Processo para imprimir seus detalhes

# --- CONTROLADOR (Ajustado para orquestrar a coleta e exibição no console) ---
class ConsoleController:
    """
    Atua como o "cérebro" da aplicação, coordenando a comunicação entre o Modelo (coleta de dados)
    e a Visão (exibição no console).
    """
    def __init__(self):
        """
        Inicializa o controlador com uma instância do Modelo.
        """
        self.model = SystemMonitorConsoleModel()

    def run_monitor(self):
        """
        Orquestra o ciclo de coleta e exibição dos dados do sistema.
        """
        # 1. O Controlador pede os dados ao Modelo. O Modelo inicia a coleta em uma thread separada.
        collected_data = self.model.get_all_data()

        # 2. O Controlador passa os dados recebidos para as funções de exibição (Visão).
        mostrarInfoGlobal(collected_data)
        # Garante que a lista de processos seja passada, mesmo que esteja vazia
        mostrarListaProcessos(collected_data.get('processes_list', []))

# --- EXECUÇÃO PRINCIPAL DO SCRIPT ---
if __name__ == '__main__':
    """
    Bloco de execução principal do script.
    Cria uma instância do Controlador e entra em um loop infinito para atualizar
    continuamente as informações no console.
    """
    controller = ConsoleController()
    while True: # Loop principal para atualização contínua
        controller.run_monitor() # Executa um ciclo completo de coleta e exibição
        print("\n--- Atualizando em 2 segundos... ---")
        time.sleep(2) # Pausa por 2 segundos antes da próxima atualização
        # Linha para limpar a tela do console. Útil para monitores em tempo real,
        # mas pode não funcionar em todos os ambientes ou pode não ser desejado.
        # import os
        # os.system('cls' if os.name == 'nt' else 'clear')