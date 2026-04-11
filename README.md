# FMW Save Editor

Save editor for **Fantasy Maiden Wars: Dream of the Stray Dreamer** (幻想少女大戦 完全版ドリーム).

Decrypts, parses, modifies, and re-encrypts FMW DOSD intermission save files (`gsw_NNN.sav`).

## Usage

```bash
uv run fmw-save-editor info saves/gsw_032.sav
uv run fmw-save-editor edit saves/gsw_032.sav --set Reimu=500 --set Keine=300
uv run fmw-save-editor edit saves/gsw_032.sav --delta Reimu=140 --delta Keine=200
uv run fmw-save-editor refund-all saves/gsw_032.sav --dry-run
```

## Save Format

FMW DOSD uses GameMaker's `buffer_encode_ext` cipher with a per-byte rolling XOR key derived from MD5/SHA1 hashes. The game's `hex_to_dec_fast` function has a quirk where lowercase hex `a-f` maps to `3-8` instead of the standard `10-15`. This implementation faithfully reproduces that behavior.

| Save Type | Key |
|---|---|
| Intermission (`gsw_NNN.sav`) | `avAVqqFDy2` |
| Battle/SLG (`gsw_as_*.sav`) | `aVb` |

After decryption, the payload is structured as GMBIN binary data: a 4-byte int32 size header followed by 95 fields of null-terminated strings, signed integers, floats, and ds_list/ds_grid structures.

## Development

```bash
uv sync
uv run fmw-save-editor --help
```
