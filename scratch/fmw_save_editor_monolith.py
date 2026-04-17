# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "tyro",
#   "rich",
#   "pydantic",
# ]
# ///
"""FMW DOSD Save Editor — decrypt, inspect, and patch PP in intermission saves."""
import hashlib
import shutil
import struct
from pathlib import Path
from typing import Annotated, Union

import tyro
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table


console = Console()
err_console = Console(stderr=True)

INTERMISSION_KEY = "avAVqqFDy2"
SLG_KEY = "aVb"


# ---------------------------------------------------------------------------
# Section 1 — Crypto
# ---------------------------------------------------------------------------

def hex_to_dec_fast(h: str) -> int:
    """Convert hex string using GameMaker's quirky hex_to_dec_fast formula.

    GM maps lowercase hex chars via (((ord(c)+4)%23)-6)&15, which is NOT
    the same as int(h,16). Lowercase a-f map to 3-8, not 10-15. All Python
    hashlib digests are lowercase, so this must be used everywhere.
    """
    r = 0
    for c in h:
        r = (r << 4) + (((ord(c) + 4) % 23 - 6) & 15)
    return r


def codec_ext(data: bytes | bytearray, is_encrypting: bool, enc_key: str) -> bytes:
    """Implement GameMaker's buffer_encode_ext XOR cipher."""
    md5u = lambda s: hashlib.md5(s.encode("utf-16-le")).hexdigest()
    sha1u = lambda s: hashlib.sha1(s.encode("utf-16-le")).hexdigest()
    md5f = lambda s: hashlib.md5(s.encode("utf-8")).hexdigest()
    sha1f = lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest()

    kh = md5u(enc_key) + sha1u(enc_key) + md5f(enc_key) + sha1f(enc_key)
    kh2 = md5u(kh) + sha1u(kh) + md5f(kh) + sha1f(kh)
    kf = kh + kh2
    kl = len(kf) // 2
    ka = [hex_to_dec_fast(kf[i * 2 : i * 2 + 2]) for i in range(kl)]

    sd = 1 if is_encrypting else -1
    bs = 128
    xs = 1
    kp = 0
    out = bytearray(len(data))

    for p in range(len(data)):
        if is_encrypting:
            out[p] = (((data[p] + bs + ka[kp]) % 256) ^ xs ^ ka[kp]) & 0xFF
        else:
            out[p] = (((data[p] ^ xs ^ ka[kp]) + bs) - ka[kp]) % 256
        xs += 1
        if xs > 5000:
            xs = 1
            kh = md5u(kh2) + sha1u(kh2) + md5f(kh2) + sha1f(kh2)
            kh2 = md5u(kh) + sha1u(kh) + md5f(kh) + sha1f(kh)
            kf = kh + kh2
            ka = [hex_to_dec_fast(kf[i * 2 : i * 2 + 2]) for i in range(kl)]
        bs += sd * (ka[kl - 1 - kp] % 2)
        if bs > 255:
            bs = 1
        elif bs < 1:
            bs = 255
        kp = (kp + 1) % kl

    return bytes(out)


# ---------------------------------------------------------------------------
# Section 2 — GmbinReader
# ---------------------------------------------------------------------------

