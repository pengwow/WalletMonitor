#!/usr/bin/env python3
"""
WalletMonitor CLI – comprehensive command-line interface.

Provides wallet management, transaction queries, alert management,
whale monitoring, API server, status, and export commands.

Run standalone:
    cd /opt/data/WalletMonitor && .venv/bin/python3 scripts/cli.py <command>
"""

import os
import sys
import json
import csv
import io
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Bootstrap – ensure the project root is on sys.path so that
# ``wallet_monitor.*`` is importable when running this script directly.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ---------------------------------------------------------------------------
# Lazy imports (after sys.path is fixed)
# ---------------------------------------------------------------------------
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
console = Console()
app = typer.Typer(
    help="WalletMonitor – 多链钱包监控、交易追踪与巨鲸告警",
    no_args_is_help=True,
    add_completion=False,
)

# Sub-command groups
wallet_app = typer.Typer(help="管理监控钱包", no_args_is_help=True)
tx_app = typer.Typer(help="查询和同步交易", no_args_is_help=True)
alert_app = typer.Typer(help="管理告警和告警规则", no_args_is_help=True)
alert_rules_app = typer.Typer(help="管理告警规则", no_args_is_help=True)
monitor_app = typer.Typer(help="巨鲸/市场监控 (Hyperliquid)", no_args_is_help=True)

app.add_typer(wallet_app, name="wallet")
app.add_typer(tx_app, name="tx")
app.add_typer(alert_app, name="alert")
alert_app.add_typer(alert_rules_app, name="rules")
app.add_typer(monitor_app, name="monitor")


# ===================================================================
# Helpers
# ===================================================================

def _get_storage():
    """Return a DataStorage instance with the default DB path."""
    from wallet_monitor.data.storage import DataStorage
    db_path = os.path.join(_PROJECT_ROOT, "wallet_monitor.db")
    return DataStorage(db_path=db_path)


def _print_json(data):
    """Pretty-print JSON to stdout."""
    console.print_json(json.dumps(data, default=str, ensure_ascii=False))


def _risk_style(level: str):
    """Return a Rich style string for a risk level."""
    m = {"high": "bold red", "medium": "yellow", "low": "green", "critical": "bold red blink"}
    return m.get(level, "")


# ===================================================================
# wallet commands
# ===================================================================

