from rich.table import Table
from rich.console import Console

console = Console()

table = Table(title="Planetas do Sistema Solar")

table.add_column("Nome", style="cyan")
table.add_column("Ordem", style="magenta")
table.add_column("Massa (10^24 kg)", justify="right")

table.add_row("Terra", "3", "5.97")
table.add_row("Marte", "4", "0.642")
table.add_row("Júpiter", "5", "1898")

console.print(table)