class GmbinReader:
    """Cursor-based reader over a decrypted GMBIN buffer."""

    def __init__(self, buf: bytes, pos: int = 0) -> None:
        self.buf = buf
        self.pos = pos

    def read_string(self) -> str:
        """Read null-terminated UTF-8 string."""
        end = self.buf.find(0, self.pos)
        s = self.buf[self.pos:end].decode("utf-8", errors="replace")
        self.pos = end + 1
        return s

    def read_byte(self) -> int:
        (v,) = struct.unpack_from("<b", self.buf, self.pos)
        self.pos += 1
        return v

    def read_ubyte(self) -> int:
        (v,) = struct.unpack_from("<B", self.buf, self.pos)
        self.pos += 1
        return v

    def read_short(self) -> int:
        (v,) = struct.unpack_from("<h", self.buf, self.pos)
        self.pos += 2
        return v

    def read_ushort(self) -> int:
        (v,) = struct.unpack_from("<H", self.buf, self.pos)
        self.pos += 2
        return v

    def read_int(self) -> int:
        (v,) = struct.unpack_from("<i", self.buf, self.pos)
        self.pos += 4
        return v

    def read_float(self) -> float:
        (v,) = struct.unpack_from("<f", self.buf, self.pos)
        self.pos += 4
        return v

    def read_double(self) -> float:
        (v,) = struct.unpack_from("<d", self.buf, self.pos)
        self.pos += 8
        return v

    def read_list(self, type_code: int) -> tuple[list, list[int]]:
        """Read ds_list_write_ext format: short count + typed elements.

        Returns (values, element_byte_offsets).
        """
        count = self.read_short()
        values: list = []
        offsets: list[int] = []
        for _ in range(count):
            offsets.append(self.pos)
            if type_code == 0:
                values.append(self.read_byte())
            elif type_code == 2:
                values.append(self.read_short())
            elif type_code == 4:
                values.append(self.read_int())
            elif type_code == 6:
                values.append(self.read_float())
            elif type_code == 7:
                values.append(self.read_double())
            elif type_code == 8:
                values.append(self.read_string())
        return values, offsets

    def skip_list(self, type_code: int) -> None:
        """Read and discard a ds_list."""
        self.read_list(type_code)

    def read_grid(self, type_code: int) -> tuple[int, int, list[list]]:
        """Read ds_grid_write_ext format: short w, short h, column-major data."""
        w = self.read_short()
        h = self.read_short()
        grid: list[list] = [[None] * h for _ in range(w)]
        for col in range(w):
            for row in range(h):
                if type_code == 0:
                    grid[col][row] = self.read_byte()
                elif type_code == 2:
                    grid[col][row] = self.read_short()
                elif type_code == 4:
                    grid[col][row] = self.read_int()
                elif type_code == 8:
                    grid[col][row] = self.read_string()
        return w, h, grid

    def skip_grid(self, type_code: int) -> None:
        """Read and discard a ds_grid."""
        self.read_grid(type_code)


# ---------------------------------------------------------------------------
# Section 3 — Data models
# ---------------------------------------------------------------------------

class UnitData(BaseModel):
    """Per-unit data with byte offsets for in-place PP patching."""

    index: int
    code: str
    pp: int
    tot_pp: int
    pp_offset: int
    tot_pp_offset: int


class SkillGrids(BaseModel):
    """Skill grid data with byte ranges for buffer splicing."""

    model_config = {"arbitrary_types_allowed": True}

    skill_id: list[list[str]]   # [col=slot][row=unit]
    skill_lv: list[list[int]]   # [col=slot][row=unit]
    id_start: int               # byte offset where skill_id grid starts
    lv_end: int                 # byte offset after skill_lv grid ends
    width: int                  # columns (8 = slot count)
    height: int                 # rows (= unit count)


class SaveHeader(BaseModel):
    """Top-level scalar metadata from the save."""

    version: str
    route: str
    level: int
    stage_id: str


class IntermissionSave(BaseModel):
    """Parsed intermission save with raw buffer for in-place patching."""

    model_config = {"arbitrary_types_allowed": True}

    header: SaveHeader
    units: list[UnitData]
    skill_grids: SkillGrids
    raw_decrypted: bytearray
    total_size: int


# ---------------------------------------------------------------------------
# Section 4 — Parser
# ---------------------------------------------------------------------------

