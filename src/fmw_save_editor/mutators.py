"""Save mutation functions — modify PP values in decrypted save buffers."""
import shutil
import struct
from pathlib import Path

from .crypto import encrypt_intermission
from .models import IntermissionSave, UnitData


def apply_pp_set(save: IntermissionSave, unit_code: str, new_pp: int) -> int:
    """Set PP for a unit. Returns old PP. Raises KeyError if not found."""
    unit = save.unit_by_name(unit_code)
    if unit is None:
        raise KeyError(f"Unit '{unit_code}' not found in save")
    old_pp = unit.pp
    struct.pack_into("<i", save.raw_decrypted, unit.pp_offset, new_pp)
    unit.pp = new_pp
    return old_pp


def apply_pp_delta(save: IntermissionSave, unit_code: str, delta: int) -> tuple[int, int]:
    """Add delta to a unit's PP. Returns (old_pp, new_pp)."""
    unit = save.unit_by_name(unit_code)
    if unit is None:
        raise KeyError(f"Unit '{unit_code}' not found in save")
    old_pp = unit.pp
    new_pp = old_pp + delta
    struct.pack_into("<i", save.raw_decrypted, unit.pp_offset, new_pp)
    unit.pp = new_pp
    return old_pp, new_pp


def apply_pp_refund_all(save: IntermissionSave) -> list[tuple[UnitData, int, int]]:
    """Set every unit's PP to their tot_PP. Returns changes as (unit, old, new)."""
    changes: list[tuple[UnitData, int, int]] = []
    for unit in save.units:
        if unit.pp != unit.tot_pp:
            old_pp = unit.pp
            struct.pack_into("<i", save.raw_decrypted, unit.pp_offset, unit.tot_pp)
            unit.pp = unit.tot_pp
            changes.append((unit, old_pp, unit.tot_pp))
    return changes


def write_save(save: IntermissionSave, path: Path, backup: bool = True) -> Path | None:
    """Re-encrypt and write the save. Returns backup path if created."""
    bak_path = None
    if backup and path.exists():
        bak_path = path.with_suffix(".sav.bak")
        shutil.copy2(path, bak_path)

    encrypted = encrypt_intermission(save.raw_decrypted)
    path.write_bytes(encrypted)
    return bak_path
