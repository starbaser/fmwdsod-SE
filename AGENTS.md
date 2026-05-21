# CLAUDE.md

## Project

FMW DOSD Save Editor — decrypts, parses, and modifies Fantasy Maiden Wars: Dream of the Stray Dreamer save files.

## Architecture

```
src/fmw_save_editor/
├── __init__.py
├── crypto.py      # buffer_encode_ext cipher with hex_to_dec_fast quirk
├── gmbin.py       # GmbinReader/GmbinWriter for GMBIN binary format (list, grid, map, bool)
├── models.py      # UnitData, SaveHeader, IntermissionSave, RawSaveField, RawSaveFields
├── parser.py      # parse_intermission_save() + parse_all_fields() — 95-field walkers
├── mutators.py    # PP set/delta/refund + write_save (in-place patching)
├── rebuilder.py   # rebuild_save() + write_rebuilt_save() — full binary reconstruction
└── cli.py         # tyro subcommands: info, edit, refund-all, add-item
scratch/
├── dump_quicksave.py              # SLG/quicksave byte map tool (CSV output)
├── fmw_save_editor_monolith.py    # archived original monolith
└── gml_GlobalScript_*.gml         # decompiled GML reference (18 files)
```

## Running

```bash
uv sync
uv run fmw-save-editor info <save_file>
uv run fmw-save-editor edit <save_file> --set Reimu=500
uv run fmw-save-editor refund-all <save_file> --dry-run
uv run fmw-save-editor add-item <save_file> Sunflower

# Quicksave byte map (scratch tool)
uv run scratch/dump_quicksave.py saves/gsw_qs.sav > dump.csv
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
- `ds_map_write_ext`: `[int16 count] [string key + typed value]×count`
- Strings are null-terminated UTF-8
- `buffer_bool`: 1 byte (unsigned)

### PP patching strategy

PP values are fixed-width int32 at known byte offsets. The parser captures these offsets during traversal. `struct.pack_into` patches them in-place without shifting any surrounding data. The modified buffer is then re-encrypted and written.

### Full rebuild pipeline

`parse_all_fields()` captures all 95 fields as `RawSaveField` objects (scalar/list/grid with metadata). `rebuild_save()` serializes them back through `GmbinWriter`. This supports mutations that change field lengths (e.g., adding items to lists, modifying skill grid strings).

### Quicksave (SLG) format

Quicksaves (`gsw_qs.sav`, `gsw_as_*.sav`) use key `aVb` and wrap the intermission save data with battle state. Structure:

```
┌──────────────────────────────────────────────┐
│ [4B] size_prefix (int32)                     │
├──────────────────────────────────────────────┤
│ SLG Header                                   │
│   SLG_ID (string), phase_id (s8)             │
│   if phase 0|5: cost*2 (u8), l_final (list0) │
├──────────────────────────────────────────────┤
│ Version Block                                │
│   version (string), is_autosave (bool)       │
│   if autosave: [pos(s32)][size(s32)][img]    │
├──────────────────────────────────────────────┤
│ file_save() — 95 fields (same as intermiss.) │
│   34 scalars, 6 grids, 55 lists              │
│   item_id grid = equipment allocation        │
├──────────────────────────────────────────────┤
│ save_control() — battle state                │
│   29 ints, 7 strings, 2 shorts               │
│   7 lists, 2 maps (tent_vnames, tent_snames) │
├──────────────────────────────────────────────┤
│ save_draw() — map/bullet/spell/skill grid    │
│   w×h tile grid (3B each: MOV + wall)        │
│   variable-length bullet/spell/skill arrays  │
├──────────────────────────────────────────────┤
│ save_icons() — per-ObjIcon battle state      │
│   player icons: <player> sentinel per icon   │
│     unit data, pilot stats, equipment slots  │
│     ammo, unit commands, uval entries        │
│   </players> delimiter                       │
│   enemy icons: <enemy> sentinel per icon     │
│     unit data, AI state, equipment, uvals    │
│   </enemies> delimiter                       │
├──────────────────────────────────────────────┤
│ save_objects()                                │
│   <object>...</object> map objects            │
│   <item>...</item> map items                 │
├──────────────────────────────────────────────┤
│ save_etc() — 2 grids + 10 scalar fields      │
└──────────────────────────────────────────────┘
```

Phase 0 (deployment) quicksaves have no player icons — units aren't placed yet. Equipment allocation is in the `item_id` grid from `file_save()`.

The `scratch/dump_quicksave.py` tool fully parses all sections and outputs a CSV byte map. Verified: 100% coverage with zero leftover bytes on a 32KB quicksave.

## Reference

Keys and format were reverse-engineered by decompiling `data.win` with UndertaleModTool CLI. Canonical decompiled GML sources live at `~/gaming/touhou/fantasy-maiden-wars/modding/decompiled/CodeEntries/`. The `scratch/` directory contains local copies of all GML files needed for save format work:

| GML File | Purpose |
|---|---|
| `file_save.gml` | 95-field intermission save format |
| `save_SLG.gml` | Quicksave top-level structure |
| `save_global.gml` | Delegates to file_save() |
| `save_control.gml` | Battle control state (29 ints, 7 strings, lists, maps) |
| `save_draw.gml` | Map tile grid, bullets, spells, skills |
| `save_icons.gml` | Iterates ObjIcon instances (player/enemy) |
| `save_icon_player2.gml` | Per-player: equipment, pilots, weapons, unit commands |
| `save_icon_enemy2.gml` | Per-enemy: AI state, stats, equipment |
| `save_objects.gml` | Map objects and items with sentinel delimiters |
| `save_etc.gml` | SpellTot/SpellGot grids + misc scalars |
| `buffer_encode_ext.gml` | Cipher algorithm |
| `ds_list_write_ext.gml` | List serialization format |
| `ds_grid_write_ext.gml` | Grid serialization format |
| `ds_map_write_ext.gml` | Map serialization format |
| `hex_to_dec_fast.gml` | GameMaker hex parsing quirk |
| `save_functions.gml` | Encryption keys |
| `GMBINCloseFile.gml` | Size prefix + encrypt-on-close |
| `GMBINOpenFileReadPW.gml` | Confirms cipher is buffer_encode_ext |
