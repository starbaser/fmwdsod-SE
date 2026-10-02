# FMW DOSD Save Editor

Decrypt, inspect, and modify save files for Fantasy Maiden Wars: Dream of the Stray Dreamer (Steam App ID: 3575980).

Supports intermission saves (`gsw_NNN.sav`). Quicksave/battle saves (`gsw_qs.sav`, `gsw_as_*.sav`) use a different key and extended format.

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## CLI

```bash
# Inspect a save — shows route, stage, difficulty, and per-unit PP table
uv run fmw-save-editor info <save_file>

# Set a unit's PP to an absolute value
uv run fmw-save-editor edit <save_file> --set Reimu=500

# Add/subtract PP
uv run fmw-save-editor edit <save_file> --delta Marisa=100

# Combine multiple edits
uv run fmw-save-editor edit <save_file> --set Reimu=500 --delta Marisa=100

# Preview without writing
uv run fmw-save-editor edit <save_file> --set Reimu=500 --dry-run

# Write to a different file
uv run fmw-save-editor edit <save_file> --set Reimu=500 --output modified.sav

# Refund all spent PP across every unit
uv run fmw-save-editor refund-all <save_file>
uv run fmw-save-editor refund-all <save_file> --dry-run

# Add an item to inventory
uv run fmw-save-editor add-item <save_file> Sunflower
```

When writing to the input file (the default), a `.sav.bak` backup is created automatically.

## Save Format

### Encryption

Saves are encrypted with `buffer_encode_ext` -- a per-byte rolling XOR cipher. Key material is derived from the password through MD5 and SHA1 hashes (both UTF-16LE and UTF-8 encodings), producing a 160-byte key array that cycles with period 5000.

| Save Type | File Pattern | Key |
|---|---|---|
| Intermission | `gsw_NNN.sav` | `avAVqqFDy2` |
| Battle / SLG / Autosave | `gsw_as_*.sav`, `gsw_qs.sav` | `aVb` |

### `hex_to_dec_fast` Quirk

The cipher's key derivation depends on GameMaker's non-standard hex parser:

```
(((ord(c) + 4) % 23) - 6) & 15
```

This maps lowercase `a-f` to `3-8`, not the standard `10-15`. Since Python's `hashlib` returns lowercase hex digests, using `int(h, 16)` for key derivation produces wrong keys and corrupts the file. All hex-to-integer conversion in this codebase uses the formula above.

### GMBIN Binary Payload

After decryption, the payload is a GMBIN binary stream:

```
┌────────────────────────────────────────────┐
│ int32 size    (total payload length incl.) │
├────────────────────────────────────────────┤
│ 34 scalar fields (strings, ints, floats)   │
├────────────────────────────────────────────┤
│ 6 grids + 55 lists                         │
│   unit codes, PP, equipment, skills, etc.  │
├────────────────────────────────────────────┤
│ 95 fields total per file_save.gml          │
└────────────────────────────────────────────┘
```

**Primitive types** -- all little-endian:

| Type Code | Format | Size |
|---|---|---|
| 0 | signed byte | 1B |
| 2 | signed short | 2B |
| 4 | signed int32 | 4B |
| 6 | float | 4B |
| 7 | double | 8B |
| 8 | null-terminated UTF-8 string | variable |

**Composite structures:**

- `ds_list_write_ext`: `[int16 count] [element] x count`
- `ds_grid_write_ext`: `[int16 width] [int16 height] [element] x (w*h)` (column-major)
- `ds_map_write_ext`: `[int16 count] [string key, typed value] x count`

### Two Mutation Strategies

**In-place patching** (`edit`, `refund-all`) -- for fixed-width fields like PP (int32). The parser records byte offsets during traversal; `struct.pack_into` overwrites values without shifting surrounding data. Fast and safe for scalar edits.

**Full rebuild** (`add-item`) -- for mutations that change field lengths (adding list elements, modifying string grids). All 95 fields are parsed into `RawSaveField` objects, mutated, then serialized back through `GmbinWriter`.

Both paths re-encrypt the buffer before writing.

## Library API

```python
from pathlib import Path
from fmw_save_editor.parser import parse_intermission_save, parse_all_fields
from fmw_save_editor.crypto import decrypt_intermission, encrypt_intermission
from fmw_save_editor.mutators import apply_pp_set, write_save
from fmw_save_editor.rebuilder import rebuild_save, write_rebuilt_save

# Inspect a save
save = parse_intermission_save(Path("gsw_001.sav"))
for unit in save.units:
    print(f"{unit.code}: {unit.pp}/{unit.tot_pp} PP")

# Modify PP and write back
apply_pp_set(save, "Reimu", 999)
write_save(save, Path("gsw_001.sav"))

# Full rebuild (for structural mutations)
parsed = parse_all_fields(Path("gsw_001.sav"))
parsed.fields[90].value.append("NewItem")   # ItemID list
parsed.fields[91].value.append(1)           # tot_num_of_items
parsed.fields[92].value.append(1)           # num_of_items
write_rebuilt_save(parsed, Path("gsw_001.sav"))

# Raw crypto
raw = Path("gsw_001.sav").read_bytes()
decrypted = decrypt_intermission(raw)
# ... inspect bytes ...
encrypted = encrypt_intermission(decrypted)
```

## Project Structure

```
src/fmw_save_editor/
├── cli.py         # tyro subcommands: info, edit, refund-all, add-item
├── crypto.py      # buffer_encode_ext cipher with hex_to_dec_fast
├── gmbin.py       # GmbinReader / GmbinWriter for binary format
├── models.py      # UnitData, SaveHeader, IntermissionSave, RawSaveField
├── parser.py      # parse_intermission_save() + parse_all_fields()
├── mutators.py    # in-place PP patching + write_save
└── rebuilder.py   # full binary reconstruction + write_rebuilt_save
```
