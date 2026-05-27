import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import termios
import tty
from datetime import datetime

import typer
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from wallet_monitor.whale_monitor.formatter import (
    format_price,
    format_usd,
    format_usd_unsigned,
    get_risk_summary,
)
from wallet_monitor.whale_monitor.models import COMMON_COINS, CST, SORT_CONFIG
from wallet_monitor.whale_monitor.monitor import WhaleMonitor

if sys.platform == "win32":
    console = Console(force_terminal=True, force_jupyter=False)
else:
    console = Console()

app = typer.Typer(help="Hyperliquid 巨鲸持仓监控 TUI")


def pct_bar(long_count: int, short_count: int, width: int = 24) -> Text:
    total = long_count + short_count
    if total == 0:
        return Text("─" * width, style="dim")
    long_pct = long_count / total
    long_width = round(long_pct * width)
    short_width = width - long_width
    bar = Text()
    bar.append("▓" * long_width, style="bold green")
    bar.append("▓" * short_width, style="bold red")
    return bar


def build_header(coin: str, refresh_interval: int, last_update: str) -> Panel:
    title = Text()
    title.append("[HypeWatcher]  ", style="bold cyan")
    title.append(f"[ {coin} ]", style="bold yellow")
    title.append(f"  |  刷新: {refresh_interval}s", style="dim")
    title.append(f"  |  更新: {last_update}", style="dim")
    return Panel(Align.center(title), style="cyan", height=3)


def build_stats(coin: str, state: dict) -> Panel:
    stats = state.get("stats", {})
    risk = state.get("risk", {})
    long_count = stats.get("longCount", 0)
    short_count = stats.get("shortCount", 0)
    total = long_count + short_count
    long_pct = (long_count / total * 100) if total > 0 else 0
    short_pct = 100 - long_pct

    grid = Table.grid(padding=(0, 2))
    grid.add_column(justify="right", style="bold green", min_width=10)
    grid.add_column(justify="center", min_width=28)
    grid.add_column(justify="left", style="bold red", min_width=10)

    grid.add_row(
        f"Long {long_count}",
        pct_bar(long_count, short_count, 28),
        f"{short_count} Short",
    )
    grid.add_row(
        f"{long_pct:.1f}%",
        Text("─" * 28, style="dim"),
        f"{short_pct:.1f}%",
    )

    risk_text = Text()
    at_risk_count = risk.get("at_risk_count", 0)
    at_risk_value = risk.get("at_risk_value_str", "$0")
    high_lev = risk.get("high_lev_count", 0)
    total_pnl = risk.get("total_pnl_str", "$0")
    pnl_val = risk.get("total_pnl", 0)
    lev_dist = risk.get("leverage_dist", {})

    risk_text.append("\n  ⚠ Liq Risk: ", style="bold")
    if at_risk_count > 0:
        risk_text.append(f"{at_risk_count} pos ({at_risk_value})", style="bold red")
    else:
        risk_text.append("None", style="green")
    risk_text.append("   ")
    risk_text.append("🔴 ≥20x: ", style="bold")
    risk_text.append(str(high_lev), style="bold red" if high_lev > 0 else "white")
    risk_text.append("   ")
    risk_text.append("Σ PnL: ", style="bold")
    risk_text.append(total_pnl, style="green" if pnl_val >= 0 else "red")

    if lev_dist:
        risk_text.append("\n  Lev: ", style="dim")
        for bucket, count in lev_dist.items():
            risk_text.append(f"{bucket}:{count}  ", style="dim")

    return Panel(
        Align.center(Group(Text("\n"), grid, risk_text)),
        title=f"[bold yellow][STATS] {coin} 多空比例 & 风险[/bold yellow]",
        border_style="yellow",
        height=9,
    )


def build_positions_table(positions: list[dict], coin: str) -> Panel:
    if not positions:
        return Panel(
            Align.center(Text("加载数据中...", style="dim yellow")),
            title=f"[bold cyan][WHALES] {coin} 鲸鱼持仓列表[/bold cyan]",
            border_style="cyan",
        )

    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.SIMPLE_HEAVY,
        border_style="bright_black",
        row_styles=["", "dim"],
        expand=True,
        show_edge=False,
    )

    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("地址", min_width=14)
    table.add_column("方向", width=5, justify="center")
    table.add_column("持仓价值", min_width=10, justify="right")
    table.add_column("未实现盈亏", min_width=12, justify="right")
    table.add_column("保证金", min_width=10, justify="right")
    table.add_column("开仓价", min_width=10, justify="right")
    table.add_column("清算价", min_width=10, justify="right")
    table.add_column("杠杆", width=5, justify="center")
    table.add_column("时间", min_width=10, justify="center")

    for idx, row in enumerate(positions[:50], 1):
        dir_text = row["direction"]
        dir_level = row["direction_level"]
        if dir_level == "green":
            dir_cell = Text("多 ▲", style="bold green")
        elif dir_level == "red":
            dir_cell = Text("空 ▼", style="bold red")
        else:
            dir_cell = Text("─", style="dim")

        upnl_raw = row.get("upnl_raw", 0)
        if upnl_raw > 0:
            upnl_cell = Text(f"+{row['upnl']}", style="bold green")
        elif upnl_raw < 0:
            upnl_cell = Text(row["upnl"], style="bold red")
        else:
            upnl_cell = Text(row["upnl"], style="dim")

        liq_level = row.get("liq_level", "normal")
        liq_cell = Text(row["liq_price"], style="bold red blink" if liq_level == "danger" else "")

        lev_level = row.get("leverage_level", "normal")
        if lev_level == "danger":
            lev_cell = Text(row["leverage"], style="bold red")
        elif lev_level == "warn":
            lev_cell = Text(row["leverage"], style="yellow")
        else:
            lev_cell = Text(row["leverage"])

        table.add_row(
            str(idx),
            Text(row["address"], style="cyan"),
            dir_cell,
            Text(row["value"]),
            upnl_cell,
            Text(row["margin"]),
            Text(row["entry"]),
            liq_cell,
            lev_cell,
            Text(row["time"], style="dim"),
        )

    total_long = sum(r.get("value_raw", 0) for r in positions if r.get("direction_level") == "green")
    total_short = sum(r.get("value_raw", 0) for r in positions if r.get("direction_level") == "red")
    subtitle = (
        f"共 {len(positions)} 条 · "
        f"多头总值: [green]{format_usd_unsigned(total_long)}[/green] · "
        f"空头总值: [red]{format_usd_unsigned(total_short)}[/red]"
    )

    return Panel(
        table,
        title=f"[bold cyan][WHALES] {coin} 鲸鱼持仓列表[/bold cyan]",
        subtitle=subtitle,
        border_style="cyan",
    )


