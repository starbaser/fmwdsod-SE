# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Two workstreams for **Fantasy Maiden Wars** (幻想少女大戦 / Gensou Shoujo Taisen) — a Touhou fan-made SRPG by doujin circle Sanbondo:

1. **Wiki pipeline** — scraping, cleaning, and translating the Japanese strategy wiki into English
2. **Save editor** — reverse-engineered save file encryption and GMBIN binary format for the Steam/Steam Deck version (DOSD)

## Local Inference Stack

**All LLM processing runs locally on GPU. No cloud API calls for pipeline stages.**

- **Model**: Qwen3.5-122B-A10B (Q4_K_M GGUF, split across 2 files)
- **Server**: llama-server (llama-cpp with CUDA) on `127.0.0.1:8080`
- **GPU offload**: Full (`--n-gpu-layers 999`)
- **Context window**: 96K tokens (`--ctx-size 98304`)
- **Parallel slots**: 3 (`--parallel 3`)
- **Reasoning budget**: 0 (extended thinking disabled)

Model files: `./models/Qwen_Qwen3.5-122B-A10B-Q4_K_M-*.gguf`

### Starting the inference server

```bash
nix develop              # enter devShell (provides llama-server with CUDA)
process-compose up       # starts llama-server on :8088
```

The `flake.nix` provides `python3`, `uv`, and `cudaPkgs.llama-cpp`. The `process-compose.yml` defines the `llama-server` process with all GPU/context/parallelism settings.

### Connecting from scripts

All pipeline scripts use the OpenAI-compatible API at `http://localhost:8088/v1`:

```python
DEFAULT_BASE_URL = "http://localhost:8088/v1"
DEFAULT_API_KEY = "not-needed"        # no auth for local llama-server
DEFAULT_MODEL = "qwen3.5-122b-a10b"  # matches local GGUF
```

**ccproxy** (`localhost:4000`) exists separately as a cloud model routing gateway for Claude Code itself. Pipeline scripts should NOT use ccproxy — they connect to llama-server directly.

## Running the Pipeline

All scripts use PEP 723 inline metadata — run with `uv run` (no pyproject.toml or requirements.txt):

```bash
# Ensure llama-server is running first:
# nix develop && process-compose up

# Core translation pipeline
uv run scrape_wiki.py [--concurrency N] [--output DIR] [--retry N]     # requires FIRECRAWL_API_KEY
uv run clean_wiki.py [--input DIR] [--output DIR] [--dry-run]          # pure Python, no deps
uv run translate_wiki.py [--concurrency N] [--input DIR] [--output DIR] [--model MODEL]

# Validation pipeline (under active development)
uv run stage1_catalog.py [--input akurasu.net] [--output cache/entity_catalog.jsonl]
uv run stage3_extract_en.py [--input wiki-en] [--output cache/en_terms] [--concurrency N]
# stage2_extract_jp.py — not yet implemented
# stage4_validate.py — not yet implemented
# apply_corrections.py — not yet implemented
```

## Architecture

### Core Translation Pipeline

```
scrape_wiki.py ──▶ wiki-jp/*.md (raw scraped markdown)
                        │
clean_wiki.py  ──▶ wiki-clean/*.md (stripped of wiki chrome)
                        │
translate_wiki.py ──▶ wiki-en/*.md (English translations)
```

**Key design properties:**
- **Idempotent** — all stages skip already-processed files (existence + size check)
- **Resumable** — semaphore-bounded async concurrency with retry/backoff
- **Self-contained** — each script declares its own deps via PEP 723 inline metadata
- **Local-first** — all LLM processing via local llama-server (Qwen3.5-122B)

| Script | Deps | Service | Notes |
|--------|------|---------|-------|
| `scrape_wiki.py` | `httpx` | Firecrawl API (cloud) | 243 hardcoded URLs, writes YAML frontmatter |
| `clean_wiki.py` | stdlib only | none | Regex-based subtractive cleaning |
| `translate_wiki.py` | `openai` | llama-server (localhost:8088) | Qwen3.5-122B, 100+ term glossary, chunks at `##`/`###` (>15K chars) |

### Validation Pipeline (Stages 0-5) — Under Development

Extracts and validates game terms (spirit commands, skills, abilities, weapons, etc.) across translated wiki:

```
akurasu.net/*.md (canonical wiki)
     │
     ▼
[Stage 1: stage1_catalog.py] ──▶ entity_catalog.jsonl
                                 (EN, JP, category triples)
                                      ▲
                ┌─────────────────────┘
                │
wiki-en/*.md ──▶ [Stage 3: stage3_extract_en.py] ──▶ cache/en_terms/*.jsonl
                │
                ├─▶ [Stage 2: stage2_extract_jp.py] ──▶ cache/jp_terms/*.jsonl
                │   (uses wiki-clean/*.md source)
                │
                └─▶ [Stage 4: stage4_validate.py] ──▶ corrections.jsonl
                    (align JP↔EN, validate against catalog)
                        │
                        ▼
                 [Stage 5: apply_corrections.py]
                 (patch wiki-en/*.md)
```

