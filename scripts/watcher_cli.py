import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import termios
import tty
from datetime import datetime

import typer
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from wallet_monitor.whale_monitor.formatter import (
    get_direction,
    get_leverage_text,
    get_liq_text,
    get_long_short_bar,
    get_position_row,
)
from wallet_monitor.whale_monitor.models import COMMON_COINS, CST, SORT_CONFIG, MonitorState
from wallet_monitor.whale_monitor.monitor import WhaleMonitor

app = typer.Typer(help="Hyperliquid 巨鲸持仓监控 TUI")
console = Console()


def build_header(state: dict) -> Panel:
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    sort_key = state.get("sortKey", "value")
    sort_reverse = state.get("sortReverse", True)
    sort_label = SORT_CONFIG.get(sort_key, ("", ""))[1]
    arrow = "↓" if sort_reverse else "↑"
    coin = state.get("coin", "BTC")
    text = Text()
    text.append(f"  🐋 Whale Monitor — {coin}", style="bold cyan")
    text.append(f"        Sort: {sort_label} {arrow}    {now} CST", style="dim")
    return Panel(text, style="bold", box=box.DOUBLE)


def build_stats(state: dict) -> Panel:
    stats = state.get("stats", {})
    long_count = stats.get("longCount", 0)
    short_count = stats.get("shortCount", 0)
    bar = get_long_short_bar(long_count, short_count)

    text = Text()
    if bar.get("long_count") is not None:
        text.append(f"  Long: {bar['long_count']}  ")
        text.append("█" * bar["long_bars"], style="green")
        text.append("░" * bar["short_bars"], style="red")
        text.append(f"  Short: {bar['short_count']}")
        text.append("\n")
        text.append(f"  Long: {bar['long_pct']:.1f}%")
        text.append(" " * (bar["width"] + 14))
        text.append(f"Short: {bar['short_pct']:.1f}%")
    else:
        text.append(f"  {bar['text']}", style="dim")

    text.append("\n\n")
    text.append("  24h Liquidation: ", style="bold")
    text.append("N/A", style="dim")
    text.append(" (接口暂不可用)", style="dim")
    return Panel(text, title="[bold]📊 Market Stats[/bold]", box=box.ROUNDED)


def build_positions_table(state: dict) -> Panel:
    table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold magenta",
        expand=True,
        pad_edge=False,
    )

    table.add_column("Address", ratio=2, min_width=12)
    table.add_column("Dir", ratio=1, min_width=5, justify="center")
    table.add_column("Value", ratio=2, min_width=10, justify="right")
    table.add_column("uPnL", ratio=2, min_width=10, justify="right")
    table.add_column("Margin", ratio=2, min_width=10, justify="right")
    table.add_column("Entry", ratio=2, min_width=10, justify="right")
    table.add_column("Liq Price", ratio=2, min_width=10, justify="right")
    table.add_column("Lev", ratio=1, min_width=5, justify="center")
    table.add_column("Mode", ratio=1, min_width=6, justify="center")
    table.add_column("Time", ratio=2, min_width=10, justify="center")

    positions = state.get("positions", [])

    for row in positions:
        dir_style = "bold green" if row["direction_level"] == "green" else "bold red" if row["direction_level"] == "red" else ""
        upnl_style = "green" if row["upnl_positive"] else "red"
        lev_style = "bold red" if row["leverage_level"] == "danger" else "yellow" if row["leverage_level"] == "warn" else ""
        liq_style = "bold red blink" if row["liq_level"] == "danger" else ""

        table.add_row(
            Text(row["address"], style="cyan"),
            Text(row["direction"], style=dir_style),
            Text(row["value"], style="white"),
            Text(row["upnl"], style=upnl_style),
            Text(row["margin"], style="white"),
            Text(row["entry"], style="white"),
            Text(row["liq_price"], style=liq_style) if liq_style else Text(row["liq_price"]),
            Text(row["leverage"], style=lev_style),
            Text(row["mode"], style="dim"),
            Text(row["time"], style="dim"),
        )

    if not positions:
        table.add_row(
            Text("  Waiting for data...", style="dim italic"),
            Text(""), Text(""), Text(""), Text(""),
            Text(""), Text(""), Text(""), Text(""), Text(""),
        )

    title = f"[bold]🐋 Whale Positions ({len(positions)})[/bold]"
    return Panel(table, title=title, box=box.ROUNDED)


