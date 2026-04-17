"""Rebuild save files from parsed fields using GmbinWriter."""
import struct
from pathlib import Path

from .crypto import encrypt_intermission
from .gmbin import GmbinWriter
from .models import RawSaveFields


def rebuild_save(parsed: RawSaveFields) -> bytes:
    """Rebuild a decrypted save buffer from parsed fields.

    Returns the fully reconstructed payload (4-byte size header + fields),
    ready to be encrypted and written.
    """
    w = GmbinWriter()

    for field in parsed.fields:
        if field.kind == "scalar":
            getattr(w, field.write_method)(field.value)
        elif field.kind == "list":
            w.write_list(field.value, field.type_code)
        elif field.kind == "grid":
            w.write_grid(field.width, field.height, field.grid, field.type_code)

    # Build final payload: 4-byte size header (includes itself) + fields
    body = w.get_bytes()
    size = struct.pack("<i", 4 + len(body))
    return size + body


def write_rebuilt_save(parsed: RawSaveFields, path: Path, backup: bool = True) -> Path | None:
    """Rebuild, encrypt, and write the save. Returns backup path if created."""
    import shutil

    bak_path = None
    if backup and path.exists():
        bak_path = path.with_suffix(".sav.bak")
        shutil.copy2(path, bak_path)

    payload = rebuild_save(parsed)
    encrypted = encrypt_intermission(payload)
    path.write_bytes(encrypted)
    return bak_path
