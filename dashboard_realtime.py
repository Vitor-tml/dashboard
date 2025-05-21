import curses
import time
from model import listaProcessos, uso_cpu_percent, info_memoria, total_processos_threads

def format_process(p):
    try:
        return (f"PID={p.pid} | Nome={p.name} | Estado={p.estado} | "
                f"PPID={p.ppid} | UID={p.uid} | Threads={p.threads} | "
                f"CPU User={p.cpuUserTick} | CPU Kernel={p.cpuSysTick} | "
                f"RAM={p.memoriaKB} KB | Usuário={p.user}")
    except Exception:
        return None

def draw_dashboard(stdscr):
    curses.curs_set(0)  # Esconde o cursor
    stdscr.nodelay(1)   # Modo não-bloqueante para getch()
    delay = 5  # Atualiza a cada 5 segundos (conforme especificação)
    
    while True:
        stdscr.clear()
        
        # Cabeçalho
        stdscr.addstr(0, 0, "╔════════════════════════════════════════════════════╗")
        stdscr.addstr(1, 0, "║ DASHBOARD DE PROCESSOS (TEMPO REAL)               ║")
        stdscr.addstr(2, 0, "╚════════════════════════════════════════════════════╝")
        
        # Informações globais do sistema
        uso, ocioso = uso_cpu_percent()
        mem = info_memoria()
        total_proc, total_threads = total_processos_threads()
        
        stdscr.addstr(4, 0, f"Uso da CPU: {uso:.2f}% | CPU ociosa: {ocioso:.2f}%")
        stdscr.addstr(5, 0, f"Total Processos: {total_proc} | Total Threads: {total_threads}")
        stdscr.addstr(6, 0, f"Memória Usada: {mem['mem_usada_percent']:.2f}% | Memória Livre: {mem['mem_livre_percent']:.2f}%")
        stdscr.addstr(7, 0, "=" * (curses.COLS - 1))
        
        # Lista de processos
        processes = listaProcessos()
        processes.sort(key=lambda p: p.pid)
        
        row = 9
        stdscr.addstr(8, 0, "PROCESSOS:")
        for p in processes:
            info = format_process(p)
            if info:
                try:
                    # Limita a string ao tamanho da tela
                    stdscr.addstr(row, 0, info[:curses.COLS - 1])
                    row += 1
                    if row >= curses.LINES - 1:
                        break
                except curses.error:
                    pass  # Ignora erros ao escrever fora da tela
        
        stdscr.refresh()
        
        # Espera pela tecla 'q' para sair ou atualiza após o delay
        for _ in range(delay * 10):
            time.sleep(0.1)
            key = stdscr.getch()
            if key == ord('q'):
                return

if __name__ == "__main__":
    curses.wrapper(draw_dashboard)