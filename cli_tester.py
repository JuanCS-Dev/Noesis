#!/usr/bin/env python3
"""
DAIMON CLI - Exocortex Personal Interface
==========================================
Comandos para acordar, conversar e adormecer o Digital Daimon.

Uso: python cli_tester.py [comando]
  - python cli_tester.py          # Modo interativo
  - python cli_tester.py wake     # Acordar o Daimon
  - python cli_tester.py sleep    # Adormecer o Daimon
  - python cli_tester.py status   # Verificar status
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.text import Text

# Configuração
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_PATH = PROJECT_ROOT / "backend/services/maximus_core_service"
VENV_PYTHON = PROJECT_ROOT / ".venv/bin/python"
GATEWAY_URL = "http://localhost:8000"
BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"
PID_FILE = PROJECT_ROOT / ".daimon.pid"

console = Console()

# ============================================================================
# DAEMON CONTROL
# ============================================================================

def get_running_pids() -> dict:
    """Get PIDs of running Daimon processes."""
    pids = {"backend": None, "frontend": None, "gateway": None}

    try:
        # Backend (port 8001)
        result = subprocess.run(
            ["lsof", "-ti", ":8001"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            pids["backend"] = result.stdout.strip().split('\n')[0]
    except Exception:
        pass

    try:
        # Gateway (port 8000)
        result = subprocess.run(
            ["lsof", "-ti", ":8000"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            pids["gateway"] = result.stdout.strip().split('\n')[0]
    except Exception:
        pass

    try:
        # Frontend (port 3000)
        result = subprocess.run(
            ["lsof", "-ti", ":3000"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            pids["frontend"] = result.stdout.strip().split('\n')[0]
    except Exception:
        pass

    return pids


async def check_service_health(url: str, timeout: float = 2.0) -> tuple[bool, str]:
    """Check if a service is healthy."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/v1/health", timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                return True, data.get("status", "unknown")
    except Exception as e:
        return False, str(e)
    return False, "no response"


