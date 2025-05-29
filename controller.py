from model import SystemMonitorConsoleModel 
from view import render_dashboard          

# Instancia o modelo uma única vez no início
# Isso garante que _last_cpu_total e _last_cpu_idle persistam entre as atualizações
monitor_model = SystemMonitorConsoleModel()

def executarDashboard():
    # 1. O Controller pede os dados completos ao Modelo
    dashboard_data = monitor_model.get_all_data()

    # 2. O Controller passa os dados para a função da View para renderizar
    render_dashboard(dashboard_data)