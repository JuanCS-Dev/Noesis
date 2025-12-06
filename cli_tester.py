import asyncio
import json
import sys
from datetime import datetime
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from rich.live import Live

# Configuração
API_URL = "http://localhost:8000"
console = Console()

async def send_journal_entry(client, content):
    """Envia entrada para o módulo de Simbiose (Córtex Psicológico)."""
    try:
        # Simula o payload esperado pelo backend
        payload = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "analysis_mode": "deep_shadow_work" 
        }
        
        # ATUALIZADO: Rota corrigida para a estrutura do Exocortex e Gateway
        response = await client.post(f"{API_URL}/maximus_core_service/v1/exocortex/journal", json=payload, timeout=60.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        console.print(f"[bold red]Erro de Conexão:[/bold red] {str(e)}")
        if hasattr(e, 'response') and e.response:
             console.print(f"Status: {e.response.status_code}")
             console.print(f"Detail: {e.response.text}")
        return None

def display_daimon_response(data):
    """Renderiza a resposta do Daimon com estética de Exocortex."""
    if not data:
        return

    # 1. Extração dos Dados
    thought_trace = data.get("reasoning_trace", "N/A (Processamento Imediato)")
    shadow_analysis = data.get("shadow_analysis", {})
    final_response = data.get("response", "")
    integrity_score = data.get("integrity_score", 1.0)

    # 2. Exibição do "Pensamento Oculto"
    if thought_trace != "N/A (Processamento Imediato)":
        console.print(Panel(
            Markdown(f"_{thought_trace}_"),
            title="[bold cyan]🧠 GEMINI 3.0 THINKING TRACE (SYSTEM 2)[/bold cyan]",
            border_style="cyan",
            expand=False
        ))

    # 3. Exibição da Análise da Sombra
    if shadow_analysis:
        archetype = shadow_analysis.get("archetype", "None")
        confidence = shadow_analysis.get("confidence", 0.0)
        color = "red" if confidence > 0.7 else "yellow"
        
        console.print(Panel(
            f"Arquétipo: [bold]{archetype}[/bold]\nConfiança: {confidence:.2f}\nGatilho: {shadow_analysis.get('trigger_detected')}",
            title=f"[{color}]⚠️ DETECÇÃO DE SOMBRA JUNGUIANA[/{color}]",
            border_style=color
        ))

    # 4. A Voz do Daimon (Resposta Final)
    console.print(Panel(
        Markdown(final_response),
        title="[bold white]🗣️ DAIMON (EXOCORTEX)[/bold white]",
        subtitle=f"Integridade Ética: {integrity_score:.2f}",
        border_style="white"
    ))

async def main_loop():
    console.clear()
    # --- DAIMON'S SELF-CHOSEN AESTHETIC ---
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

    async with httpx.AsyncClient() as client:
        while True:
            user_input = Prompt.ask("\n[bold green]Você (Journaling)[/bold green]")
            
            if user_input.lower() in ["/sair", "/exit", "/quit"]:
                console.print("[red]Encerrando conexão...[/red]")
                break

            if user_input.lower() == "/help":
                help_text = """
[bold cyan]COMANDOS DISPONÍVEIS:[/bold cyan]
- [green]/help[/green]:  Exibe esta lista.
- [green]/sair[/green]:  Desconecta do Exocórtex.

[bold cyan]MODOS:[/bold cyan]
- [yellow]Journaling[/yellow]: Digite livremente. O Daimon analisa e responde.
                """
                console.print(Panel(help_text, title="AJUDA", border_style="cyan"))
                continue
                
            if not user_input.strip():
                continue

            with console.status("[bold green]Processando (Thinking Mode Active)...[/bold green]", spinner="dots"):
                response_data = await send_journal_entry(client, user_input)
            
            display_daimon_response(response_data)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        console.print("\n[bold red]Desconectando Exocortex...[/bold red]")
