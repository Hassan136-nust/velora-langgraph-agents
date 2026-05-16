"""
Rich Terminal CLI for the Multi-Agent Business Research Assistant.
Beautiful output with panels, spinners, progress indicators, and formatted reports.
Streams agent JSON logs sequentially in real-time.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.json import JSON as RichJSON
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.rule import Rule
from rich import box

from app.graph import build_graph, AgentState
from app.utils.logger import clear_logs, get_logs

console = Console()


def print_header():
    header = Text()
    header.append("🔬 ", style="bold")
    header.append("VELORA", style="bold bright_magenta")
    header.append(" Research Assistant", style="bold white")

    console.print()
    console.print(Panel(
        header,
        subtitle="[dim]Powered by LangGraph + Tavily[/dim]",
        border_style="bright_magenta",
        box=box.DOUBLE_EDGE,
        padding=(1, 4),
    ))
    console.print(
        "[dim]Ask about any company. Type [bold]quit[/bold] to exit.[/dim]\n"
    )


def print_agent_step(emoji: str, agent: str, status: str, style: str = ""):
    text = Text()
    text.append(f"{emoji} ", style="bold")
    text.append(f"{agent}", style=f"bold {style}")
    text.append(f" → {status}", style="dim")
    console.print(text)


def print_spellcheck(sc_result: dict):
    if not sc_result:
        return
    status = sc_result.get("status", "no_correction")
    if status == "corrected":
        console.print(Panel(
            f"[bold yellow]🔤 Auto-corrected:[/bold yellow] "
            f"\"{sc_result['original']}\" → [bold green]{sc_result['suggested']}[/bold green] "
            f"[dim](confidence: {sc_result.get('confidence', 0):.0%})[/dim]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 2),
        ))
    elif status == "uncertain":
        console.print(Panel(
            f"[bold yellow]🤔 Did you mean[/bold yellow] "
            f"[bold]{sc_result['suggested']}[/bold] "
            f"instead of \"{sc_result['original']}\"?",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 2),
        ))


def print_logs(logs: list[dict]):
    if not logs:
        return
    console.print()
    console.print(Rule("[bold dim]Pipeline Logs[/bold dim]", style="dim"))
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("Agent", style="cyan", width=18)
    table.add_column("Level", width=8)
    table.add_column("Message", style="white")
    for entry in logs:
        level = entry.get("level", "INFO")
        level_style = {
            "INFO": "green", "WARNING": "yellow",
            "ERROR": "red", "DEBUG": "dim"
        }.get(level, "white")
        table.add_row(
            entry.get("agent", ""),
            f"[{level_style}]{level}[/{level_style}]",
            entry.get("message", ""),
        )
    console.print(table)


def main():
    print_header()

    messages = []
    company_name = ""

    while True:
        console.print()
        user_input = Prompt.ask("[bold bright_cyan]📝 You[/bold bright_cyan]").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            console.print("\n[bold bright_magenta]👋 Goodbye![/bold bright_magenta]\n")
            break

        messages.append({"role": "user", "content": user_input})
        console.print()
        
        clear_logs()
        graph = build_graph()
        
        state: AgentState = {
            "messages": messages,
            "user_query": user_input,
            "company_name": company_name,
            "clarity_status": "",
            "clarification_question": "",
            "spellcheck_result": None,
            "research_findings": None,
            "confidence_score": 0,
            "validation_result": "",
            "validation_notes": "",
            "attempts": 0,
            "final_answer": "",
            "agent_outputs": {},
            "agent_logs": [],
            "error_log": [],
        }

        console.print(Rule("[bold]Agent Execution Flow[/bold]", style="bright_magenta"))
        console.print()

        try:
            with console.status("[bold bright_magenta]🔍 Velora is processing...[/bold bright_magenta]", spinner="dots") as status_ctx:
                for output in graph.stream(state, stream_mode="updates"):
                    for node_name, state_update in output.items():
                        
                        # Merge state sequentially
                        for k, v in state_update.items():
                            if k == "agent_outputs":
                                state["agent_outputs"].update(v)
                            else:
                                state[k] = v
                                
                        outs = state.get("agent_outputs", {})
                        
                        status_ctx.stop()  # Pause spinner to print clean block
                        
                        if node_name == "clarity" and "clarity_agent" in outs:
                            cl = outs["clarity_agent"]
                            
                            # Show spellcheck IMMEDIATELY when clarity finishes
                            print_spellcheck(state.get("spellcheck_result"))
                            
                            status_icon = "✅" if cl.get("clarity_status") == "clear" else "⚠️"
                            print_agent_step("🔍", "Clarity Agent", f"{cl.get('clarity_status', '')} — {cl.get('detected_company', 'N/A')}", "cyan")
                            console.print(Panel(RichJSON(json.dumps(cl, indent=2, default=str)), title="[bold cyan]Clarity Agent Output[/bold cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 1)))
                            console.print()

                        elif node_name == "research" and "research_agent" in outs:
                            ra = outs["research_agent"]
                            conf = ra.get("confidence_score", 0)
                            conf_icon = "🟢" if conf >= 8 else "🟡" if conf >= 6 else "🔴"
                            print_agent_step("📚", "Research Agent", f"confidence {conf}/10 {conf_icon} | {ra.get('total_results', 0)} sources | attempt {ra.get('search_attempt', 1)}", "blue")
                            console.print(Panel(RichJSON(json.dumps(ra, indent=2, default=str)), title="[bold blue]Research Agent Output[/bold blue]", border_style="blue", box=box.ROUNDED, padding=(0, 1)))
                            console.print()

                        elif node_name == "validator" and "validator_agent" in outs:
                            va = outs["validator_agent"]
                            print_agent_step("🛡️", "Validator Agent", f"{va.get('validation_result', '')} | quality {va.get('quality_score', 0)}/10", "yellow")
                            console.print(Panel(RichJSON(json.dumps(va, indent=2, default=str)), title="[bold yellow]Validator Agent Output[/bold yellow]", border_style="yellow", box=box.ROUNDED, padding=(0, 1)))
                            console.print()

                        elif node_name == "synthesis" and "synthesis_agent" in outs:
                            sa = outs["synthesis_agent"]
                            print_agent_step("🧠", "Synthesis Agent", f"{sa.get('report_status', '')}", "magenta")
                            console.print(Panel(RichJSON(json.dumps(sa, indent=2, default=str)), title="[bold magenta]Synthesis Agent Output[/bold magenta]", border_style="magenta", box=box.ROUNDED, padding=(0, 1)))
                            console.print()

                        status_ctx.start()  # Resume spinner
                        
        except Exception as e:
            console.print(f"\n[bold red]❌ Pipeline Error:[/bold red] {str(e)}\n")

        # End of Pipeline Print
        console.print(Rule(style="dim"))
        console.print()

        if state.get("company_name"):
            company_name = state["company_name"]

        if state.get("clarity_status") == "needs_clarification":
            clarification = state.get("clarification_question", "Could you provide more details?")
            console.print(Panel(f"[bold yellow]🤔 Clarification needed:[/bold yellow]\n\n{clarification}", border_style="yellow", box=box.ROUNDED, padding=(1, 2)))
            messages.append({"role": "assistant", "content": clarification})
        else:
            final_answer = state.get("final_answer", "No response generated.")
            confidence = state.get("confidence_score", 0)
            attempts = state.get("attempts", 0)

            console.print(Panel(Markdown(final_answer), title="[bold bright_magenta]🤖 Research Report[/bold bright_magenta]", border_style="bright_magenta", box=box.ROUNDED, padding=(1, 2)))

            conf_color = "green" if confidence >= 8 else "yellow" if confidence >= 6 else "red"
            info_bar = Text()
            info_bar.append("📊 Confidence: ", style="bold")
            info_bar.append(f"{confidence}/10", style=f"bold {conf_color}")
            info_bar.append("  |  ", style="dim")
            info_bar.append(f"🔄 Attempts: {attempts}", style="dim")

            findings = state.get("research_findings", {})
            items = findings.get("items", []) if findings else []
            if items:
                info_bar.append("  |  ", style="dim")
                info_bar.append(f"📎 Sources: {len(items)}", style="dim")

            console.print(info_bar)
            messages.append({"role": "assistant", "content": final_answer})

        print_logs(get_logs())
        console.print()
        console.print(Rule(style="dim"))


if __name__ == "__main__":
    main()
