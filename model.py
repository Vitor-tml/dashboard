from pathlib import Path

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

    def cmdLine(self):
        try:
            cmd_path = '/proc/' + str(self.pid) + '/cmdline'
            with open(cmd_path, 'r') as f:
                conteudo = f.read()
                self.commandCMD = conteudo.replace('\x00', ' ').strip()
        except:
            self.commandCMD = 'NO COMMAND'

    def tempoDeCPU(self):
        path_cpu = '/proc/' + str(self.pid) + '/stat'
        with open(path_cpu, 'r') as f:
            valores = f.read().split()
            self.cpuUserTick = int(valores[13])  # tempo em ticks no modo usuário
            self.cpuSysTick = int(valores[1
            4])  # tempo em ticks no modo sistema

    def statusProcesso(self):
        status_path = '/proc/' + str(self.pid) + '/status'
        try:
            with open(status_path, 'r') as f:
                for linha in f:
                    if linha.startswith("Name:"):
                        self.name = linha.split()[1]
                    elif linha.startswith("PPid:"):
                        self.ppid = int(linha.split()[1])
                    elif linha.startswith("Uid:"):
                        self.uid = int(linha.split()[1])
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
        f"└────────────────────────────────────────────"
    )


# Funções
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