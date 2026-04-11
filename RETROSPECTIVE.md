# Retrospective: Reverse-Engineering the FMW DOSD Save Format

## How We Cracked the Fantasy Maiden Wars Save Encryption

### The Problem

Kyle was playing Fantasy Maiden Wars: Dream of the Stray Dreamer on his Steam Deck — a Touhou fan-made SRPG running via Proton. On Lunatic difficulty at Chapter 17, he realized he'd spent hundreds of PP (Pilot Points) on suboptimal generic skills across multiple characters. The game has no built-in PP refund mechanic. Skills once purchased with PP are permanent — the only reset path is a full New Game+ after completing the entire game.

The characters affected:
- **Reimu**: 430 PP spent on Predict (160 PP waste), Belief, P-Hit, P-Evade
- **Keine**: 280 PP spent but missing Support Defense — her most critical skill
- **Marisa**: 280 PP spent with questionable picks like Tipsy
- **Alice**: 250 PP spent with redundant P-Hit (her Calm temperament already provides Power on hits)

The question: could we edit the save files directly?

---

### Phase 1: Reconnaissance

We first searched for existing tools. The search turned up:

1. **FMW Patching Repository** (`github.com/FMW-HUB/fmw_patches`) — an xdelta-based modding framework with a debug menu mod that can add PP in-game
2. **FearlessRevolution Cheat Engine thread** — documented that PP is stored as doubles and is hard to scan, with the consensus being "just use the debug menu mod"
3. **FLiNG Trainer** — a commercial trainer with 20+ options but the PP cheat was removed in recent versions
4. **No save editor existed** for FMW DOSD

The debug menu mod was the community-endorsed approach. We cloned the repos, patched `data.win` with xdelta, and deployed the mod to the Steam Deck via SSH. But the debug menu only adds PP globally to all units — it can't selectively refund specific skills. And we discovered the game re-learns equipped skills on load, so just adding PP back didn't solve the problem. We needed to actually modify the save file.

---

### Phase 2: The Encryption Layer

FMW DOSD is a GameMaker game. Save files are binary blobs — no readable text at all:

```
00000000: 53ae 828b d9b8 db41 5db2 b0b9 6950 54c8  S......A]...iPT.
00000010: d755 a838 ccd5 3107 08e4 1d96 68a3 467e  .U.8..1.....h.F~
```

The modding tool repository contained GML source for two encryption functions:
- `buffer_encode` — a simple rolling-add cipher
- `buffer_encode_ext` — a more complex XOR cipher with MD5/SHA1-derived key arrays

We also found the game data encryption key `Fp1OUltT6n` in the modding tool's `extract_all_files_from_game_folder.gml`. We tried both ciphers with this key against the save files. Neither worked.

The save files clearly used a different encryption key than the game data files.

---

### Phase 3: Decompiling data.win

We downloaded UndertaleModTool CLI (a .NET GameMaker decompiler) and extracted GML bytecode from the game's `data.win`. The critical discovery was in `gml_GlobalScript_save_functions.gml`:

```gml
var fid = GMBINOpenFileReadPW(global.save_dir + fname, "avAVqqFDy2", false);
```

And for battle/autosaves:

```gml
var fid = GMBINOpenFileReadPW(arg0, "aVb", false);
```

Two passwords. Decompiling `GMBINOpenFileReadPW` revealed it was just a wrapper around `buffer_encode_ext`:

```gml
function GMBINOpenFileReadPW(arg0, arg1, arg2) {
    var buf = buffer_load(arg0);
    var buf_dec = buffer_encode_ext(buf, false, arg1);
    var size = buffer_read(buf_dec, buffer_s32);
    return buf_dec;
}
```

And `GMBINCloseFile` confirmed the write side: encrypt with `buffer_encode_ext`, prepend a 4-byte size header.

We had the keys. We had the algorithm. We tried decrypting. It partially worked — some recognizable fragments appeared in the output, but most bytes were garbled. Something was subtly wrong.

---

### Phase 4: The hex_to_dec_fast Breakthrough

The `buffer_encode_ext` cipher derives its key array from MD5/SHA1 hashes of the password. The hash hex strings are parsed into byte values using a function called `hex_to_dec_fast`. We decompiled it:

```gml
function hex_to_dec_fast(arg0) {
    var hex = arg0;
    var res = 0;
    for (var i = 1; i <= string_length(hex); i++) {
        var n = ord(string_char_at(hex, i));
        res = (res << 4) + ((((n + 4) % 23) - 6) & 15);
    }
    return res;
}
```

This is NOT standard hex parsing. We tested every hex character:

