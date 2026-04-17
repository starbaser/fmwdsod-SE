"""Data models for parsed FMW save files."""
from typing import Any

import attrs


@attrs.define
class UnitData:
    """Per-unit data with byte offsets for in-place PP patching."""

    index: int
    code: str
    pp: int
    tot_pp: int
    pp_offset: int
    tot_pp_offset: int


@attrs.define
class SaveHeader:
    """Top-level scalar metadata from an intermission save."""

    version: str
    route: str
    level: int
    stage_num: float
    stage_id: str
    tot_turns: int
    tot_points: int
    tot_wp: int
    playtime_sec: float


@attrs.define
class IntermissionSave:
    """Parsed intermission save with raw buffer for patching."""

    header: SaveHeader
    units: list[UnitData]
    raw_decrypted: bytearray
    total_size: int
    file_size: int

    def unit_by_name(self, name: str) -> UnitData | None:
        name_lower = name.lower()
        for unit in self.units:
            if unit.code.lower() == name_lower:
                return unit
        return None

    @property
    def playtime_str(self) -> str:
        sec = self.header.playtime_sec
        h = int(sec) // 3600
        m = (int(sec) % 3600) // 60
        s = int(sec) % 60
        return f"{h}:{m:02d}:{s:02d}"


@attrs.define
class RawSaveField:
    """A single field from file_save.gml for exact rebuild."""

    name: str
    kind: str  # "scalar", "list", "grid"
    write_method: str  # "write_string", "write_byte", etc. or "write_list", "write_grid"
    type_code: int | None = None  # for lists/grids
    value: Any = None  # scalar value, or list values
    width: int | None = None  # grid width
    height: int | None = None  # grid height
    grid: list[list] | None = None  # grid data (column-major)


@attrs.define
class RawSaveFields:
    """All 95 fields from file_save.gml, stored for exact rebuild."""

    fields: list[RawSaveField]
    raw_decrypted: bytearray
    total_size: int
