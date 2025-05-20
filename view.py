from colorama import Fore, Style, init

init(autoreset=True)

def mostrarProcessos(listaDeProcessos):
    print(Fore.GREEN + Style.BRIGHT + "\n╔════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN  + Style.BRIGHT +   "║                  DASHBOARD DE PROCESSOS (RETRO)            ║")
    print(Fore.GREEN + Style.BRIGHT +   "╚════════════════════════════════════════════════════════════╝\n")

    for p in listaDeProcessos:
        print(Fore.YELLOW + Style.BRIGHT + str(p))
        print(Fore.MAGENTA + "-" * 60)
