from model import listaProcessos
from view import iniciaDash

def executarDashboard():
    processos = listaProcessos()
#    iniciaDash(processos)

    # Teste de gráfico
    from view import testes
    testes()