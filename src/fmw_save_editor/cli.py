"""CLI interface using tyro subcommands."""
from pathlib import Path
from typing import Annotated, Union

import attrs
import tyro
from rich.console import Console
from rich.table import Table

from .mutators import apply_pp_delta, apply_pp_refund_all, apply_pp_set, write_save
from .parser import parse_all_fields, parse_intermission_save
from .rebuilder import write_rebuilt_save

console = Console()
err_console = Console(stderr=True)

LEVEL_NAMES = {0: "Easy", 1: "Normal", 2: "Hard", 3: "Lunatic", 4: "Extra"}


@attrs.define
class InfoCmd:
    """Show unit PP summary for a save file."""

    save: Annotated[Path, tyro.conf.Positional]

    def run(self) -> None:
        save = parse_intermission_save(self.save)
        h = save.header

        console.print(
            f"[bold cyan]{self.save.name}[/bold cyan]  "
            f"[yellow]{h.version}[/yellow]  "
            f"route=[green]{h.route}[/green]  "
            f"stage=[green]{h.stage_id}[/green]  "
            f"difficulty=[magenta]{LEVEL_NAMES.get(h.level, str(h.level))}[/magenta]  "
            f"playtime=[dim]{save.playtime_str}[/dim]"
        )

        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Unit", style="cyan", min_width=12)
        table.add_column("PP", justify="right", min_width=6)
        table.add_column("Tot PP", justify="right", min_width=7)
        table.add_column("Spent", justify="right", min_width=6)

        for unit in save.units:
            spent = unit.tot_pp - unit.pp
            spent_str = f"[yellow]{spent}[/yellow]" if spent > 0 else f"[dim]{spent}[/dim]"
            table.add_row(str(unit.index), unit.code, str(unit.pp), str(unit.tot_pp), spent_str)

        console.print(table)


@attrs.define
class EditCmd:
    """Edit PP values for specific units."""

    save: Annotated[Path, tyro.conf.Positional]
    set: list[str] = attrs.Factory(list)
    """Unit=value pairs (absolute PP)"""
    delta: list[str] = attrs.Factory(list)
    """Unit=N pairs (add/subtract PP)"""
    output: Path | None = None
    dry_run: bool = False

    def run(self) -> None:
        save_data = parse_intermission_save(self.save)

        if not self.set and not self.delta:
            err_console.print("[bold red]Error:[/bold red] Provide --set or --delta assignments")
            raise SystemExit(1)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Unit", style="cyan")
        table.add_column("Old PP", justify="right")
        table.add_column("New PP", justify="right", style="green")
        table.add_column("Change", justify="right")

        for assignment in self.set:
            name, val_str = assignment.split("=", 1)
            new_pp = int(val_str)
            old_pp = apply_pp_set(save_data, name, new_pp)
            table.add_row(name, str(old_pp), str(new_pp), f"set")

        for assignment in self.delta:
            name, val_str = assignment.split("=", 1)
            d = int(val_str)
            old_pp, new_pp = apply_pp_delta(save_data, name, d)
            sign = "+" if d >= 0 else ""
            table.add_row(name, str(old_pp), str(new_pp), f"{sign}{d}")

        console.print(table)

        if self.dry_run:
            console.print("[yellow]Dry run — no file written.[/yellow]")
            return

        out = self.output or self.save
        bak = write_save(save_data, out, backup=(out == self.save))
        if bak:
            console.print(f"[dim]Backup: {bak}[/dim]")
        console.print(f"[green]Saved:[/green] {out}")


@attrs.define
class RefundAllCmd:
    """Refund all PP to tot_PP for every unit (full reset)."""

    save: Annotated[Path, tyro.conf.Positional]
    output: Path | None = None
    dry_run: bool = False

    def run(self) -> None:
        save_data = parse_intermission_save(self.save)
        changes = apply_pp_refund_all(save_data)

        if not changes:
            console.print("[dim]No units have spent PP to refund.[/dim]")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("Unit", style="cyan")
        table.add_column("Old PP", justify="right")
        table.add_column("New PP", justify="right", style="green")
        table.add_column("Refunded", justify="right", style="yellow")

        for unit, old_pp, new_pp in changes:
            table.add_row(unit.code, str(old_pp), str(new_pp), f"+{new_pp - old_pp}")

        console.print(table)

        if self.dry_run:
            console.print("[yellow]Dry run — no file written.[/yellow]")
            return

        out = self.output or self.save
        bak = write_save(save_data, out, backup=(out == self.save))
        if bak:
            console.print(f"[dim]Backup: {bak}[/dim]")
        console.print(f"[green]Saved:[/green] {out}")


@attrs.define
class AddItemCmd:
    """Add an item to the save by appending to the item lists."""

    save: Annotated[Path, tyro.conf.Positional]
    item: Annotated[str, tyro.conf.Positional]
    """Item name to add (e.g. Sunflower)"""
    output: Path | None = None
    dry_run: bool = False

    def run(self) -> None:
        parsed = parse_all_fields(self.save)

        # Field 91 (index 90): ItemID (string list)
        # Field 92 (index 91): tot_num_of_items (byte list)
        # Field 93 (index 92): num_of_items (byte list)
        item_id_field = parsed.fields[90]
        tot_field = parsed.fields[91]
        num_field = parsed.fields[92]

        if self.item in item_id_field.value:
            err_console.print(f"[yellow]Item '{self.item}' already exists in save.[/yellow]")
            return

        console.print(f"Adding [cyan]{self.item}[/cyan] to save (items: {len(item_id_field.value)} -> {len(item_id_field.value) + 1})")

        item_id_field.value = item_id_field.value + [self.item]
        tot_field.value = tot_field.value + [1]
        num_field.value = num_field.value + [1]

        if self.dry_run:
            console.print("[yellow]Dry run — no file written.[/yellow]")
            return

        out = self.output or self.save
        bak = write_rebuilt_save(parsed, out, backup=(out == self.save))
        if bak:
            console.print(f"[dim]Backup: {bak}[/dim]")
        console.print(f"[green]Saved:[/green] {out}")


Command = Union[
    Annotated[InfoCmd, tyro.conf.subcommand("info")],
    Annotated[EditCmd, tyro.conf.subcommand("edit")],
    Annotated[RefundAllCmd, tyro.conf.subcommand("refund-all")],
    Annotated[AddItemCmd, tyro.conf.subcommand("add-item")],
]


def main() -> None:
    cmd = tyro.cli(Command, description="FMW DOSD save editor")
    cmd.run()


if __name__ == "__main__":
    main()
