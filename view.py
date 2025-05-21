from colorama import Fore, Style, init
from model import uso_cpu_percent, info_memoria, total_processos_threads

init(autoreset=True)

def mostrarProcessos(listaDeProcessos):
    # Obter informações globais do sistema usando as funções do model.py
    uso, ocioso = uso_cpu_percent()
    mem = info_memoria()
    total_proc, total_threads = total_processos_threads()
    
    print(Fore.GREEN + Style.BRIGHT + "\n╔════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + Style.BRIGHT + "║ DASHBOARD DE PROCESSOS (RETRO)                              ║")
    print(Fore.GREEN + Style.BRIGHT + "╚════════════════════════════════════════════════════════════╝\n")
    
    print(Fore.BLUE + Style.BRIGHT + f"Uso da CPU: {uso:.2f}%")
    print(Fore.BLUE + Style.BRIGHT + f"Tempo ocioso da CPU: {ocioso:.2f}%")
    print(Fore.BLUE + Style.BRIGHT + f"Total de processos: {total_proc}")
    print(Fore.BLUE + Style.BRIGHT + f"Total de threads: {total_threads}")
    print(Fore.BLUE + Style.BRIGHT + f"Memória Usada: {mem['mem_usada_percent']:.2f}%")
    print(Fore.BLUE + Style.BRIGHT + f"Memória Livre: {mem['mem_livre_percent']:.2f}%")
    
    for p in listaDeProcessos:
        print(Fore.YELLOW + Style.BRIGHT + str(p))
        print(Fore.MAGENTA + "-" * 60)