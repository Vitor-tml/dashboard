from model import Processo
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
import plotext as plt
from rich.align import Align


def testes():
    console = Console()

    # Dados
    x = list(range(1, 13))
    y = [3, 5, 2, 6, 4, 7, 5, 6, 4, 5, 8, 9]

    # Gera o gráfico como string
    plt.clf()
    
    plt.plot(x, y)
    plt.title("Gráfico de Linha")
    plt.frame(True)    # Ativa moldura no plotext
    plt.xticks([2, 4, 6, 8, 10])  # ✅ Coloca ticks apenas nos pontos definidos
    graph = plt.build()

    # Alinha o gráfico ao centro dentro do painel
    panel = Panel(Align.center(graph), title="📊 Dashboard Capivárico")

    console.print(panel)

def iniciaDash(processos, page_size=10):
    console = Console()

    total = len(processos)
    page = 0

    while True:
        table = Table(title="Lista de Processos", expand=True)  # cria a tabela em cada iteração

        table.add_column("ID", style="cyan")
        table.add_column("Nome", style="magenta")
        table.add_column("PPID", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("UID", style="blue")
        table.add_column("CPU (ticks)", style="white")
        table.add_column("Threads", style="purple")
        table.add_column("Comando", style="bright_black")
        table.add_column("Memória (kB)", style="red")
    

        start = page * page_size
        end = min(start + page_size, total)

        for processo in processos[start:end]:
            table.add_row(
                str(processo.pid),
                str(processo.name),
                str(processo.ppid),
                str(processo.estado),
                str(processo.uid),
                str(processo.cpuUserTick + processo.cpuSysTick),
                str(processo.threads),
                str(processo.commandCMD),
                str(processo.memoriaKB),
            )

        console.clear()
        console.print(table)
        console.print(f"Página {page + 1}/{(total - 1) // page_size + 1} (q para sair, Enter ou w para próxima)")

        cmd = input()
        if cmd.lower() == 'q':
            break
        if cmd.lower() == 'w' or cmd == '':
            if (page + 1) * page_size >= total:
                page = 0  # volta para a primeira página se passar do total
            else:
                page += 1