def parse_intermission_save_from_buffer(
    dec: bytearray, total_size: int
) -> IntermissionSave:
    """Parse an already-decrypted intermission save buffer.

    Walks all 95 fields in the exact order defined by file_save.gml.
    """
    payload = bytes(dec[:total_size])

    r = GmbinReader(buf=payload, pos=4)

    # Scalars (fields 1-34)
    version = r.read_string()
    route = r.read_string()
    level = r.read_byte()
    _stage_num = r.read_float()
    stage_id = r.read_string()
    _tot_turns = r.read_ushort()
    _tot_points = r.read_int()
    _tot_wp = r.read_ushort()
    _date = r.read_double()
    _sec = r.read_double()
    _is_ng0 = r.read_byte()
    _is_lvchg = r.read_byte()
    _gsp = r.read_byte()
    _gsp_max = r.read_byte()
    _num_defeat = r.read_byte()
    _is_im_ini = r.read_byte()
    _bgm_default = r.read_string()
    _team_name = r.read_string()
    _c_tot_points = r.read_int()
    _c_tot_wp = r.read_int()
    _c_tot_sec = r.read_double()
    _c_atk_dam = r.read_int()
    _c_hit_dam = r.read_int()
    _c_atk_data = r.read_string()
    _c_hit_data = r.read_string()
    _c_oimo = r.read_short()
    _c_photo = r.read_short()
    _c_yume = r.read_short()
    _c_toyohime = r.read_short()
    _c_makura = r.read_short()
    _c_meko = r.read_short()
    _c_akyu = r.read_byte()
    _c_lily = r.read_byte()
    _is_ng1 = r.read_byte()

    # Lists and grids (fields 35-49) — skip all until u_code
    r.skip_list(0)   # p_list
    r.skip_list(2)   # p_name_id
    r.skip_list(8)   # p_name_name
    r.skip_list(8)   # p_hist
    r.skip_grid(0)   # pairs
    r.skip_list(0)   # d_pair
    r.skip_list(0)   # l_select
    r.skip_list(8)   # l_BGM
    r.skip_grid(0)   # tune_lv
    r.skip_grid(0)   # char_lv
    skill_id_start = r.pos
    skill_id_w, skill_id_h, skill_id_data = r.read_grid(8)
    skill_lv_w, skill_lv_h, skill_lv_data = r.read_grid(0)
    skill_lv_end = r.pos
    r.skip_grid(8)   # item_id

    # Capture u_code (field 50)
    u_code, _ = r.read_list(8)

    # Skip until PP (fields 51-59)
    r.skip_list(8)   # u_data
    r.skip_list(8)   # BGM
    r.skip_list(2)   # rem_HP
    r.skip_list(2)   # rem_MP
    r.skip_list(8)   # rem_BL
    r.skip_list(0)   # tbonus
    r.skip_list(8)   # p_code
    r.skip_list(8)   # p_data
    r.skip_list(2)   # EXP

    # Capture PP and tot_PP with element offsets (fields 60-61)
    pp_vals, pp_offsets = r.read_list(4)
    tot_pp_vals, tot_pp_offsets = r.read_list(4)

    header = SaveHeader(
        version=version,
        route=route,
        level=level,
        stage_id=stage_id,
    )

    units = [
        UnitData(
            index=i,
            code=u_code[i],
            pp=pp_vals[i],
            tot_pp=tot_pp_vals[i],
            pp_offset=pp_offsets[i],
            tot_pp_offset=tot_pp_offsets[i],
        )
        for i in range(len(u_code))
    ]

    skill_grids = SkillGrids(
        skill_id=skill_id_data,
        skill_lv=skill_lv_data,
        id_start=skill_id_start,
        lv_end=skill_lv_end,
        width=skill_id_w,
        height=skill_id_h,
    )

    return IntermissionSave(
        header=header,
        units=units,
        skill_grids=skill_grids,
        raw_decrypted=dec,
        total_size=total_size,
    )


def parse_intermission_save(path: Path) -> IntermissionSave:
    """Decrypt and parse a gsw_NNN.sav intermission save."""
    raw = path.read_bytes()
    dec = bytearray(codec_ext(raw, False, INTERMISSION_KEY))
    total_size = struct.unpack_from("<i", dec)[0]
    return parse_intermission_save_from_buffer(dec, total_size)


# ---------------------------------------------------------------------------
# Section 5 — Mutators
# ---------------------------------------------------------------------------

INNATE_SKILLS: dict[str, set[str]] = {
    "Reimu":  {"MIKO", "KIAI", "GRAZE"},
    "Keine":  {"BLOCKING", "SATTACK", "SOKO"},
    "Youmu":  {"BLOCKING", "KIAI", "SOKO", "P_HIT"},
    "Marisa": {"MAHOU", "KIAI", "P_HIT"},
    "Nitori": {"SATTACK", "SGUARD", "P_BEAT"},
    "Alice":  {"MAHOU", "ACCURATE", "SAVE_MP", "P_EVADE"},
    "Rumia":  {"SGUARD", "SOKO", "P_TURN", "P_HIT"},
}


