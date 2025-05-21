from pathlib import Path
import pwd
import time

# Objeto
class Processo:
    def __init__(self, pid):
        self.pid = pid       # PID do proceso
        self.ppid = 0        # PID do processo pai
        self.name = ''       # Nome do processo
        self.estado = ''     # Estado (running, sleep, etc)
        self.uid = 0         # ID do usuário dono do processo
        self.cpuUserTick = 0 # Tempo de uso de CPU modo usuário
        self.cpuSysTick = 0  # Tempo de uso de CPU modo sistema
        self.threads = 0     # Threads do processo
        self.commandCMD = '' # Comando que iniciou o processo
        self.memoriaKB = 0   # Memória RAM usada (em kB)
        self.user = 'root'   # Nome do usuário

    def cmdLine(self):
        try:
            cmd_path = f'/proc/{self.pid}/cmdline'
            with open(cmd_path, 'r') as f:
                conteudo = f.read()
                self.commandCMD = conteudo.replace('\x00', ' ').strip()
        except:
            self.commandCMD = 'NO COMMAND'

    def tempoDeCPU(self):
        path_cpu = f'/proc/{self.pid}/stat'
        with open(path_cpu, 'r') as f:
            valores = f.read().split()
            self.cpuUserTick = int(valores[13])
            self.cpuSysTick = int(valores[14])

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
                        self.user = pwd.getpwuid(self.uid).pw_name if self.uid != 0 else 'root'
                    elif linha.startswith("State:"):
                        self.estado = linha.split()[1]
                    elif linha.startswith("Threads:"):
                        self.threads = int(linha.split()[1])
                    elif linha.startswith("VmRSS:"):
                        self.memoriaKB = int(linha.split()[1])  # valor em kB
                    # Se já tiver todos os campos, pode parar cedo (opcional)
                    if all([self.name, self.ppid, self.estado, self.uid, self.threads]):
                        break
        except FileNotFoundError:
            print(f"Processo {self.pid} não encontrado.")

    def iniciarProcesso(self):
        self.statusProcesso()
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
        f"│  Usuário     : {self.user}\n"
        f"└────────────────────────────────────────────"
    )


# Funções principais

def imprimeArquivo(path):
    with open(path, 'r') as f:
        for linha in f:
            print(linha)

def cpuInfo():
    imprimeArquivo('/proc/cpuinfo')


def listaProcessos():
    listaProcessos = []
    proc = Path('/proc')
    PIDS = [int(p.name) for p in proc.iterdir() if p.is_dir() and p.name.isdigit()]
    for i in PIDS:
        aux = Processo(i)
        aux.iniciarProcesso()
        listaProcessos.append(aux)
    return listaProcessos


# Informações do sistema

def uso_cpu_percent():
    def ler_cpu():
        with open("/proc/stat", "r") as f:
            linha = f.readline()
            campos = list(map(int, linha.strip().split()[1:]))
            total = sum(campos)
            idle = campos[3]
            return total, idle

    total1, idle1 = ler_cpu()
    time.sleep(1)
    total2, idle2 = ler_cpu()

    total_diff = total2 - total1
    idle_diff = idle2 - idle1

    uso_percent = 100.0 * (total_diff - idle_diff) / total_diff
    ocioso_percent = 100.0 - uso_percent
    return uso_percent, ocioso_percent


def info_memoria():
    info = {}
    with open("/proc/meminfo", "r") as f:
        for linha in f:
            partes = linha.split()
            chave = partes[0].rstrip(":")
            valor = int(partes[1])
            info[chave] = valor

    mem_total = info['MemTotal']
    mem_livre = info['MemFree'] + info.get('Buffers', 0) + info.get('Cached', 0)
    mem_usada = mem_total - mem_livre
    mem_percent = 100 * mem_usada / mem_total
    livre_percent = 100 - mem_percent

    swap_total = info.get('SwapTotal', 0)
    swap_usada = swap_total - info.get('SwapFree', 0)

    return {
        "mem_total": mem_total,
        "mem_usada": mem_usada,
        "mem_livre_percent": livre_percent,
        "mem_usada_percent": mem_percent,
        "swap_total": swap_total,
        "swap_usada": swap_usada
    }


def total_processos_threads():
    total_threads = 0
    total_processos = 0

    proc = Path('/proc')
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

    return total_processos, total_threads


def mostrarInfoGlobal():
    uso, ocioso = uso_cpu_percent()
    mem = info_memoria()
    total_proc, total_threads = total_processos_threads()

    print("╔══════════════════ INFORMAÇÕES GLOBAIS DO SISTEMA ══════════════════╗")
    print(f"│ Uso total da CPU    : {uso:.2f}%")
    print(f"│ CPU ociosa          : {ocioso:.2f}%")
    print(f"│ Total de processos  : {total_proc}")
    print(f"│ Total de threads    : {total_threads}")
    print(f"│ Memória RAM Total   : {mem['mem_total']} kB")
    print(f"│ Memória RAM Usada   : {mem['mem_usada']} kB")
    print(f"│ Memória Livre (%)   : {mem['mem_livre_percent']:.2f}%")
    print(f"│ Memória Usada (%)   : {mem['mem_usada_percent']:.2f}%")
    print(f"│ SWAP Total          : {mem['swap_total']} kB")
    print(f"│ SWAP Usada          : {mem['swap_usada']} kB")
    print("╚════════════════════════════════════════════════════════════════════╝")


# Execução principal
if __name__ == '__main__':
    mostrarInfoGlobal()
    print("\n[ PROCESSOS ATIVOS ]\n")
    processos = listaProcessos()
    for p in processos:
        print(p)
