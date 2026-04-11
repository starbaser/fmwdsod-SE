"""Parse FMW DOSD intermission save files.

Field order follows gml_GlobalScript_file_save.gml exactly.
"""
import struct
from pathlib import Path

from .crypto import decrypt_intermission
from .gmbin import GmbinReader
from .models import IntermissionSave, SaveHeader, UnitData


def parse_intermission_save(path: Path) -> IntermissionSave:
    """Decrypt and parse a gsw_NNN.sav intermission save."""
    raw = path.read_bytes()
    dec = decrypt_intermission(raw)
    total_size = struct.unpack_from("<i", dec)[0]
    payload = bytes(dec[:total_size])

    r = GmbinReader(buf=payload, pos=4)

    # ── Scalar header (fields 1–34) ──
    version = r.read_string()       # 1: "GSWX:X.X.X"
    route = r.read_string()         # 2: route
    level = r.read_byte()           # 3: difficulty
    stage_num = r.read_float()      # 4: stage_num
    stage_id = r.read_string()      # 5: stage_ID
    tot_turns = r.read_ushort()     # 6: tot_turns
    tot_points = r.read_int()       # 7: tot_points
    tot_wp = r.read_ushort()        # 8: tot_WP
    _date = r.read_double()         # 9: date
    playtime = r.read_double()      # 10: sec (playtime)
    r.read_byte()                   # 11: is_NG0
    r.read_byte()                   # 12: is_lvchg
    r.read_byte()                   # 13: GSP
    r.read_byte()                   # 14: GSP_max
    r.read_byte()                   # 15: num_defeat
    r.read_byte()                   # 16: is_IM_ini
    r.read_string()                 # 17: bgm_default
    r.read_string()                 # 18: team_name
    r.read_int()                    # 19: c_tot_points
    r.read_int()                    # 20: c_tot_WP
    r.read_double()                 # 21: c_tot_sec
    r.read_int()                    # 22: c_atk_dam
    r.read_int()                    # 23: c_hit_dam
    r.read_string()                 # 24: c_atk_data
    r.read_string()                 # 25: c_hit_data
    r.read_short()                  # 26: c_Oimo
    r.read_short()                  # 27: c_Photo
    r.read_short()                  # 28: c_Yume
    r.read_short()                  # 29: c_Toyohime
    r.read_short()                  # 30: c_Makura
    r.read_short()                  # 31: c_Meko
    r.read_byte()                   # 32: c_Akyu
    r.read_byte()                   # 33: c_Lily
    r.read_byte()                   # 34: is_NG1

    # ── Lists and grids (fields 35–49) ──
    r.skip_list(0)                  # 35: p_list
    r.skip_list(2)                  # 36: p_name_id
    r.skip_list(8)                  # 37: p_name_name
    r.skip_list(8)                  # 38: p_hist
    r.skip_grid(0)                  # 39: pairs
    r.skip_list(0)                  # 40: d_pair
    r.skip_list(0)                  # 41: l_select
    r.skip_list(8)                  # 42: l_BGM
    r.skip_grid(0)                  # 43: tune_lv
    r.skip_grid(0)                  # 44: char_lv
    r.skip_grid(8)                  # 45: skill_id
    r.skip_grid(0)                  # 46: skill_lv
    r.skip_grid(8)                  # 47: item_id

    # ── Unit codes (field 48) ──
    u_code, _ = r.read_list(8)

    # ── Skip to PP (fields 49–57) ──
    r.skip_list(8)                  # 49: u_data
    r.skip_list(8)                  # 50: BGM
    r.skip_list(2)                  # 51: rem_HP
    r.skip_list(2)                  # 52: rem_MP
    r.skip_list(8)                  # 53: rem_BL
    r.skip_list(0)                  # 54: tbonus
    r.skip_list(8)                  # 55: p_code
    r.skip_list(8)                  # 56: p_data
    r.skip_list(2)                  # 57: EXP

    # ── PP and tot_PP (fields 58–59) ──
    pp_vals, pp_offsets = r.read_list(4)
    tot_pp_vals, tot_pp_offsets = r.read_list(4)

    header = SaveHeader(
        version=version,
        route=route,
        level=level,
        stage_num=stage_num,
        stage_id=stage_id,
        tot_turns=tot_turns,
        tot_points=tot_points,
        tot_wp=tot_wp,
        playtime_sec=playtime,
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

    return IntermissionSave(
        header=header,
        units=units,
        raw_decrypted=dec,
        total_size=total_size,
        file_size=len(raw),
    )