def serialize_string_grid(grid: list[list[str]]) -> bytes:
    """Serialize a string grid to ds_grid_write_ext format (type 8)."""
    w = len(grid)
    h = len(grid[0]) if w else 0
    parts = [struct.pack("<hh", w, h)]
    for col in range(w):
        for row in range(h):
            parts.append(grid[col][row].encode("utf-8") + b"\x00")
    return b"".join(parts)


def serialize_byte_grid(grid: list[list[int]]) -> bytes:
    """Serialize a byte grid to ds_grid_write_ext format (type 0)."""
    w = len(grid)
    h = len(grid[0]) if w else 0
    parts = [struct.pack("<hh", w, h)]
    for col in range(w):
        for row in range(h):
            parts.append(struct.pack("<b", grid[col][row]))
    return b"".join(parts)


def apply_skill_reset(save: IntermissionSave) -> list[tuple[str, list[str], int]]:
    """Reset skills to innate defaults for known characters and refund PP.

    Replaces purchased skill slots with NONE/0, rebuilds the buffer
    (since string lengths may change), and sets PP = tot_pp.

    Returns list of (unit_code, removed_skills, pp_refunded) per modified unit.
    """
    sg = save.skill_grids
    changes: list[tuple[str, list[str], int]] = []

    for unit in save.units:
        innate = INNATE_SKILLS.get(unit.code)
        if innate is None:
            continue

        removed: list[str] = []
        col = unit.index
        for slot in range(sg.height - 1):  # slots 0-6 only, skip personal slot 7
            skill_name = sg.skill_id[col][slot]
            if skill_name == "NONE":
                continue
            if skill_name not in innate:
                removed.append(f"{skill_name} L{sg.skill_lv[col][slot]}")
                sg.skill_id[col][slot] = "NONE"
                sg.skill_lv[col][slot] = 0

        if removed or unit.pp != unit.tot_pp:
            refunded = unit.tot_pp - unit.pp
            changes.append((unit.code, removed, refunded))

    # Rebuild buffer: splice new grids into the byte stream
    new_id_bytes = serialize_string_grid(sg.skill_id)
    new_lv_bytes = serialize_byte_grid(sg.skill_lv)

    before = save.raw_decrypted[: sg.id_start]
    after = save.raw_decrypted[sg.lv_end :]
    new_buf = bytearray(before + new_id_bytes + new_lv_bytes + after)

    # Update total_size (first 4 bytes)
    new_total_size = save.total_size + (len(new_buf) - len(save.raw_decrypted))
    struct.pack_into("<i", new_buf, 0, new_total_size)
    save.raw_decrypted = new_buf
    save.total_size = new_total_size

    # Re-parse from rebuilt buffer to get fresh PP offsets, then refund
    temp_save = parse_intermission_save_from_buffer(new_buf, new_total_size)
    for unit in temp_save.units:
        if unit.code in INNATE_SKILLS and unit.pp != unit.tot_pp:
            struct.pack_into("<i", new_buf, unit.pp_offset, unit.tot_pp)

    # Update save.units with fresh offsets and values
    save.units = temp_save.units
    for unit in save.units:
        if unit.code in INNATE_SKILLS:
            unit.pp = unit.tot_pp
    save.skill_grids = temp_save.skill_grids

    return changes


def apply_pp_set(save: IntermissionSave, unit_code: str, new_pp: int) -> int:
    """Set PP for a unit by code name. Returns old PP value.

    Patches in-place at the captured byte offset in raw_decrypted.
    """
    code_lower = unit_code.lower()
    for unit in save.units:
        if unit.code.lower() == code_lower:
            old_pp = unit.pp
            struct.pack_into("<i", save.raw_decrypted, unit.pp_offset, new_pp)
            unit.pp = new_pp
            return old_pp
    raise KeyError(f"Unit '{unit_code}' not found in save")


def apply_pp_delta(save: IntermissionSave, unit_code: str, delta: int) -> tuple[int, int]:
    """Add delta to a unit's PP. Returns (old_pp, new_pp)."""
    code_lower = unit_code.lower()
    for unit in save.units:
        if unit.code.lower() == code_lower:
            old_pp = unit.pp
            new_pp = old_pp + delta
            struct.pack_into("<i", save.raw_decrypted, unit.pp_offset, new_pp)
            unit.pp = new_pp
            return old_pp, new_pp
    raise KeyError(f"Unit '{unit_code}' not found in save")