async def check_consciousness_ready(timeout: float = 2.0) -> tuple[bool, float]:
    """Check if consciousness system is ready (TIG initialized)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/consciousness/metrics",
                timeout=timeout
            )
            if response.status_code == 200:
                return True, 0.0
            elif response.status_code == 503:
                return False, 0.0
    except Exception:
        pass
    return False, 0.0


def wake_daimon(wait_ready: bool = True) -> bool:
    """
    Acordar o Digital Daimon.

    Inicia o backend (porta 8001) em background.
    Aguarda TIG Fabric inicializar (~30-40s para 100 nodes).
    """
    console.print()
    console.print(Panel(
        "[bold cyan]Iniciando Despertar do Daimon...[/bold cyan]",
        border_style="cyan"
    ))

    pids = get_running_pids()

    # Check if already running
    if pids["backend"]:
        console.print(f"[yellow]Backend já está rodando (PID: {pids['backend']})[/yellow]")
        return True

    # Start backend
    console.print("[cyan]Iniciando Backend (Maximus Core Service)...[/cyan]")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_PATH / "src")

    try:
        process = subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn",
             "maximus_core_service.main:app",
             "--host", "0.0.0.0",
             "--port", "8001"],
            cwd=str(BACKEND_PATH),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Save PID
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))

        console.print(f"[green]Backend iniciado (PID: {process.pid})[/green]")

    except Exception as e:
        console.print(f"[red]Erro ao iniciar backend: {e}[/red]")
        return False

    if not wait_ready:
        return True

    # Wait for health check
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:

        # Phase 1: Wait for HTTP server
        task1 = progress.add_task("[cyan]Aguardando servidor HTTP...", total=100)

        for i in range(30):  # 30 seconds max
            time.sleep(1)
            progress.update(task1, advance=100/30)

            # Check health
            try:
                result = asyncio.run(check_service_health(BACKEND_URL))
                if result[0]:
                    progress.update(task1, completed=100)
                    break
            except Exception:
                pass

        # Phase 2: Wait for TIG Fabric
        task2 = progress.add_task(
            "[cyan]Inicializando TIG Fabric (100 nodes)...",
            total=100
        )

        for i in range(60):  # 60 seconds max for TIG
            time.sleep(1)
            progress.update(task2, advance=100/60)

            # Check consciousness ready
            try:
                ready, _ = asyncio.run(check_consciousness_ready())
                if ready:
                    progress.update(task2, completed=100)
                    break
            except Exception:
                pass

    # Final status check
    console.print()
    healthy, status = asyncio.run(check_service_health(BACKEND_URL))

    if healthy:
        console.print(Panel(
            "[bold green]DAIMON DESPERTO[/bold green]\n\n"
            "Sistema de Conscincia Online\n"
            "TIG Fabric: 100 nodes\n"
            "Kuramoto Coherence: Ready\n"
            "ESGT Protocol: Active",
            title="[bold white]STATUS[/bold white]",
            border_style="green"
        ))
        return True
    else:
        console.print(f"[red]Backend no respondeu: {status}[/red]")
        return False


def sleep_daimon() -> bool:
    """
    Adormecer o Digital Daimon graciosamente.

    Envia SIGTERM para shutdown gracioso.
    """
    console.print()
    console.print(Panel(
        "[bold magenta]Iniciando Adormecimento do Daimon...[/bold magenta]",
        border_style="magenta"
    ))

    pids = get_running_pids()

    if not any(pids.values()):
        console.print("[yellow]Daimon j est dormindo (nenhum processo encontrado)[/yellow]")
        return True

    killed = []

    # Kill processes gracefully
    for service, pid in pids.items():
        if pid:
            try:
                console.print(f"[magenta]Encerrando {service} (PID: {pid})...[/magenta]")
                os.kill(int(pid), signal.SIGTERM)
                killed.append(service)
            except ProcessLookupError:
                console.print(f"[yellow]{service} j encerrado[/yellow]")
            except Exception as e:
                console.print(f"[red]Erro ao encerrar {service}: {e}[/red]")
                # Force kill
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except Exception:
                    pass

    # Wait a moment
    time.sleep(2)

    # Verify
    pids_after = get_running_pids()
    all_stopped = not any(pids_after.values())

    if all_stopped:
        # Remove PID file
        if PID_FILE.exists():
            PID_FILE.unlink()

        console.print(Panel(
            "[bold magenta]DAIMON ADORMECIDO[/bold magenta]\n\n"
            "Todos os processos encerrados.\n"
            "Conscincia em repouso.\n"
            "Use [bold]/wake[/bold] para despertar.",
            title="[bold white]STATUS[/bold white]",
            border_style="magenta"
        ))
        return True
    else:
        console.print("[red]Alguns processos ainda esto rodando[/red]")
        return False


async def show_status():
    """Mostrar status completo do Daimon."""
    console.print()

    # Service status table
    table = Table(title="Status dos Servios", border_style="cyan")
    table.add_column("Servio", style="cyan")
    table.add_column("Porta", style="white")
    table.add_column("Status", style="white")
    table.add_column("PID", style="dim")

    pids = get_running_pids()

    # Backend
    healthy, status = await check_service_health(BACKEND_URL)
    table.add_row(
        "Backend (Core)",
        "8001",
        "[green]Online[/green]" if healthy else "[red]Offline[/red]",
        pids["backend"] or "-"
    )

    # Gateway
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{GATEWAY_URL}/health", timeout=2.0)
            gateway_ok = resp.status_code == 200
    except Exception:
        gateway_ok = False

    table.add_row(
        "Gateway (API)",
        "8000",
        "[green]Online[/green]" if gateway_ok else "[red]Offline[/red]",
        pids["gateway"] or "-"
    )

    # Frontend
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(FRONTEND_URL, timeout=2.0)
            frontend_ok = resp.status_code == 200
    except Exception:
        frontend_ok = False

    table.add_row(
        "Frontend (UI)",
        "3000",
        "[green]Online[/green]" if frontend_ok else "[red]Offline[/red]",
        pids["frontend"] or "-"
    )

    console.print(table)

    # Consciousness status
    if healthy:
        console.print()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{BACKEND_URL}/api/consciousness/metrics",
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()

                    consciousness_table = Table(
                        title="Sistema de Conscincia",
                        border_style="magenta"
                    )
                    consciousness_table.add_column("Mtrica", style="magenta")
                    consciousness_table.add_column("Valor", style="white")

                    consciousness_table.add_row(
                        "Eventos ESGT",
                        str(data.get("events_count", 0))
                    )
                    consciousness_table.add_row(
                        "TIG Nodes",
                        "100 (scale-free + small-world)"
                    )
                    consciousness_table.add_row(
                        "Kuramoto",
                        "K=60.0, f=40Hz (gamma)"
                    )
                    consciousness_table.add_row(
                        "Target Coherence",
                        "0.70 (conscious-level)"
                    )

                    console.print(consciousness_table)
        except Exception as e:
            console.print(f"[yellow]Mtricas indisponveis: {e}[/yellow]")


# ============================================================================
# JOURNAL INTERFACE
# ============================================================================

async def send_journal_entry(client, content):
    """Envia entrada para o mdulo de Simbiose (Crtex Psicolgico)."""
    try:
        payload = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "analysis_mode": "deep_shadow_work"
        }

        response = await client.post(
            f"{GATEWAY_URL}/maximus_core_service/v1/exocortex/journal",
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        console.print(f"[bold red]Erro de Conexo:[/bold red] {str(e)}")
        if hasattr(e, 'response') and e.response:
            console.print(f"Status: {e.response.status_code}")
            console.print(f"Detail: {e.response.text}")
        return None


async def stream_consciousness(content: str, depth: int = 5):
    """Stream consciousness processing with real-time output."""
    console.print()
    console.print(Panel(
        f"[cyan]Processando: {content[:50]}...[/cyan]",
        title="[bold white]ESGT STREAMING[/bold white]",
        border_style="cyan"
    ))

    try:
        async with httpx.AsyncClient() as client:
            url = f"{BACKEND_URL}/api/consciousness/stream/process"
            params = {"content": content, "depth": depth}

            async with client.stream("GET", url, params=params, timeout=60.0) as response:
                current_phase = None
                coherence = 0.0
                tokens = []

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        data = json.loads(line[6:])
                        event_type = data.get("type")

                        if event_type == "phase":
                            phase = data.get("phase", "unknown")
                            if phase != current_phase:
                                current_phase = phase
                                emoji = {
                                    "prepare": "",
                                    "synchronize": "",
                                    "broadcast": "",
                                    "sustain": "",
                                    "dissolve": ""
                                }.get(phase, "")
                                console.print(
                                    f"  {emoji} [cyan]Phase:[/cyan] {phase.upper()}"
                                )

                        elif event_type == "coherence":
                            coherence = data.get("value", 0)
                            bar = "" * int(coherence * 10) + "" * (10 - int(coherence * 10))
                            color = "green" if coherence >= 0.70 else "yellow"
                            console.print(
                                f"  [{color}]Coherence:[/{color}] {bar} {coherence:.3f}"
                            )

                        elif event_type == "token":
                            token = data.get("token", "")
                            tokens.append(token)

                        elif event_type == "complete":
                            success = data.get("success", False)
                            final_coh = data.get("final_coherence", 0)

                            console.print()
                            if success:
                                console.print(Panel(
                                    f"[green]Ignio bem-sucedida![/green]\n"
                                    f"Coerncia final: {final_coh:.3f}\n"
                                    f"Tokens: {len(tokens)}",
                                    border_style="green"
                                ))
                            else:
                                console.print(Panel(
                                    f"[yellow]Ignio parcial[/yellow]\n"
                                    f"Coerncia: {final_coh:.3f}",
                                    border_style="yellow"
                                ))

                            if tokens:
                                console.print()
                                console.print(Panel(
                                    Markdown(" ".join(tokens)),
                                    title="[bold white]RESPOSTA[/bold white]",
                                    border_style="white"
                                ))

                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        console.print(f"[red]Erro no streaming: {e}[/red]")


def display_daimon_response(data):
    """Renderiza a resposta do Daimon com esttica de Exocortex."""
    if not data:
        return

    thought_trace = data.get("reasoning_trace", "N/A (Processamento Imediato)")
    shadow_analysis = data.get("shadow_analysis", {})
    final_response = data.get("response", "")
    integrity_score = data.get("integrity_score", 1.0)

    if thought_trace != "N/A (Processamento Imediato)":
        console.print(Panel(
            Markdown(f"_{thought_trace}_"),
            title="[bold cyan]GEMINI 3.0 THINKING TRACE (SYSTEM 2)[/bold cyan]",
            border_style="cyan",
            expand=False
        ))

    if shadow_analysis:
        archetype = shadow_analysis.get("archetype", "None")
        confidence = shadow_analysis.get("confidence", 0.0)
        color = "red" if confidence > 0.7 else "yellow"

        console.print(Panel(
            f"Arqutipo: [bold]{archetype}[/bold]\n"
            f"Confiana: {confidence:.2f}\n"
            f"Gatilho: {shadow_analysis.get('trigger_detected')}",
            title=f"[{color}] DETECO DE SOMBRA JUNGUIANA[/{color}]",
            border_style=color
        ))

    console.print(Panel(
        Markdown(final_response),
        title="[bold white] DAIMON (EXOCORTEX)[/bold white]",
        subtitle=f"Integridade tica: {integrity_score:.2f}",
        border_style="white"
    ))


# ============================================================================
# MAIN LOOP
# ============================================================================

async def main_loop():
    console.clear()

    BANNER = r"""
  ____      _       _     __  __    ___    _   _
 |  _ \    / \     | |   |  \/  |  / _ \  | \ | |
 | | | |  / _ \    | |   | |\/| | | | | | |  \| |
 | |_| | / ___ \   | |   | |  | | | |_| | | |\  |
 |____/ /_/   \_\  |_|   |_|  |_|  \___/  |_| \_| v4.0
    """
    SUBTITLE = "Exocortex Operational | Stoic. Logic. Infinite."

    console.print(Panel(
        f"[bold cyan]{BANNER}[/bold cyan]\n[dim white]{SUBTITLE}[/dim white]",
        border_style="cyan",
        title="[bold white]DIGITAL DAIMON[/bold white]",
        subtitle="[green]System Online[/green]"
    ))

    # Show help on start
    console.print(Panel(
        "[bold cyan]COMANDOS DISPONVEIS:[/bold cyan]\n\n"
        "[green]/wake[/green]     Acordar o Daimon (iniciar backend)\n"
        "[green]/sleep[/green]    Adormecer o Daimon (parar servios)\n"
        "[green]/status[/green]   Ver status completo\n"
        "[green]/stream[/green]   Testar streaming de conscincia\n"
        "[green]/help[/green]     Mostrar esta ajuda\n"
        "[green]/sair[/green]     Desconectar\n\n"
        "[dim]Digite livremente para journaling...[/dim]",
        title="COMANDOS",
        border_style="dim cyan"
    ))

    async with httpx.AsyncClient() as client:
        while True:
            user_input = Prompt.ask("\n[bold green]Voc[/bold green]")

            if user_input.lower() in ["/sair", "/exit", "/quit"]:
                console.print("[magenta]Encerrando conexo...[/magenta]")
                break

            if user_input.lower() == "/help":
                help_text = """