**Extraction stages use langextract** — LLM-powered few-shot structured extraction with char_interval source grounding. All extraction stages must use llama-server (localhost:8088) with Qwen3.5-122B, NOT ccproxy.

| Script | Input | Output | Notes |
|--------|-------|--------|-------|
| `stage1_catalog.py` | akurasu.net/*.md (20 pages) | cache/entity_catalog.jsonl | 2-pass extraction for high recall |
| `stage3_extract_en.py` | wiki-en/*.md (239+ files) | cache/en_terms/*.jsonl | char_start/char_end + heading_path |
| `stage2_extract_jp.py` | wiki-clean/*.md | cache/jp_terms/*.jsonl | requires UnicodeTokenizer for JP accuracy |
| `stage4_validate.py` | JP + EN terms + catalog | corrections.jsonl | structural alignment validator |
| `apply_corrections.py` | corrections.jsonl | patched wiki-en/*.md | in-place fixes |

## Output Directories

- `wiki-jp/` — raw scraped Japanese markdown
- `wiki-clean/` — cleaned Japanese markdown
- `wiki-en/` — translated English markdown (git submodule)
- `akurasu.net/` — harvested Akurasu wiki pages (canonical term references)
- `cache/entity_catalog.jsonl` — canonical (EN, JP, category) triples
- `cache/en_terms/` — extracted EN game terms per file (JSONL)
- `cache/jp_terms/` — extracted JP game terms per file (JSONL, not yet generated)

## Save Editor (`fmw_save_editor.py`)

Decrypts, parses, modifies, and re-encrypts FMW DOSD intermission save files. PEP 723 standalone script, run via `uv run`.

```bash
uv run fmw_save_editor.py info saves/gsw_032.sav          # inspect save
uv run fmw_save_editor.py edit saves/gsw_032.sav --set Reimu=500  # set PP
uv run fmw_save_editor.py refund-all saves/gsw_032.sav --dry-run  # preview full refund
```

### Save Encryption

FMW DOSD saves use `buffer_encode_ext` — a per-byte rolling cipher with XOR and key-array derived from MD5/SHA1 hashes.

| Save Type | Files | Key |
|---|---|---|
| Intermission | `gsw_NNN.sav` | `avAVqqFDy2` |
| Battle/SLG/Autosave | `gsw_as_*.sav`, `gsw_qs.sav` | `aVb` |

**`hex_to_dec_fast` quirk**: GameMaker's hex parser uses `(((ord(c)+4)%23)-6)&15` which maps lowercase `a-f` → `3-8` (not `10-15`). This is NOT `int(h, 16)`. The game's cipher was built around this behavior. All Python implementations MUST use this formula, not standard hex parsing.

Keys were extracted by decompiling `data.win` with UndertaleModTool CLI — see `decompiled/CodeEntries/gml_GlobalScript_save_functions.gml` for the `GMBINOpenFileReadPW` calls.

### GMBIN Binary Format

Save payload structure: 4-byte int32 size header, then null-terminated strings, signed bytes/shorts/ints, floats, doubles.

- `ds_list_write_ext`: `[int16 count] [elements...]` — type codes: 0=byte, 2=short, 4=int, 6=float, 7=double, 8=string
- `ds_grid_write_ext`: `[int16 w] [int16 h] [column-major elements...]`
- Intermission saves have 95 fields in fixed order defined by `gml_GlobalScript_file_save.gml`
- Key data fields: `u_code` (unit names), `PP` (pilot points, int list), `tot_PP`, `skill_id` (string grid), `skill_lv` (byte grid)

### Modding Infrastructure

The game can be patched with the community `fmw_patches` framework:

```
fmw-patches/        # https://github.com/FMW-HUB/fmw_patches — xdelta patches + mod JSONs
modding-tool/        # https://github.com/Sanoi777/Fantasy-Maiden-Wars-DoSD-Modding-Tool
fmw-docs/            # https://github.com/FMW-HUB/fmw_docs — formulas, bugs, tutorials
```

Debug menu mod: patch `data.win` with xdelta, place `mods/Debugging/EnableDebugMenu.json` in the game's AppData. Provides in-game PP/kills/skill editing.

### Steam Deck Integration

Game runs via Proton. Save files at:
```
~/.local/share/Steam/steamapps/compatdata/3575980/pfx/drive_c/users/steamuser/AppData/Local/fmw_dosd/savedata/
```

Steam App ID: **3575980**. SSH access to Deck at `deck@10.0.0.66`.

### Decompiled GML Reference

UndertaleModTool CLI extracts GML from `data.win`:
```bash
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 ./utmt/UndertaleModCli dump data.win.original -o decompiled -c gml_GlobalScript_<function_name>
```

Key decompiled files in `decompiled/CodeEntries/`:
- `gml_GlobalScript_file_save.gml` — 95-field intermission save format
- `gml_GlobalScript_save_SLG.gml` — battle/autosave format
- `gml_GlobalScript_buffer_encode_ext.gml` — cipher algorithm
- `gml_GlobalScript_hex_to_dec_fast.gml` — the critical hex parsing quirk
- `gml_GlobalScript_save_functions.gml` — encryption keys (`avAVqqFDy2`, `aVb`)
- `gml_GlobalScript_GMBINOpenFileReadPW.gml` — confirms cipher is `buffer_encode_ext`
- `gml_GlobalScript_GMBINCloseFile.gml` — size prefix + encrypt-on-close
- `gml_GlobalScript_ds_list_write_ext.gml` — list serialization format
- `gml_GlobalScript_ds_grid_write_ext.gml` — grid serialization format

### Innate Skill Reference

Each character has innate generic skills (free, not PP-purchased). The save editor must distinguish these from purchased skills when doing refunds. Innate skills per character:

| Character | Innate Generic Skills |
|---|---|
| Reimu | MIKO (Shrine Maiden), KIAI (Morale Dodge L1-L6), GRAZE (Graze L1) |
| Keine | BLOCKING L1, SATTACK (Support Attack L1), SOKO (Grit L1-L5), SHINNEN (Conviction L1) |
| Youmu | BLOCKING L1-L3, KIAI (Morale Dodge L1-L6), SOKO (Grit L1-L5), P_HIT L1 |
| Marisa | MAHOU (Magician), KIAI (Morale Dodge L1-L7), P_HIT L1 |
| Nitori | SATTACK (Support Attack L1-L2), SGUARD (Support Defense L1-L2), P_HIT L1 |
| Alice | MAHOU (Magician L1-L2), ACCURATE (Precision Danmaku L1), SAVE_MP (SP Saver L1), P_EVADE L1 |
| Rumia | SGUARD (Support Defense L1), SOKO (Grit L1-L4), P_TURN (High Spirits L1), P_HIT L1 |
| Meiling | SOKO (Grit L1-L7), SGUARD (Support Defense L1-L2), P_GOTHIT (P-Damaged L1) |
| Sakuya | SHOSYA (Elegant L1), BLOCKING L1-L2, COUNTER (Pattern Recognition L1-L2) |
| Mokou | KIAI (Morale Dodge L1-L9), SOKO (Grit L1-L9) |
| Daiyousei | SGUARD (Support Defense L1-L2), KIAI (Morale Dodge L1-L3) |
| Cirno | KIAI (Morale Dodge L1-L7), USO (Lie Dodge L1), P_HIT L1 |
| Kurumi | SATTACK (Support Attack L1-L2), DAM+_SATTACK (Link Attack L1), P_TURN (High Spirits L1) |
| Ellie | BLOCKING L1, SOKO (Grit L1-L5), SGUARD (Support Defense L1-L2) |

The last slot (index 7) in the 8-slot skill grid is always the **Personal Skill** (free, set in formation screen). Empty generic slots use `"NONE"`.

## Output Directories

- `wiki-jp/` — raw scraped Japanese markdown
- `wiki-clean/` — cleaned Japanese markdown
- `wiki-en/` — translated English markdown (git submodule)
- `akurasu.net/` — harvested Akurasu wiki pages (canonical term references)
- `cache/entity_catalog.jsonl` — canonical (EN, JP, category) triples
- `cache/en_terms/` — extracted EN game terms per file (JSONL)
- `cache/jp_terms/` — extracted JP game terms per file (JSONL, not yet generated)
- `saves/` — working copy of save files for editing
- `saves-backup-20260411/` — pristine backup of all save files from Steam Deck
- `decompiled/CodeEntries/` — decompiled GML from data.win via UndertaleModTool
- `fmw-patches/` — community patching framework (cloned from GitHub)
- `modding-tool/` — GameMaker extraction tool (cloned from GitHub)
- `fmw-docs/` — community documentation (cloned from GitHub)
- `utmt/` — UndertaleModTool CLI binary (Linux)

## Reference Data

- `.claude/plans/active/00-fmw-data-sources.md` — primary wiki sources and game title reference table
- `.claude/plans/iterative-orbiting-karp.md` — save editor tool design plan