def apply_pp_refund_all(save: IntermissionSave) -> list[tuple[UnitData, int, int]]:
    """Set every unit's PP to their tot_PP (full refund).

    Returns list of (unit, old_pp, new_pp) for each unit that changed.
    """
    changes: list[tuple[UnitData, int, int]] = []
    for unit in save.units:
        if unit.pp != unit.tot_pp:
            old_pp = unit.pp
            struct.pack_into("<i", save.raw_decrypted, unit.pp_offset, unit.tot_pp)
            unit.pp = unit.tot_pp
            changes.append((unit, old_pp, unit.tot_pp))
    return changes


def write_intermission_save(save: IntermissionSave, path: Path, backup: bool = True) -> None:
    """Re-encrypt and write the save back to disk.

    Creates a .bak sibling before overwriting when backup=True.
    """
    if backup and path.exists():
        bak = path.with_suffix(".sav.bak")
        shutil.copy2(path, bak)
        console.print(f"[dim]Backup: {bak}[/dim]")

    encrypted = codec_ext(save.raw_decrypted, True, INTERMISSION_KEY)
    path.write_bytes(encrypted)


# ---------------------------------------------------------------------------
# Section 6 — CLI commands
# ---------------------------------------------------------------------------

class InfoCmd(BaseModel):
    """Show unit PP summary for a save file."""

    save: Annotated[Path, tyro.conf.Positional]
    """Path to the .sav file"""

    verbose: bool = False
    """Show all unit fields including tot_PP and offset"""

    def run(self) -> None:
        """Execute info command."""
        save = parse_intermission_save(self.save)
        h = save.header

        level_names = {0: "Easy", 1: "Normal", 2: "Hard", 3: "Lunatic", 4: "Extra"}
        level_str = level_names.get(h.level, str(h.level))

        console.print(
            f"[bold cyan]{self.save.name}[/bold cyan]  "
            f"[yellow]{h.version}[/yellow]  "
            f"route=[green]{h.route}[/green]  "
            f"stage=[green]{h.stage_id}[/green]  "
            f"difficulty=[magenta]{level_str}[/magenta]"
        )

        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Unit", style="cyan", min_width=12)
        table.add_column("PP", justify="right", min_width=6)
        table.add_column("Tot PP", justify="right", min_width=7)
        table.add_column("Unspent", justify="right", min_width=8)
        if self.verbose:
            table.add_column("PP offset", style="dim", justify="right")

        for unit in save.units:
            unspent = unit.tot_pp - unit.pp
            unspent_str = f"[green]{unspent}[/green]" if unspent > 0 else f"[dim]{unspent}[/dim]"
            pp_str = f"[bold]{unit.pp}[/bold]"
            row = [str(unit.index), unit.code, pp_str, str(unit.tot_pp), unspent_str]
            if self.verbose:
                row.append(hex(unit.pp_offset))
            table.add_row(*row)

        console.print(table)


class DumpCmd(BaseModel):
    """Dump all raw field values from a save file."""

    save: Annotated[Path, tyro.conf.Positional]
    """Path to the .sav file"""

    def run(self) -> None:
        """Execute dump command."""
        save = parse_intermission_save(self.save)
        h = save.header
        console.print(f"[bold]version:[/bold] {h.version}")
        console.print(f"[bold]route:[/bold]   {h.route}")
        console.print(f"[bold]level:[/bold]   {h.level}")
        console.print(f"[bold]stage_id:[/bold] {h.stage_id}")
        console.print(f"[bold]units ({len(save.units)}):[/bold]")
        for unit in save.units:
            console.print(
                f"  [{unit.index:2d}] {unit.code:<20s} "
                f"PP={unit.pp:<6d} tot_PP={unit.tot_pp:<6d} "
                f"pp@{hex(unit.pp_offset)} tot_pp@{hex(unit.tot_pp_offset)}"
            )


