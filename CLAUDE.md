# CLAUDE.md

## Project

FMW DOSD Save Editor — decrypts, parses, and modifies Fantasy Maiden Wars: Dream of the Stray Dreamer save files.

## Architecture

```
src/fmw_save_editor/
├── __init__.py
├── crypto.py      # buffer_encode_ext cipher with hex_to_dec_fast quirk
├── gmbin.py       # GmbinReader/GmbinWriter for GMBIN binary format
├── models.py      # UnitData, SaveHeader, IntermissionSave
├── parser.py      # parse_intermission_save() — 95-field walker
├── mutators.py    # PP set/delta/refund + write_save
└── cli.py         # tyro subcommands: info, edit, refund-all
```

## Running

```bash
uv sync
uv run fmw-save-editor info <save_file>
uv run fmw-save-editor edit <save_file> --set Reimu=500
uv run fmw-save-editor refund-all <save_file> --dry-run
```

## Critical Implementation Details

### hex_to_dec_fast

GameMaker's hex parser uses `(((ord(c)+4)%23)-6)&15`, NOT `int(h, 16)`. Lowercase `a-f` maps to `3-8` instead of `10-15`. This is the key to the cipher working. Python `hashlib` returns lowercase hex digests. NEVER use `int(h, 16)` for key derivation — always use `hex_to_dec_fast`.

### Save keys

- `avAVqqFDy2` — intermission saves (`gsw_NNN.sav`)
- `aVb` — SLG/battle saves (`gsw_as_*.sav`, `gsw_qs.sav`)

### GMBIN format

- `ds_list_write_ext`: `[int16 count] [elements...]` — type 0=byte, 2=short, 4=int, 6=float, 7=double, 8=string
- `ds_grid_write_ext`: `[int16 w] [int16 h] [column-major elements...]`
- Strings are null-terminated UTF-8

### PP patching strategy

PP values are fixed-width int32 at known byte offsets. The parser captures these offsets during traversal. `struct.pack_into` patches them in-place without shifting any surrounding data. The modified buffer is then re-encrypted and written.

### Skill editing (future)

Skill grids use variable-length strings. Editing skills requires full binary reconstruction via GmbinWriter, since changing a string length shifts all subsequent offsets. The GmbinWriter class exists for this purpose.

## Reference

Keys and format were reverse-engineered by decompiling `data.win` with UndertaleModTool CLI. Decompiled GML sources live in the parent FMW project at `decompiled/CodeEntries/`.
