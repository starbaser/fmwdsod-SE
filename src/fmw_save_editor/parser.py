"""Parse FMW DOSD intermission save files.

Field order follows gml_GlobalScript_file_save.gml exactly.
"""
import struct
from pathlib import Path

from .crypto import decrypt_intermission
from .gmbin import GmbinReader
from .models import IntermissionSave, RawSaveField, RawSaveFields, SaveHeader, UnitData


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


def parse_all_fields(path: Path) -> RawSaveFields:
    """Decrypt and parse all 95 fields from an intermission save."""
    raw = path.read_bytes()
    dec = decrypt_intermission(raw)
    total_size = struct.unpack_from("<i", dec)[0]
    payload = bytes(dec[:total_size])
    r = GmbinReader(buf=payload, pos=4)

    fields: list[RawSaveField] = []

    def _scalar(name: str, method: str):
        if method == "write_string":
            return RawSaveField(name=name, kind="scalar", write_method=method, value=r.read_string())
        elif method == "write_byte":
            return RawSaveField(name=name, kind="scalar", write_method=method, value=r.read_byte())
        elif method == "write_short":
            return RawSaveField(name=name, kind="scalar", write_method=method, value=r.read_short())
        elif method == "write_int":
            return RawSaveField(name=name, kind="scalar", write_method=method, value=r.read_int())
        elif method == "write_float":
            return RawSaveField(name=name, kind="scalar", write_method=method, value=r.read_float())
        elif method == "write_double":
            return RawSaveField(name=name, kind="scalar", write_method=method, value=r.read_double())

    def _list(name: str, tc: int):
        vals, _ = r.read_list(tc)
        return RawSaveField(name=name, kind="list", write_method="write_list", type_code=tc, value=vals)

    def _grid(name: str, tc: int):
        w, h, g = r.read_grid(tc)
        return RawSaveField(name=name, kind="grid", write_method="write_grid", type_code=tc, width=w, height=h, grid=g)

    # Fields 1-34: scalars
    fields.append(_scalar("version", "write_string"))          # 1
    fields.append(_scalar("route", "write_string"))            # 2
    fields.append(_scalar("level", "write_byte"))              # 3
    fields.append(_scalar("stage_num", "write_float"))         # 4
    fields.append(_scalar("stage_ID", "write_string"))         # 5
    fields.append(_scalar("tot_turns", "write_short"))         # 6
    fields.append(_scalar("tot_points", "write_int"))          # 7
    fields.append(_scalar("tot_WP", "write_short"))            # 8
    fields.append(_scalar("date", "write_double"))             # 9
    fields.append(_scalar("sec", "write_double"))              # 10
    fields.append(_scalar("is_NG0", "write_byte"))             # 11
    fields.append(_scalar("is_lvchg", "write_byte"))           # 12
    fields.append(_scalar("GSP", "write_byte"))                # 13
    fields.append(_scalar("GSP_max", "write_byte"))            # 14
    fields.append(_scalar("num_defeat", "write_byte"))         # 15
    fields.append(_scalar("is_IM_ini", "write_byte"))          # 16
    fields.append(_scalar("bgm_default", "write_string"))      # 17
    fields.append(_scalar("team_name", "write_string"))        # 18
    fields.append(_scalar("c_tot_points", "write_int"))        # 19
    fields.append(_scalar("c_tot_WP", "write_int"))            # 20
    fields.append(_scalar("c_tot_sec", "write_double"))        # 21
    fields.append(_scalar("c_atk_dam", "write_int"))           # 22
    fields.append(_scalar("c_hit_dam", "write_int"))           # 23
    fields.append(_scalar("c_atk_data", "write_string"))       # 24
    fields.append(_scalar("c_hit_data", "write_string"))       # 25
    fields.append(_scalar("c_Oimo", "write_short"))            # 26
    fields.append(_scalar("c_Photo", "write_short"))           # 27
    fields.append(_scalar("c_Yume", "write_short"))            # 28
    fields.append(_scalar("c_Toyohime", "write_short"))        # 29
    fields.append(_scalar("c_Makura", "write_short"))          # 30
    fields.append(_scalar("c_Meko", "write_short"))            # 31
    fields.append(_scalar("c_Akyu", "write_byte"))             # 32
    fields.append(_scalar("c_Lily", "write_byte"))             # 33
    fields.append(_scalar("is_NG1", "write_byte"))             # 34

    # Fields 35-48: lists and grids
    fields.append(_list("p_list", 0))                          # 35
    fields.append(_list("p_name_id", 2))                       # 36
    fields.append(_list("p_name_name", 8))                     # 37
    fields.append(_list("p_hist", 8))                          # 38
    fields.append(_grid("pairs", 0))                           # 39
    fields.append(_list("d_pair", 0))                          # 40
    fields.append(_list("l_select", 0))                        # 41
    fields.append(_list("l_BGM", 8))                           # 42
    fields.append(_grid("tune_lv", 0))                         # 43
    fields.append(_grid("char_lv", 0))                         # 44
    fields.append(_grid("skill_id", 8))                        # 45
    fields.append(_grid("skill_lv", 0))                        # 46
    fields.append(_grid("item_id", 8))                         # 47
    fields.append(_list("u_code", 8))                          # 48

    # Fields 49-57: unit data lists
    fields.append(_list("u_data", 8))                          # 49
    fields.append(_list("BGM", 8))                             # 50
    fields.append(_list("rem_HP", 2))                          # 51
    fields.append(_list("rem_MP", 2))                          # 52
    fields.append(_list("rem_BL", 8))                          # 53
    fields.append(_list("tbonus", 0))                          # 54
    fields.append(_list("p_code", 8))                          # 55
    fields.append(_list("p_data", 8))                          # 56
    fields.append(_list("EXP", 2))                             # 57

    # Fields 58-59: PP
    fields.append(_list("PP", 4))                              # 58
    fields.append(_list("tot_PP", 4))                          # 59

    # Fields 60-76: more lists
    fields.append(_list("geki", 2))                            # 60
    fields.append(_list("WP", 2))                              # 61
    fields.append(_list("skill_aq", 8))                        # 62
    fields.append(_list("rem_SP", 2))                          # 63
    fields.append(_list("rem_PW", 0))                          # 64
    fields.append(_list("wbonus", 0))                          # 65
    fields.append(_list("trust", 8))                           # 66
    fields.append(_list("updates_ID", 0))                      # 67
    fields.append(_list("updates_char", 8))                    # 68
    fields.append(_list("updates_val", 8))                     # 69
    fields.append(_list("u_code0", 8))                         # 70
    fields.append(_list("u_data0", 8))                         # 71
    fields.append(_list("p_code0", 8))                         # 72
    fields.append(_list("p_data0", 8))                         # 73
    fields.append(_list("PP0", 4))                             # 74
    fields.append(_list("geki0", 2))                           # 75
    fields.append(_list("item0", 0))                           # 76

    # Fields 77-90: chapter stats
    fields.append(_list("c_st_stage", 0))                      # 77
    fields.append(_list("c_st_level", 0))                      # 78
    fields.append(_list("c_st_turns", 2))                      # 79
    fields.append(_list("c_st_time", 4))                       # 80
    fields.append(_list("c_st_beat", 2))                       # 81
    fields.append(_list("c_st_enemies", 2))                    # 82
    fields.append(_list("c_st_beaten", 0))                     # 83
    fields.append(_list("c_st_points", 4))                     # 84
    fields.append(_list("c_st_spell0", 0))                     # 85
    fields.append(_list("c_st_spell1", 0))                     # 86
    fields.append(_list("c_st_bonus", 0))                      # 87
    fields.append(_list("c_st_defeat", 2))                     # 88
    fields.append(_list("c_st_save", 2))                       # 89
    fields.append(_list("c_st_load", 2))                       # 90

    # Fields 91-95: items and flags
    fields.append(_list("ItemID", 8))                          # 91
    fields.append(_list("tot_num_of_items", 0))                # 92
    fields.append(_list("num_of_items", 0))                    # 93
    fields.append(_list("FlagID", 8))                          # 94
    fields.append(_list("FlagIsOn", 0))                        # 95

    return RawSaveFields(fields=fields, raw_decrypted=dec, total_size=total_size)