class EditCmd(BaseModel):
    """Edit PP values for specific units."""

    save: Annotated[Path, tyro.conf.Positional]
    """Path to the .sav file"""

    set: list[str] = Field(default_factory=list)
    """PP assignments: Name=value (sets absolute PP)"""

    delta: list[str] = Field(default_factory=list)
    """PP deltas: Name=+N or Name=-N (adds/subtracts PP)"""

    output: Path | None = None
    """Output path (default: in-place with .bak backup)"""

    dry_run: bool = False
    """Preview changes without writing"""

    def run(self) -> None:
        """Execute edit command."""
        save_data = parse_intermission_save(self.save)

        if not self.set and not self.delta:
            err_console.print("[bold red]Error:[/bold red] Provide --set or --delta assignments")
            raise SystemExit(1)

        changes: list[str] = []

        for assignment in self.set:
            if "=" not in assignment:
                err_console.print(f"[red]Invalid --set value:[/red] {assignment!r} (expected Name=value)")
                raise SystemExit(1)
            name, val_str = assignment.split("=", 1)
            new_pp = int(val_str)
            old_pp = apply_pp_set(save_data, name, new_pp)
            changes.append(f"  {name}: PP {old_pp} -> {new_pp} (set)")

        for assignment in self.delta:
            if "=" not in assignment:
                err_console.print(f"[red]Invalid --delta value:[/red] {assignment!r} (expected Name=N)")
                raise SystemExit(1)
            name, val_str = assignment.split("=", 1)
            d = int(val_str)
            old_pp, new_pp = apply_pp_delta(save_data, name, d)
            sign = "+" if d >= 0 else ""
            changes.append(f"  {name}: PP {old_pp} -> {new_pp} ({sign}{d})")

        for line in changes:
            console.print(line)

        if self.dry_run:
            console.print("[yellow]Dry run — no file written.[/yellow]")
            return

        out = self.output or self.save
        write_intermission_save(save_data, out, backup=(out == self.save))
        console.print(f"[green]Saved:[/green] {out}")


class RefundAllCmd(BaseModel):
    """Refund all PP to tot_PP for every unit (full reset)."""

    save: Annotated[Path, tyro.conf.Positional]
    """Path to the .sav file"""

    output: Path | None = None
    """Output path (default: in-place with .bak backup)"""

    dry_run: bool = False
    """Preview changes without writing"""

    def run(self) -> None:
        """Execute refund-all command."""
        save_data = parse_intermission_save(self.save)
        changes = apply_pp_refund_all(save_data)

        if not changes:
            console.print("[dim]No units have unspent PP to refund.[/dim]")
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
        write_intermission_save(save_data, out, backup=(out == self.save))
        console.print(f"[green]Saved:[/green] {out}")


class ResetSkillsCmd(BaseModel):
    """Reset purchased skills to innate defaults and refund PP for known units."""

    save: Annotated[Path, tyro.conf.Positional]
    """Path to the .sav file"""

    output: Path | None = None
    """Output path (default: in-place with .bak backup)"""

    dry_run: bool = False
    """Preview changes without writing"""

    def run(self) -> None:
        """Execute reset-skills command."""
        save_data = parse_intermission_save(self.save)
        changes = apply_skill_reset(save_data)

        if not changes:
            console.print("[dim]No skills to reset.[/dim]")
            return

        for unit_code, removed, refunded in changes:
            console.print(f"\n[bold cyan]{unit_code}[/bold cyan]")
            if removed:
                for skill in removed:
                    console.print(f"  [red]- {skill}[/red]")
            if refunded > 0:
                console.print(f"  [green]PP refunded: +{refunded}[/green]")

        if self.dry_run:
            console.print("\n[yellow]Dry run — no file written.[/yellow]")
            return

        out = self.output or self.save
        write_intermission_save(save_data, out, backup=(out == self.save))
        console.print(f"\n[green]Saved:[/green] {out}")


Command = Union[
    Annotated[InfoCmd, tyro.conf.subcommand("info")],
    Annotated[DumpCmd, tyro.conf.subcommand("dump")],
    Annotated[EditCmd, tyro.conf.subcommand("edit")],
    Annotated[RefundAllCmd, tyro.conf.subcommand("refund-all")],
    Annotated[ResetSkillsCmd, tyro.conf.subcommand("reset-skills")],
]


if __name__ == "__main__":
    cmd = tyro.cli(Command, description="FMW DOSD save editor — inspect and patch PP in intermission saves.")
    cmd.run()
