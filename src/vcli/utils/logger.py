from rich.console import Console

console = Console()


def success(message: str) -> None:
    console.print(f"[bold green]v[/bold green] {message}")


def error(message: str) -> None:
    console.print(f"[bold red]x[/bold red] {message}")


def info(message: str) -> None:
    console.print(f"[bold blue]>[/bold blue] {message}")


def warn(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")