```
'0'-'9' → 0-9    ✓ (correct)
'a'-'f' → 3-8    ✗ (should be 10-15!)
'A'-'F' → 10-15  ✓ (correct)
```

**Lowercase hex letters a-f are parsed as 3-8 instead of 10-15.** The function only works correctly for uppercase hex and digits. But Python's `hashlib` returns lowercase hex digests. And GameMaker's `md5_string_unicode` also returns lowercase.

Our initial Python implementation used `int(h, 16)` to parse hex pairs — which gives correct results for both cases. This is equivalent to using `hex_to_dec_fast` on uppercase input. Since the hash digests are lowercase, we were getting different key arrays than the game.

We first tried uppercasing the hash outputs before parsing, thinking GameMaker must return uppercase. This made things **worse**, because the hash strings themselves get fed back into `md5_string_unicode` for the secondary key derivation — and `md5("ABCDEF")` ≠ `md5("abcdef")`. The hash chain depends on the exact case of the intermediate strings.

The solution was blindingly simple once we understood it: **use the exact `hex_to_dec_fast` formula on lowercase hex**. The game was designed around this "broken" parser. The entire cipher's key derivation produces different key arrays than standard hex would — and that's intentional (or at least, the cipher was tested and works with this behavior).

```python
def hex_to_dec_fast(h: str) -> int:
    r = 0
    for c in h:
        r = (r << 4) + (((ord(c) + 4) % 23 - 6) & 15)
    return r
```

With this fix, the meta file `data4.meta` decrypted to valid JSON. And the save files decrypted to readable structured data:

```
gsw_032.sav → size=5826, first string: "GSWX:1.2.4" ✓
gsw_as_007.sav → size=58290, first string: "20260410_123542_18Reimu" ✓
```

---

### Phase 5: Parsing the GMBIN Format

With decryption working, we needed to understand the binary payload format. More decompilation revealed:

**`ds_list_write_ext`**: Count is a `int16` (short), not int32. Element types: 0=byte, 2=short, 4=int, 6=float, 7=double, 8=null-terminated string.

**`ds_grid_write_ext`**: Width and height are `int16`. Data is stored **column-major** (outer loop = columns, inner = rows).

**`file_save.gml`**: 95 fields in fixed order. The key fields for PP editing:
- Field 48: `u_code` — list of unit name strings (e.g., "Reimu", "Keine")
- Field 58: `PP` — list of int32 pilot point values, one per unit
- Field 59: `tot_PP` — total PP earned per unit

We initially got the list format wrong (using int32 for counts instead of int16, and int32 for type-0 elements instead of bytes), which caused buffer overruns. We also initially read the skill grid in the wrong orientation — column-major means `grid[col][row]`, and with `col = unit_index`, `row = skill_slot`, not the other way around.

After fixing these issues, we could parse every field correctly and display all 18 characters with their PP values matching what the in-game screenshots showed.

---

### Phase 6: Building the Save Editor

PP values are fixed-width int32 at known byte offsets. The parser captures these offsets during traversal. Modifying PP is a simple `struct.pack_into('<i', buffer, offset, new_value)` — no need to reconstruct the binary or shift any surrounding data.

The first version of the editor supported:
- `info` — display all units with PP/tot_PP
- `edit --set Reimu=287` — set absolute PP values
- `refund-all` — set all PP to tot_PP (full refund)

Verification was done by re-decrypting the modified file and re-parsing to confirm values round-tripped correctly.

---

### Phase 7: The Skill Grid Problem

Pushing the modified save to the Steam Deck revealed a problem: **the game re-equipped the old skills on load**. Simply refunding PP wasn't enough — the purchased skills were still in the `skill_id` grid, and the game treated them as actively equipped.

We needed to:
1. Identify which skills were **innate** (free) vs **purchased** (PP-cost)
2. Clear purchased skills from the grid (set to `"NONE"`)
3. Refund the PP

The innate skill data came from the translated Japanese wiki (already indexed in our kitstore). We built a reference table mapping each character to their innate skill set.

But clearing skills in the grid meant changing string data — replacing `"MIKIRI"` (7 bytes) with `"NONE"` (5 bytes) shifts all subsequent byte offsets. We couldn't do in-place patching anymore.