@wallet_app.command("add")
def wallet_add(
    address: str = typer.Argument(..., help="要监控的钱包地址"),
    chain: str = typer.Argument(..., help="区块链类型 (ethereum, bsc, polygon, solana)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="钱包名称"),
    desc: Optional[str] = typer.Option(None, "--desc", "-d", help="描述/备注"),
):
    """添加钱包到监控列表."""
    storage = _get_storage()
    ok = storage.add_wallet(address=address, chain=chain.lower(), name=name, description=desc)
    if ok:
        console.print(f"[green]✓[/green] Wallet [cyan]{address}[/cyan] added on [bold]{chain}[/bold].")
    else:
        console.print("[red]✗[/red] Failed to add wallet. It may already exist.", err=True)
        raise typer.Exit(1)


@wallet_app.command("list")
def wallet_list(
    chain: Optional[str] = typer.Option(None, "--chain", "-c", help="按链筛选"),
    as_json: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式输出"),
):
    """列出所有监控钱包."""
    storage = _get_storage()
    wallets = storage.get_wallets(chain=chain)
    if as_json:
        _print_json(wallets)
        return
    if not wallets:
        console.print("[dim]No wallets found.[/dim]")
        return
    table = Table(title="Watched Wallets", box=box.ROUNDED, show_lines=False)
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Address", style="cyan", min_width=20)
    table.add_column("Chain", style="bold", width=10)
    table.add_column("Name", min_width=12)
    table.add_column("Description", min_width=16)
    table.add_column("Created", style="dim", width=19)
    for w in wallets:
        table.add_row(
            str(w.get("id", "")),
            w.get("address", ""),
            w.get("chain", ""),
            w.get("name") or "[dim]—[/dim]",
            w.get("description") or "[dim]—[/dim]",
            str(w.get("created_at", "")),
        )
    console.print(table)
    console.print(f"\n[dim]{len(wallets)} wallet(s) total.[/dim]")


@wallet_app.command("remove")
def wallet_remove(
    id: int = typer.Argument(..., help="要停用的钱包 ID"),
):
    """停用（软删除）监控钱包."""
    storage = _get_storage()
    ok = storage.delete_wallet(id)
    if ok:
        console.print(f"[green]✓[/green] Wallet #{id} deactivated.")
    else:
        console.print(f"[red]✗[/red] Wallet #{id} not found.", err=True)
        raise typer.Exit(1)


@wallet_app.command("balance")
def wallet_balance(
    address: str = typer.Argument(..., help="钱包地址"),
    chain: str = typer.Argument(..., help="区块链名称"),
):
    """查询钱包原生代币余额."""
    from wallet_monitor.blockchain.factory import BlockchainFactory
    client = BlockchainFactory.create_blockchain(chain.lower())
    if client is None:
        console.print(f"[red]✗[/red] Unsupported chain: {chain}", err=True)
        raise typer.Exit(1)
    try:
        balance = client.get_balance(address)
        console.print(
            Panel(
                f"[bold]{balance:,.6f}[/bold] {chain.upper()}",
                title=f"Balance – {address}",
                border_style="cyan",
            )
        )
    except Exception as exc:
        console.print(f"[red]✗[/red] Failed to fetch balance: {exc}", err=True)
        raise typer.Exit(1)


# ===================================================================
# tx commands
# ===================================================================

@tx_app.command("list")
def tx_list(
    wallet: Optional[str] = typer.Option(None, "--wallet", "-w", help="按钱包地址筛选"),
    chain: Optional[str] = typer.Option(None, "--chain", "-c", help="按链筛选"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回最大行数"),
    as_json: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式输出"),
):
    """列出已存储的交易."""
    storage = _get_storage()
    txs = storage.get_transactions(wallet_address=wallet, chain=chain, limit=limit)
    if as_json:
        _print_json(txs)
        return
    if not txs:
        console.print("[dim]No transactions found.[/dim]")
        return
    table = Table(title="Transactions", box=box.ROUNDED, show_lines=False)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Hash", style="cyan", min_width=16, no_wrap=True)
    table.add_column("Wallet", min_width=16, no_wrap=True)
    table.add_column("Chain", style="bold", width=8)
    table.add_column("Amount", justify="right", width=14)
    table.add_column("Status", width=10)
    table.add_column("Risk", width=8)
    table.add_column("Timestamp", style="dim", width=19)
    for idx, tx in enumerate(txs, 1):
        risk = tx.get("risk_level", "low")
        table.add_row(
            str(idx),
            (tx.get("hash") or "")[:16] + "…",
            (tx.get("wallet_address") or "")[:16],
            tx.get("chain", ""),
            f"{tx.get('amount', 0):,.4f}",
            tx.get("status", ""),
            Text(risk, style=_risk_style(risk)),
            str(tx.get("timestamp", "")),
        )
    console.print(table)
    console.print(f"\n[dim]{len(txs)} transaction(s) shown (limit={limit}).[/dim]")


@tx_app.command("sync")
def tx_sync(
    address: str = typer.Argument(..., help="要同步的钱包地址"),
    chain: str = typer.Argument(..., help="区块链名称"),
    limit: int = typer.Option(50, "--limit", "-l", help="获取最大交易数"),
):
    """从链上获取最近交易并存储到本地."""
    from wallet_monitor.blockchain.factory import BlockchainFactory
    storage = _get_storage()
    client = BlockchainFactory.create_blockchain(chain.lower())
    if client is None:
        console.print(f"[red]✗[/red] Unsupported chain: {chain}", err=True)
        raise typer.Exit(1)
    console.print(f"[cyan]Fetching transactions for {address} on {chain}…[/cyan]")
    try:
        raw_txs = client.get_transactions(address, limit=limit)
    except Exception as exc:
        console.print(f"[red]✗[/red] RPC error: {exc}", err=True)
        raise typer.Exit(1)

    stored = 0
    for raw in raw_txs:
        tx = {
            "hash": raw.get("hash"),
            "wallet_address": address,
            "chain": chain.lower(),
            "from_address": raw.get("from"),
            "to_address": raw.get("to"),
            "amount": int(raw.get("value", "0x0"), 16) / 1e18 if isinstance(raw.get("value"), str) else 0,
            "status": "confirmed" if raw.get("blockNumber") else "pending",
            "timestamp": int(raw.get("timeStamp", 0), 16) if isinstance(raw.get("timeStamp"), str) and raw["timeStamp"].startswith("0x") else raw.get("timeStamp"),
            "block_number": int(raw.get("blockNumber", "0x0"), 16) if isinstance(raw.get("blockNumber"), str) else raw.get("blockNumber"),
            "gas_used": int(raw.get("gasUsed", "0x0"), 16) if isinstance(raw.get("gasUsed"), str) else raw.get("gasUsed"),
            "gas_price": int(raw.get("gasPrice", "0x0"), 16) if isinstance(raw.get("gasPrice"), str) else raw.get("gasPrice"),
        }
        if storage.add_transaction(tx):
            stored += 1
    console.print(f"[green]✓[/green] Synced {stored}/{len(raw_txs)} transactions.")


@tx_app.command("show")
def tx_show(
    hash: str = typer.Argument(..., help="交易哈希"),
):
    """从本地数据库查看单笔交易详情."""
    storage = _get_storage()
    txs = storage.get_transactions(limit=99999)
    tx = next((t for t in txs if t.get("hash") == hash), None)
    if tx is None:
        console.print(f"[red]✗[/red] Transaction {hash} not found locally.", err=True)
        raise typer.Exit(1)
    if console.is_interactive:
        _print_json(tx)
    else:
        _print_json(tx)


# ===================================================================
# alert commands
# ===================================================================

@alert_app.command("list")
def alert_list(
    wallet: Optional[str] = typer.Option(None, "--wallet", "-w", help="按钱包地址筛选"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="按状态筛选 (pending, resolved)"),
    as_json: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式输出"),
):
    """列出告警."""
    storage = _get_storage()
    alerts = storage.get_alerts(wallet_address=wallet, limit=200)
    if status:
        alerts = [a for a in alerts if a.get("status") == status]
    if as_json:
        _print_json(alerts)
        return
    if not alerts:
        console.print("[dim]No alerts found.[/dim]")
        return
    table = Table(title="Alerts", box=box.ROUNDED, show_lines=False)
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Type", style="bold", width=14)
    table.add_column("Wallet", min_width=16, no_wrap=True)
    table.add_column("Chain", width=8)
    table.add_column("Risk", width=8)
    table.add_column("Status", width=10)
    table.add_column("Message", min_width=24)
    table.add_column("Created", style="dim", width=19)
    for a in alerts:
        risk = a.get("risk_level", "low")
        st = a.get("status", "")
        st_style = "green" if st == "resolved" else "yellow"
        table.add_row(
            str(a.get("id", "")),
            a.get("alert_type", ""),
            (a.get("wallet_address") or "")[:16],
            a.get("chain", ""),
            Text(risk, style=_risk_style(risk)),
            Text(st, style=st_style),
            (a.get("message") or "")[:48],
            str(a.get("created_at", "")),
        )
    console.print(table)
    console.print(f"\n[dim]{len(alerts)} alert(s) total.[/dim]")


@alert_app.command("resolve")
def alert_resolve(
    id: int = typer.Argument(..., help="要解决的告警 ID"),
):
    """将告警标记为已解决."""
    storage = _get_storage()
    ok = storage.resolve_alert(id)
    if ok:
        console.print(f"[green]✓[/green] Alert #{id} resolved.")
    else:
        console.print(f"[red]✗[/red] Alert #{id} not found.", err=True)
        raise typer.Exit(1)


# --- alert rules sub-commands ---

@alert_rules_app.command("list")
def alert_rules_list(
    as_json: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式输出"),
):
    """列出所有告警规则."""
    storage = _get_storage()
    rules = storage.get_alert_rules(enabled_only=False)
    if as_json:
        _print_json(rules)
        return
    if not rules:
        console.print("[dim]No alert rules defined.[/dim]")
        return
    table = Table(title="Alert Rules", box=box.ROUNDED, show_lines=False)
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Name", style="bold cyan", min_width=16)
    table.add_column("Type", width=14)
    table.add_column("Threshold", justify="right", width=12)
    table.add_column("Enabled", width=8, justify="center")
    table.add_column("Description", min_width=20)
    for r in rules:
        enabled = "✓" if r.get("enabled") else "✗"
        e_style = "green" if r.get("enabled") else "red"
        table.add_row(
            str(r.get("id", "")),
            r.get("name", ""),
            r.get("rule_type", ""),
            str(r.get("threshold", "")),
            Text(enabled, style=e_style),
            r.get("description") or "[dim]—[/dim]",
        )
    console.print(table)
    console.print(f"\n[dim]{len(rules)} rule(s) total.[/dim]")


@alert_rules_app.command("add")
def alert_rules_add(
    name: str = typer.Argument(..., help="规则名称"),
    type: str = typer.Argument(..., help="规则类型 (transaction, balance, contract, anomaly)"),
    threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="数值阈值"),
    desc: Optional[str] = typer.Option(None, "--desc", "-d", help="描述"),
):
    """添加新告警规则."""
    storage = _get_storage()
    rule = {
        "name": name,
        "rule_type": type.lower(),
        "threshold": threshold,
        "description": desc,
        "enabled": True,
    }
    ok = storage.add_alert_rule(rule)
    if ok:
        console.print(f"[green]✓[/green] Alert rule [cyan]{name}[/cyan] added.")
    else:
        console.print("[red]✗[/red] Failed to add alert rule.", err=True)
        raise typer.Exit(1)


@alert_rules_app.command("delete")
def alert_rules_delete(
    id: int = typer.Argument(..., help="要删除的规则 ID"),
):
    """删除告警规则."""
    storage = _get_storage()
    ok = storage.delete_alert_rule(id)
    if ok:
        console.print(f"[green]✓[/green] Alert rule #{id} deleted.")
    else:
        console.print(f"[red]✗[/red] Alert rule #{id} not found.", err=True)
        raise typer.Exit(1)


# ===================================================================
# monitor commands
# ===================================================================

@monitor_app.command("start")
def monitor_start(
    coin: str = typer.Option(..., "--coin", "-c", help="币种符号 (BTC, ETH, …)"),
    interval: int = typer.Option(30, "--interval", "-i", help="刷新间隔（秒）"),
):
    """在终端启动巨鲸监控 (Hyperliquid)."""
    from wallet_monitor.whale_monitor.monitor import WhaleMonitor
    from wallet_monitor.whale_monitor.formatter import format_usd, format_usd_unsigned, get_risk_summary

    coin = coin.upper()
    console.print(Panel(
        f"[bold cyan]Whale Monitor[/bold cyan]  –  [yellow]{coin}[/yellow]  –  interval {interval}s",
        border_style="cyan",
    ))

    monitor = WhaleMonitor(coin=coin, refresh_interval=interval)
    console.print("[cyan]Fetching initial data…[/cyan]")
    if not monitor.fetch_once():
        console.print("[red]✗[/red] Failed to fetch data. Check network / RPC.", err=True)
        raise typer.Exit(1)
    monitor.start()

    try:
        while True:
            snap = monitor.get_snapshot()
            stats = snap.get("stats", {})
            risk = snap.get("risk", {})
            positions = snap.get("positions", [])

            long_c = stats.get("longCount", 0)
            short_c = stats.get("shortCount", 0)
            total = long_c + short_c
            long_pct = (long_c / total * 100) if total else 0

            risk_summary = get_risk_summary([])
            at_risk = risk.get("at_risk_count", 0)
            total_pnl_str = risk.get("total_pnl_str", "$0")
            total_pnl = risk.get("total_pnl", 0)

            lines = Text()
            lines.append(f"  Long: {long_c} ({long_pct:.1f}%)    ", style="green")
            lines.append(f"Short: {short_c} ({100 - long_pct:.1f}%)    ", style="red")
            lines.append(f"At Risk: {at_risk}    ", style="yellow" if at_risk else "dim")
            pnl_style = "green" if total_pnl >= 0 else "red"
            lines.append(f"Total PnL: {total_pnl_str}", style=pnl_style)

            console.print(Panel(lines, title=f"[bold]{coin}[/bold] Snapshot", border_style="yellow"))

            if positions:
                tbl = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
                tbl.add_column("#", width=3, justify="right", style="dim")
                tbl.add_column("Address", min_width=14)
                tbl.add_column("Dir", width=4, justify="center")
                tbl.add_column("Value", justify="right", width=12)
                tbl.add_column("uPnL", justify="right", width=12)
                tbl.add_column("Lev", justify="center", width=6)
                for i, pos in enumerate(positions[:20], 1):
                    from wallet_monitor.whale_monitor.formatter import get_direction, get_leverage_text, get_position_row
                    row = get_position_row(pos)
                    dir_text = row["direction"]
                    upnl_style = "green" if row.get("upnl_positive") else "red"
                    lev_style = "bold red" if row["leverage_level"] == "danger" else ("yellow" if row["leverage_level"] == "warn" else "")
                    tbl.add_row(
                        str(i),
                        row["address"],
                        dir_text,
                        row["value"],
                        Text(row["upnl"], style=upnl_style),
                        Text(row["leverage"], style=lev_style),
                    )
                console.print(tbl)

            import time
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor stopped.[/yellow]")
        monitor.stop()


@monitor_app.command("coins")
def monitor_coins():
    """List available coins for whale monitoring."""
    from wallet_monitor.whale_monitor.monitor import WhaleMonitor
    coins = WhaleMonitor.available_coins()
    if not coins:
        console.print("[red]✗[/red] Could not fetch coin list.", err=True)
        raise typer.Exit(1)
    console.print(f"[bold green]Available coins ({len(coins)}):[/bold green]")
    for c in sorted(coins):
        console.print(f"  [cyan]{c}[/cyan]")


# ===================================================================
# serve command
# ===================================================================

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="绑定主机地址"),
    port: int = typer.Option(8000, "--port", "-p", help="绑定端口"),
):
    """启动 WalletMonitor API 服务器."""
    console.print(Panel(
        f"[bold cyan]Starting WalletMonitor API server[/bold cyan]\n"
        f"  Host: [yellow]{host}[/yellow]  Port: [yellow]{port}[/yellow]\n"
        f"  Docs: [link=http://{host}:{port}/docs]http://{host}:{port}/docs[/link]",
        border_style="cyan",
    ))
    try:
        import uvicorn
    except ImportError:
        console.print("[red]✗[/red] uvicorn is not installed. Install with: pip install uvicorn", err=True)
        raise typer.Exit(1)

    uvicorn.run(
        "wallet_monitor.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


# ===================================================================
# status command
# ===================================================================

@app.command()
def status(
    as_json: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式输出"),
):
    """查看 WalletMonitor 系统状态."""
    storage = _get_storage()
    wallets = storage.get_wallets()
    alerts = storage.get_alerts(limit=9999)
    pending_alerts = [a for a in alerts if a.get("status") == "pending"]
    txs = storage.get_transactions(limit=99999)
    rules = storage.get_alert_rules(enabled_only=False)

    try:
        from wallet_monitor.blockchain.factory import BlockchainFactory
        chains = BlockchainFactory.get_supported_chains()
    except Exception:
        chains = ["ethereum", "bsc", "polygon", "solana"]

    try:
        from wallet_monitor.config import settings as _settings
    except Exception:
        _settings = None

    data = {
        "version": "1.2.0",
        "db_path": storage.db_path,
        "wallets_count": len(wallets),
        "transactions_count": len(txs),
        "alerts_total": len(alerts),
        "alerts_pending": len(pending_alerts),
        "alert_rules_count": len(rules),
        "supported_chains": chains,
    }
    if _settings:
        data["api_host"] = _settings.api_host
        data["api_port"] = _settings.api_port
    else:
        data["api_host"] = "0.0.0.0"
        data["api_port"] = 8000
    if as_json:
        _print_json(data)
        return

    table = Table(title="WalletMonitor Status", box=box.ROUNDED, show_lines=False)
    table.add_column("Key", style="bold cyan", min_width=22)
    table.add_column("Value")
    table.add_row("Version", data["version"])
    table.add_row("Database", data["db_path"])
    table.add_row("Wallets", str(data["wallets_count"]))
    table.add_row("Transactions", str(data["transactions_count"]))
    table.add_row("Alerts (total)", str(data["alerts_total"]))
    table.add_row("Alerts (pending)", Text(str(data["alerts_pending"]), style="yellow" if data["alerts_pending"] else "green"))
    table.add_row("Alert Rules", str(data["alert_rules_count"]))
    table.add_row("Supported Chains", ", ".join(data["supported_chains"]))
    table.add_row("API Endpoint", f"http://{data['api_host']}:{data['api_port']}")
    console.print(table)


# ===================================================================
# export command
# ===================================================================

@app.command()
def export(
    fmt: str = typer.Option("json", "--format", "-f", help="导出格式: json 或 csv"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径（默认: stdout）"),
):
    """导出所有钱包、交易和告警数据."""
    storage = _get_storage()
    data = {
        "wallets": storage.get_wallets(),
        "transactions": storage.get_transactions(limit=99999),
        "alerts": storage.get_alerts(limit=99999),
        "alert_rules": storage.get_alert_rules(enabled_only=False),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    fmt = fmt.lower()
    if fmt == "json":
        content = json.dumps(data, default=str, ensure_ascii=False, indent=2)
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        # Wallets section
        writer.writerow(["=== WALLETS ==="])
        writer.writerow(["id", "address", "chain", "name", "description", "is_active", "created_at"])
        for w in data["wallets"]:
            writer.writerow([w.get(k, "") for k in ("id", "address", "chain", "name", "description", "is_active", "created_at")])
        writer.writerow([])
        # Transactions section
        writer.writerow(["=== TRANSACTIONS ==="])
        writer.writerow(["id", "hash", "wallet_address", "chain", "from_address", "to_address", "amount", "status", "timestamp"])
        for tx in data["transactions"]:
            writer.writerow([tx.get(k, "") for k in ("id", "hash", "wallet_address", "chain", "from_address", "to_address", "amount", "status", "timestamp")])
        writer.writerow([])
        # Alerts section
        writer.writerow(["=== ALERTS ==="])
        writer.writerow(["id", "wallet_address", "chain", "alert_type", "message", "risk_level", "status", "created_at"])
        for a in data["alerts"]:
            writer.writerow([a.get(k, "") for k in ("id", "wallet_address", "chain", "alert_type", "message", "risk_level", "status", "created_at")])
        writer.writerow([])
        # Rules section
        writer.writerow(["=== ALERT_RULES ==="])
        writer.writerow(["id", "name", "rule_type", "threshold", "enabled", "description"])
        for r in data["alert_rules"]:
            writer.writerow([r.get(k, "") for k in ("id", "name", "rule_type", "threshold", "enabled", "description")])
        content = buf.getvalue()
    else:
        console.print(f"[red]✗[/red] Unknown format: {fmt}. Use 'json' or 'csv'.", err=True)
        raise typer.Exit(1)

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(content)
        console.print(f"[green]✓[/green] Exported to {output} ({fmt.upper()}, {len(content)} bytes)")
    else:
        console.print(content)


# ===================================================================
# Entry point
# ===================================================================

if __name__ == "__main__":
    app()