def build_footer(state: dict) -> Panel:
    last_update = state.get("lastUpdate", "--:--:--")
    text = Text()
    text.append("  v", style="bold cyan")
    text.append(":Sort Value  ", style="dim")
    text.append("u", style="bold cyan")
    text.append(":Sort uPnL  ", style="dim")
    text.append("l", style="bold cyan")
    text.append(":Sort Leverage  ", style="dim")
    text.append("r", style="bold cyan")
    text.append(":Refresh  ", style="dim")
    text.append("q", style="bold cyan")
    text.append(":Quit", style="dim")
    text.append(f"   |   Updated: {last_update}", style="dim")
    return Panel(text, style="bold", box=box.DOUBLE)


def build_layout(state: dict) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=7),
        Layout(name="positions", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["header"].update(build_header(state))
    layout["stats"].update(build_stats(state))
    layout["positions"].update(build_positions_table(state))
    layout["footer"].update(build_footer(state))
    return layout


class KeyReader:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = None
        self.is_tty = sys.stdin.isatty()

    def __enter__(self):
        if self.is_tty:
            try:
                self.old_settings = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
            except termios.error:
                self.old_settings = None
        return self

    def __exit__(self, *args):
        if self.old_settings:
            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
            except termios.error:
                pass

    def read_key(self) -> str | None:
        if not self.is_tty:
            return None
        import select
        try:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                return sys.stdin.read(1)
        except Exception:
            pass
        return None


def select_coin() -> str | None:
    console.print("\n[bold cyan]常用币种:[/bold cyan]")
    console.print(f"  {', '.join(COMMON_COINS)}\n")

    coins = WhaleMonitor.available_coins()
    if coins:
        console.print(f"[dim]共 {len(coins)} 个可用币种（使用 -l 查看完整列表）[/dim]\n")

    try:
        symbol = input("请输入币种 [默认: BTC]: ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        return None

    if not symbol:
        return "BTC"

    if coins and symbol not in coins:
        console.print(f"[yellow]⚠ '{symbol}' 不在可用列表中，仍然尝试监控...[/yellow]")

    return symbol


@app.command()
def main(
    symbol: str = typer.Option(None, "-s", "--symbol", help="指定币种（如 BTC、ETH、SOL）"),
    refresh: int = typer.Option(30, "-r", "--refresh", help="刷新间隔（秒）"),
    list_coins: bool = typer.Option(False, "-l", "--list-coins", help="列出所有可用币种"),
    sort: str = typer.Option("value", "-S", "--sort", help="初始排序字段: value / upnl / leverage"),
):
    if list_coins:
        console.print("[bold cyan]正在获取可用币种列表...[/bold cyan]")
        coins = WhaleMonitor.available_coins()
        if not coins:
            console.print("[red]获取币种列表失败[/red]")
            raise typer.Exit(1)
        console.print(f"\n[bold green]共 {len(coins)} 个可用永续合约币种:[/bold green]\n")
        for i in range(0, len(coins), 10):
            chunk = coins[i : i + 10]
            console.print("  " + ", ".join(chunk))
        console.print()
        raise typer.Exit(0)

    if sort not in SORT_CONFIG:
        console.print(f"[red]无效排序字段: {sort}，可选: value / upnl / leverage[/red]")
        raise typer.Exit(1)

    coin = symbol
    if not coin:
        coin = select_coin()
        if not coin:
            raise typer.Exit(0)

    monitor = WhaleMonitor(coin=coin, refresh_interval=refresh, sort_key=sort)
    monitor.fetch_once()

    snapshot = monitor.get_snapshot()
    console.print(f"\n[bold green]🐋 开始监控 {snapshot['coin']}...[/bold green]")
    console.print(f"[dim]刷新间隔: {refresh}秒 | 排序: {SORT_CONFIG[sort][1]} | 按 q 退出[/dim]\n")

    import time
    time.sleep(1)

    monitor.start()

    with Live(
        build_layout(snapshot),
        console=console,
        refresh_per_second=2,
        screen=True,
    ) as live:
        with KeyReader() as kr:
            while True:
                key = None
                try:
                    key = kr.read_key()
                except Exception:
                    pass

                if key:
                    if key in ("q", "Q"):
                        monitor.stop()
                        break
                    elif key in ("r", "R"):
                        monitor.fetch_once()
                    elif key in ("v", "u", "l"):
                        monitor.set_sort(key)

                snapshot = monitor.get_snapshot()
                live.update(build_layout(snapshot))
                time.sleep(0.5)

    console.print("[bold cyan]👋 监控已停止[/bold cyan]")


if __name__ == "__main__":
    app()