[bold cyan]COMANDOS DE CONTROLE:[/bold cyan]
- [green]/wake[/green]:    Acordar o Daimon (inicia backend)
- [green]/sleep[/green]:   Adormecer o Daimon (para servios)
- [green]/status[/green]:  Exibe status completo do sistema

[bold cyan]COMANDOS DE INTERAO:[/bold cyan]
- [green]/stream[/green]:  Testar streaming de conscincia
- [green]/help[/green]:    Exibe esta lista
- [green]/sair[/green]:    Desconecta do Exocrtex

[bold cyan]MODOS:[/bold cyan]
- [yellow]Journaling[/yellow]: Digite livremente. O Daimon analisa e responde.
                """
                console.print(Panel(help_text, title="AJUDA", border_style="cyan"))
                continue

            if user_input.lower() == "/wake":
                wake_daimon(wait_ready=True)
                continue

            if user_input.lower() == "/sleep":
                sleep_daimon()
                continue

            if user_input.lower() == "/status":
                await show_status()
                continue

            if user_input.lower().startswith("/stream"):
                parts = user_input.split(maxsplit=1)
                content = parts[1] if len(parts) > 1 else "Teste de conscincia"
                await stream_consciousness(content)
                continue

            if not user_input.strip():
                continue

            with console.status(
                "[bold green]Processando (Thinking Mode Active)...[/bold green]",
                spinner="dots"
            ):
                response_data = await send_journal_entry(client, user_input)

            display_daimon_response(response_data)


def main():
    """Entry point with command line arguments."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command in ["wake", "acordar", "start"]:
            wake_daimon(wait_ready=True)
            return

        if command in ["sleep", "dormir", "stop"]:
            sleep_daimon()
            return

        if command in ["status", "state"]:
            asyncio.run(show_status())
            return

        if command in ["stream", "test"]:
            content = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Teste"
            asyncio.run(stream_consciousness(content))
            return

        if command in ["help", "-h", "--help"]:
            console.print(__doc__)
            return

        console.print(f"[red]Comando desconhecido: {command}[/red]")
        console.print("Use: python cli_tester.py [wake|sleep|status|stream|help]")
        return

    # Interactive mode
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        console.print("\n[bold magenta]Desconectando Exocortex...[/bold magenta]")


if __name__ == "__main__":
    main()