def build_footer() -> Panel:
    hint = Text()
    hint.append("q", style="bold cyan")
    hint.append(":Quit  ", style="dim")
    hint.append("r", style="bold cyan")
    hint.append(":Refresh  ", style="dim")
    hint.append("v", style="bold cyan")
    hint.append(":Sort Value  ", style="dim")
    hint.append("u", style="bold cyan")
    hint.append(":Sort uPnL  ", style="dim")
    hint.append("l", style="bold cyan")
    hint.append(":Sort Leverage", style="dim")
    return Panel(Align.center(hint), style="bright_black", height=3)


def build_layout(coin: str, refresh_interval: int, state: dict) -> Layout:
    last_update = state.get("lastUpdate", "--:--:--")
    positions = state.get("positions", [])

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=9),
        Layout(name="positions", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["header"].update(build_header(coin, refresh_interval, last_update))
    layout["stats"].update(build_stats(coin, state))
    layout["positions"].update(build_positions_table(positions, coin))
    layout["footer"].update(build_footer())
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
    console.print("\n[bold cyan]正在获取可用币种列表...[/bold cyan]")
    coins = WhaleMonitor.available_coins()

    console.print("\n[bold yellow]常用币种:[/bold yellow]")
    cols = [Text(c, style="bold green" if c in coins else "dim") for c in COMMON_COINS]
    console.print(Columns(cols, padding=(0, 2)))

    if coins:
        console.print(f"\n[dim]共 {len(coins)} 个可用币种（使用 -l 查看完整列表）[/dim]")

    choice = Prompt.ask("[bold cyan]请输入币种[/bold cyan]", default="BTC").strip().upper()

    if coins and choice not in coins:
        console.print(f"[yellow]⚠ '{choice}' 不在可用列表中，仍然尝试监控...[/yellow]")

    return choice


@app.command()
def main(
    symbol: str = typer.Option(None, "-s", "--symbol", help="指定币种（如 BTC、ETH、SOL）"),
    refresh: int = typer.Option(30, "-r", "--refresh", help="刷新间隔（秒）"),
    list_coins: bool = typer.Option(False, "-l", "--list-coins", help="列出所有可用币种"),
    sort: str = typer.Option("value", "-S", "--sort", help="初始排序字段: value / upnl / leverage"),
):
    console.print(
        Panel(
            Text.assemble(
                Text("[HypeWatcher]\n", style="bold cyan"),
                Text("Hyperliquid 鲸鱼持仓实时监控\n", style="dim"),
                Text("数据来源: hyperbot.network/whales", style="dim"),
            ),
            border_style="cyan",
            expand=False,
        )
    )

    if list_coins:
        console.print("\n[bold cyan]正在获取可用币种列表...[/bold cyan]")
        coins = WhaleMonitor.available_coins()
        if not coins:
            console.print("[red]获取币种列表失败[/red]")
            raise typer.Exit(1)
        console.print(f"\n[bold green]共 {len(coins)} 个可用永续合约币种:[/bold green]")
        cols = [Text(c, style="green") for c in coins]
        console.print(Columns(cols, padding=(0, 1)))
        console.print()
        raise typer.Exit(0)

    if sort not in SORT_CONFIG:
        console.print(f"[red]无效排序字段: {sort}，可选: value / upnl / leverage[/red]")
        raise typer.Exit(1)

    coin = symbol.strip().upper() if symbol else select_coin()

    monitor = WhaleMonitor(coin=coin, refresh_interval=refresh, sort_key=sort)
    monitor.fetch_once()

    snapshot = monitor.get_snapshot()
    console.print(
        Panel(
            Align.center(
                Text.assemble(
                    Text("启动中...\n", style="bold cyan"),
                    Text("监控: ", style="dim"),
                    Text(coin, style="bold yellow"),
                    Text(f"  |  刷新: {refresh}s  |  排序: {SORT_CONFIG[sort][1]}", style="dim"),
                )
            ),
            border_style="cyan",
        )
    )

    import time
    time.sleep(1)

    monitor.start()

    with Live(
        build_layout(coin, refresh, snapshot),
        console=console,
        refresh_per_second=1,
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
                live.update(build_layout(coin, refresh, snapshot))
                time.sleep(0.5)

    console.print("\n[bold yellow]监控已停止[/bold yellow]")


if __name__ == "__main__":
    app()