The solution was a **splice-and-reconstruct** approach:
1. Parse the decrypted payload up to the skill grids, recording the byte offset
2. Build replacement skill grids using `GmbinWriter` with purchased skills set to `"NONE"`
3. Splice the new grids into the buffer, replacing the old grid bytes
4. Append the remaining payload (everything after the grids)
5. Re-parse to find the new PP offsets (they shifted due to the grid size change)
6. Patch PP values at the new offsets
7. Update the size header
8. Pad to original file size (GameMaker's buffer_grow uses powers of 2)
9. Re-encrypt

This worked. The modified save loaded cleanly on the Steam Deck with all purchased skills cleared and PP fully refunded.

---

### Phase 8: Productionizing

The one-off scripts were refactored into a proper Python package at `~/dev/projects/fmwdsod-SE/`:

```
src/fmw_save_editor/
├── crypto.py      # buffer_encode_ext + hex_to_dec_fast
├── gmbin.py       # GmbinReader + GmbinWriter
├── models.py      # UnitData, SaveHeader, IntermissionSave
├── parser.py      # 95-field intermission save parser
├── mutators.py    # PP set/delta/refund + write_save
└── cli.py         # tyro subcommands: info, edit, refund-all
```

---

### Key Lessons

**1. The "bug" was the feature.** `hex_to_dec_fast` isn't broken — the game was built and tested with this exact behavior. The cipher works because the encryption and decryption both use the same "wrong" key array. Treating it as a bug to fix (by using standard hex parsing) was the wrong approach.

**2. Roundtrip tests can mask implementation errors.** Our roundtrip test (encrypt → decrypt → compare) passed perfectly even with the wrong key derivation, because the same wrong key was used in both directions. Only testing against real game-produced data revealed the mismatch.

**3. The modding community had all the pieces.** The fmw_patches repo had the cipher algorithm. The Cheat Engine thread documented the save format quirks. UndertaleModTool could extract the keys. No single source had the complete picture, but combining them got us there.

**4. GameMaker's string encoding matters.** The secondary key derivation hashes the hex string itself. Since `md5("abc") ≠ md5("ABC")`, the case of the hash output directly affects all subsequent key material. We spent significant time trying uppercase hashes before realizing lowercase was correct.

**5. Binary format assumptions kill.** We initially assumed `ds_list_write_ext` used int32 counts (it uses int16) and int32 for type-0 elements (it uses bytes). These assumptions caused buffer overruns that were hard to debug because the corrupted data still contained recognizable fragments.

**6. Decompilation is the ground truth.** Every assumption about the save format was verified by decompiling the actual GML from `data.win`. The decompiled `file_save.gml` gave us the exact field order. The decompiled `hex_to_dec_fast.gml` gave us the cipher quirk. Without UndertaleModTool, we'd still be guessing.

---

### Timeline

The entire reverse-engineering effort — from "can you help me with skills" to a working save editor pushing modified saves to the Steam Deck — took place in a single conversation session. The critical breakthroughs:

1. **Finding the keys**: Decompiling `save_functions.gml` → `"avAVqqFDy2"` and `"aVb"`
2. **The hex_to_dec_fast quirk**: `(((ord(c)+4)%23)-6)&15` maps `a-f` → `3-8`
3. **Using the quirk correctly**: lowercase hashes + formula (not int(h,16), not uppercase)
4. **The ds_list format**: short counts, type 0 = bytes
5. **The skill grid problem**: purchased skills must be cleared, not just PP refunded

Each breakthrough unlocked the next step. The hex_to_dec_fast discovery was the pivotal moment — everything before it produced garbled output, everything after it worked cleanly.

---

### Tools Used

- **UndertaleModTool CLI** (Linux) — GameMaker data.win decompiler
- **Python 3.13** with hashlib, struct — cipher implementation and binary parsing
- **SSH + SCP** — remote save file transfer to/from Steam Deck
- **kitstore** (wiki-en) — translated Japanese strategy wiki for innate skill reference
- **fmw_patches** (GitHub) — community modding framework, provided cipher GML source
- **xdelta3** (via nix) — patching data.win for debug menu mod

### Files Decompiled

| File | What It Revealed |
|---|---|
| `gml_GlobalScript_save_functions.gml` | Encryption keys `avAVqqFDy2` and `aVb` |
| `gml_GlobalScript_GMBINOpenFileReadPW.gml` | GMBIN uses `buffer_encode_ext` underneath |
| `gml_GlobalScript_GMBINCloseFile.gml` | 4-byte size prefix + encrypt on close |
| `gml_GlobalScript_hex_to_dec_fast.gml` | The critical hex parsing quirk |
| `gml_GlobalScript_buffer_encode_ext.gml` | Full cipher algorithm |
| `gml_GlobalScript_file_save.gml` | 95-field intermission save format |
| `gml_GlobalScript_ds_list_write_ext.gml` | List format: short count + typed elements |
| `gml_GlobalScript_ds_grid_write_ext.gml` | Grid format: short w/h, column-major |
| `gml_GlobalScript_save_SLG.gml` | Battle save format and `aVb` key usage |
