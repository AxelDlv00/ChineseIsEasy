# ╔════════════════════════════════════════════════════════╗
# ║                     Display Class                      ║
# ╚════════════════════════════════════════════════════════╝

# +--------------------------------------------------------+
# | This class handles all terminal output using the Rich  |
# |                        library.                        |
# +--------------------------------------------------------+

import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn
)

BANNER = """                                                                                      
 ,-----.,--.     ,--.                             ,--.       ,------.                        
'  .--./|  ,---. `--',--,--,  ,---.  ,---.  ,---. |  | ,---. |  .---' ,--,--. ,---.,--. ,--. 
|  |    |  .-.  |,--.|      \| .-. :(  .-' | .-. :|  |(  .-' |  `--, ' ,-.  |(  .-' \  '  /  
'  '--'\|  | |  ||  ||  ||  |\   --..-'  `)\   --.|  |.-'  `)|  `---.\ '-'  |.-'  `) \   '   
 `-----'`--' `--'`--'`--''--' `----'`----'  `----'`--'`----' `------' `--`--'`----'.-'  /    
                                                                                   `---'     
"""

class GeneratorDisplay:
    def __init__(self, app_name="AI Content Generator", version="1.0"):
        """Initializes the rich console and app metadata."""
        self.console = Console()
        self.version = version
        self.app_name = app_name

    def print_banner(self):
        """Displays a stylized ASCII banner for the tool."""
        banner_text = BANNER.strip()
        
        self.console.print(Panel(
            Text(banner_text, style="bold magenta"),
            subtitle=f"[bold white]{self.app_name} v{self.version}[/bold white]",
            border_style="magenta",
            expand=False
        ))

    def success(self, message):
        self.console.print(f"[bold green]✔[/bold green] {message}")

    def error(self, message):
        self.console.print(f"[bold red]✘ Error:[/bold red] {message}")

    def info(self, message):
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")
    
    def log(self, message):
        """Logs a standard message to the console using Rich's logging style."""
        self.console.log(message)

    def get_progress(self):
        """Returns a configured Rich progress bar for tracking threads."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style="magenta", complete_style="green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        )