# /// script
# requires-python = ">=3.12"
# dependencies = ["fmw-save-editor"]
#
# [tool.uv.sources]
# fmw-save-editor = { path = ".." }
# ///
"""Decrypt and byte-map an FMW DOSD quicksave (SLG) file.

Usage:
    uv run scratch/dump_quicksave.py saves/gsw_qs.sav
"""
from __future__ import annotations

import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

from fmw_save_editor.crypto import decrypt_slg
from fmw_save_editor.gmbin import GmbinReader


@dataclass
class ByteRegion:
    start: int
    end: int
    section: str
    field: str
    type_name: str
    value: str


class TrackedReader:
    """Wraps GmbinReader to record byte regions for every read."""

    def __init__(self, buf: bytes) -> None:
        self.r = GmbinReader(buf)
        self.regions: list[ByteRegion] = []
        self._section = ""

    @property
    def pos(self) -> int:
        return self.r.pos

    def section(self, name: str) -> None:
        self._section = name

    def _record(self, start: int, type_name: str, field: str, value) -> None:
        display = repr(value)
        if len(display) > 80:
            display = display[:77] + "..."
        self.regions.append(ByteRegion(start, self.r.pos, self._section, field, type_name, display))

    def string(self, field: str) -> str:
        start = self.r.pos
        v = self.r.read_string()
        self._record(start, "string", field, v)
        return v

    def byte(self, field: str) -> int:
        start = self.r.pos
        v = self.r.read_byte()
        self._record(start, "s8", field, v)
        return v

    def ubyte(self, field: str) -> int:
        start = self.r.pos
        v = self.r.read_ubyte()
        self._record(start, "u8", field, v)
        return v

    def bool_(self, field: str) -> bool:
        start = self.r.pos
        v = self.r.read_bool()
        self._record(start, "bool", field, v)
        return v

    def short(self, field: str) -> int:
        start = self.r.pos
        v = self.r.read_short()
        self._record(start, "s16", field, v)
        return v

    def ushort(self, field: str) -> int:
        start = self.r.pos
        v = self.r.read_ushort()
        self._record(start, "u16", field, v)
        return v

    def int_(self, field: str) -> int:
        start = self.r.pos
        v = self.r.read_int()
        self._record(start, "s32", field, v)
        return v

    def float_(self, field: str) -> float:
        start = self.r.pos
        v = self.r.read_float()
        self._record(start, "f32", field, v)
        return v

    def double(self, field: str) -> float:
        start = self.r.pos
        v = self.r.read_double()
        self._record(start, "f64", field, v)
        return v

    def list_(self, field: str, type_code: int) -> list:
        start = self.r.pos
        vals, _ = self.r.read_list(type_code)
        tc = {0: "byte", 2: "short", 4: "int", 6: "float", 7: "double", 8: "string"}
        self._record(start, f"list<{tc.get(type_code, '?')}>", field, f"[{len(vals)}] {vals}")
        return vals

    def grid(self, field: str, type_code: int) -> tuple[int, int, list[list]]:
        start = self.r.pos
        w, h, g = self.r.read_grid(type_code)
        tc = {0: "byte", 2: "short", 4: "int", 6: "float", 7: "double", 8: "string"}
        self._record(start, f"grid<{tc.get(type_code, '?')}>", field, f"{w}×{h}")
        return w, h, g

    def map_(self, field: str, type_code: int) -> dict:
        start = self.r.pos
        d = self.r.read_map(type_code)
        tc = {0: "byte", 2: "short", 4: "int", 6: "float", 7: "double", 8: "string"}
        self._record(start, f"map<str,{tc.get(type_code, '?')}>", field, f"[{len(d)}] {d}")
        return d

    def skip(self, n: int, field: str) -> bytes:
        start = self.r.pos
        data = self.r.buf[self.r.pos : self.r.pos + n]
        self.r.pos += n
        self._record(start, f"raw[{n}]", field, f"{n} bytes")
        return data


def parse_slg_header(t: TrackedReader) -> int:
    t.section("slg_header")
    t.string("SLG_ID")
    phase_id = t.byte("phase_id")
    if phase_id == 0 or phase_id == 5:
        t.ubyte("cost*2")
        t.list_("l_final", 0)
    return phase_id


def parse_version_block(t: TrackedReader) -> None:
    t.section("version_block")
    ver = t.string("version")
    is_autosave = t.bool_("is_autosave")
    if is_autosave:
        pos_val = t.int_("img_pos")
        size_val = t.int_("img_size")
        t.skip(size_val, "img_data")


def parse_file_save(t: TrackedReader) -> tuple[list[str], int, int, list[list]]:
    """Parse file_save() — 98 fields from gml_GlobalScript_file_save.gml."""
    t.section("file_save")
    t.string("GSWX_version")
    t.string("route")
    t.byte("level")
    t.float_("stage_num")
    t.string("stage_ID")
    t.short("tot_turns")
    t.int_("tot_points")
    t.short("tot_WP")
    t.double("datetime")
    t.double("sec")
    t.byte("is_NG0")
    t.byte("is_lvchg")
    t.byte("GSP")
    t.byte("GSP_max")
    t.byte("num_defeat")
    t.byte("is_IM_ini")
    t.string("bgm_default")
    t.string("team_name")
    t.int_("c_tot_points")
    t.int_("c_tot_WP")
    t.double("c_tot_sec")
    t.int_("c_atk_dam")
    t.int_("c_hit_dam")
    t.string("c_atk_data")
    t.string("c_hit_data")
    t.short("c_Oimo")
    t.short("c_Photo")
    t.short("c_Yume")
    t.short("c_Toyohime")
    t.short("c_Makura")
    t.short("c_Meko")
    t.byte("c_Akyu")
    t.byte("c_Lily")
    t.byte("is_NG1")

    t.list_("p_list", 0)
    t.list_("p_name_id", 2)
    t.list_("p_name_name", 8)
    t.list_("p_hist", 8)
    t.grid("pairs", 0)
    t.list_("d_pair", 0)
    t.list_("l_select", 0)
    t.list_("l_BGM", 8)
    t.grid("tune_lv", 0)
    t.grid("char_lv", 0)
    t.grid("skill_id", 8)
    t.grid("skill_lv", 0)
    item_w, item_h, item_grid = t.grid("item_id", 8)
    u_code = t.list_("u_code", 8)
    t.list_("u_data", 8)
    t.list_("BGM", 8)
    t.list_("rem_HP", 2)
    t.list_("rem_MP", 2)
    t.list_("rem_BL", 8)
    t.list_("tbonus", 0)
    t.list_("p_code", 8)
    t.list_("p_data", 8)
    t.list_("EXP", 2)
    t.list_("PP", 4)
    t.list_("tot_PP", 4)
    t.list_("geki", 2)
    t.list_("WP", 2)
    t.list_("skill_aq", 8)
    t.list_("rem_SP", 2)
    t.list_("rem_PW", 0)
    t.list_("wbonus", 0)
    t.list_("trust", 8)
    t.list_("updates_ID", 0)
    t.list_("updates_char", 8)
    t.list_("updates_val", 8)
    t.list_("u_code0", 8)
    t.list_("u_data0", 8)
    t.list_("p_code0", 8)
    t.list_("p_data0", 8)
    t.list_("PP0", 4)
    t.list_("geki0", 2)
    t.list_("item0", 0)
    t.list_("c_st_stage", 0)
    t.list_("c_st_level", 0)
    t.list_("c_st_turns", 2)
    t.list_("c_st_time", 4)
    t.list_("c_st_beat", 2)
    t.list_("c_st_enemies", 2)
    t.list_("c_st_beaten", 0)
    t.list_("c_st_points", 4)
    t.list_("c_st_spell0", 0)
    t.list_("c_st_spell1", 0)
    t.list_("c_st_bonus", 0)
    t.list_("c_st_defeat", 2)
    t.list_("c_st_save", 2)
    t.list_("c_st_load", 2)
    t.list_("ItemID", 8)
    t.list_("tot_num_of_items", 0)
    t.list_("num_of_items", 0)
    t.list_("FlagID", 8)
    t.list_("FlagIsOn", 0)
    return u_code, item_w, item_h, item_grid


def parse_save_control(t: TrackedReader) -> None:
    t.section("save_control")
    t.byte("step")
    t.short("cursor_x")
    t.short("cursor_y")
    t.int_("x")
    t.int_("y")
    t.int_("num_of_bombs")
    t.int_("demo_on")
    t.int_("num_of_players")
    t.int_("num_of_enemies")
    t.int_("num_of_npcs")
    t.int_("num_of_turns")
    t.int_("stage_num_of_players")
    t.int_("stage_num_of_enemies")
    t.int_("stage_num_of_npcs")
    t.int_("stage_tot_turns")
    t.int_("stage_tot_beat")
    t.int_("stage_tot_beaten")
    t.int_("stage_tot_exp")
    t.int_("stage_tot_pp")
    t.int_("stage_tot_points")
    t.int_("stage_tot_spells_acquired")
    t.int_("stage_tot_spells")
    t.int_("stage_tot_cost0_x2")
    t.int_("stage_tot_cost1_x2")
    t.int_("stage_tot_bombs")
    t.int_("stage_wp_bonus")
    t.int_("stage_tot_spirits")
    t.int_("stage_tot_save")
    t.int_("stage_tot_reset")
    t.int_("sort_id")
    t.int_("sort_desc")
    t.int_("sort_rep")
    t.int_("sort_mode")
    t.string("purpose")
    t.string("defeat")
    t.string("WP_cond")
    t.string("sound_default_pp")
    t.string("sound_default_ep")
    t.string("sound_fix")
    t.string("ship_init")
    t.short("WP_val[0]")
    t.short("WP_val[1]")
    t.list_("l_extended", 0)
    t.list_("tent_ID", 8)
    t.list_("tent_PP", 2)
    t.list_("tent_geki", 2)
    t.list_("tent_item", 8)
    t.list_("event_done", 0)
    t.list_("beaten_id", 8)
    t.list_("beaten_cost", 2)
    t.map_("tent_vnames", 7)
    t.map_("tent_snames", 8)


def parse_save_draw(t: TrackedReader) -> None:
    t.section("save_draw")
    t.byte("bg_spell_alpha_x100")
    map_w = t.byte("map_w_tiles")
    map_h = t.byte("map_h_tiles")
    for i in range(map_w):
        for j in range(map_h):
            t.short(f"spot_MOV[{i},{j}]_x100")
            t.byte(f"spot_wall[{i},{j}]")

    num_bullets = t.byte("num_of_bullets")
    num_spells = t.byte("num_of_spells")
    num_skills = t.byte("num_of_skills")

    for i in range(num_bullets):
        t.byte(f"bullet[{i}].x")
        t.byte(f"bullet[{i}].y")
        t.short(f"bullet[{i}].PRY")
        t.short(f"bullet[{i}].DEF")
        t.short(f"bullet[{i}].MOV_x100")
        t.string(f"bullet[{i}].ID")
        t.byte(f"bullet[{i}].sort")
        n_spots = t.short(f"bullet[{i}].num_spots")
        for j in range(n_spots):
            t.byte(f"bullet[{i}].spot[{j}].x")
            t.byte(f"bullet[{i}].spot[{j}].y")
            t.byte(f"bullet[{i}].spot[{j}].exists")

    for i in range(num_spells):
        t.short(f"spell[{i}].char_id")
        t.string(f"spell[{i}].name")
        t.byte(f"spell[{i}].turns")
        t.byte(f"spell[{i}].turns_max")
        t.byte(f"spell[{i}].is_update")
        t.byte(f"spell[{i}].is_bombed")
        n_slots = t.byte(f"spell[{i}].n_slots")
        t.byte(f"spell[{i}].sort")
        t.double(f"spell[{i}].color")
        t.short(f"spell[{i}].x0")
        t.short(f"spell[{i}].y0")
        for j in range(n_slots):
            t.short(f"spell[{i}].slot[{j}].PRY")
            t.short(f"spell[{i}].slot[{j}].DEF")
            t.short(f"spell[{i}].slot[{j}].MOV_x100")
            t.string(f"spell[{i}].slot[{j}].ID")
        n_spots = t.short(f"spell[{i}].num_spots")
        for j in range(n_spots):
            t.byte(f"spell[{i}].spot[{j}].x")
            t.byte(f"spell[{i}].spot[{j}].y")
            t.byte(f"spell[{i}].spot[{j}].n")
            t.byte(f"spell[{i}].spot[{j}].exists")

    for i in range(num_skills):
        t.short(f"skill[{i}].char_id")
        t.short(f"skill[{i}].num_spots")
        t.short(f"skill[{i}].val")
        t.string(f"skill[{i}].ID")
        n_spots_val = t.r.buf[t.r.pos - len(t.regions[-1].value) :] if False else 0
        t.byte(f"skill[{i}].sort")
        # num_spots was already read above; re-read from the region value
        # Actually we need the num_spots value — read it from the region
        # The num_spots field is 2 fields back in the region list
        num_spots_skill = int(t.regions[-4].value)
        for j in range(num_spots_skill):
            t.byte(f"skill[{i}].spot[{j}].x")
            t.byte(f"skill[{i}].spot[{j}].y")


def parse_icon_player(t: TrackedReader, icon_idx: int) -> None:
    t.section(f"icon_player[{icon_idx}]")
    marker = t.string("marker")
    assert marker == "<player>", f"Expected <player>, got {marker!r}"
    n_units = t.byte("n_units")
    t.short("icon_x")
    t.short("icon_y")

    for i in range(n_units):
        t.string(f"unit[{i}].data")
        num_weps = t.byte(f"unit[{i}].NumWeps")
        t.string(f"unit[{i}].sort")
        t.string(f"unit[{i}].landscape")
        uval_str = t.string(f"unit[{i}].uval")
        uval_type_str = t.string(f"unit[{i}].uval_type")
        t.short(f"unit[{i}].HP")
        t.short(f"unit[{i}].MP")
        t.short(f"unit[{i}].song_ID")
        t.short(f"unit[{i}].song_lv")
        t.short(f"unit[{i}].NumAct")
        t.string(f"unit[{i}].state_ID")
        t.double(f"unit[{i}].spirit_del")
        # NumPilots is encoded in the unit_data string — but the GML uses NumPilots[i]
        # which is an instance variable. We need to detect it from the data.
        # Looking at the GML: the loop is `for j in 0..NumPilots[i]-1`, but NumPilots
        # isn't written to the save. It's derived from unit_data at load time.
        # For players, NumPilots is typically 1 (single pilot per unit).
        num_pilots = 1
        for j in range(num_pilots):
            t.short(f"unit[{i}].pilot[{j}].level")
            t.short(f"unit[{i}].pilot[{j}].reserved")
            t.int_(f"unit[{i}].pilot[{j}].PP")
            t.short(f"unit[{i}].pilot[{j}].geki")
            t.short(f"unit[{i}].pilot[{j}].SP")
            t.short(f"unit[{i}].pilot[{j}].PW")
            t.short(f"unit[{i}].pilot[{j}].num_SA")
            t.short(f"unit[{i}].pilot[{j}].num_SG")
            t.double(f"unit[{i}].pilot[{j}].spirit_act")

        num_slots = t.byte(f"unit[{i}].NumSlots")
        for j in range(num_weps):
            t.byte(f"unit[{i}].ammo[{j}]")
        for j in range(num_slots):
            t.string(f"unit[{i}].equip[{j}]")

        num_ucs = t.byte(f"unit[{i}].NumUCs")
        for k in range(num_ucs):
            t.string(f"unit[{i}].UC[{k}].ID")
            t.byte(f"unit[{i}].UC[{k}].lv")
            t.byte(f"unit[{i}].UC[{k}].count")
            t.byte(f"unit[{i}].UC[{k}].max")

        n_uvals = uval_str.count("|") - 1
        for k in range(n_uvals):
            uval_type_val = int(uval_type_str.split("|")[k]) if k < len(uval_type_str.split("|")) else 0
            if uval_type_val == 0:
                t.byte(f"unit[{i}].uval_val[{k}]")
            else:
                t.string(f"unit[{i}].uval_val[{k}]")

    t.byte("pair_id")
    t.byte("control_id")
    t.byte("unit_id")
    t.byte("isActed")
    t.byte("isMoved")
    t.byte("isSlow")
    t.byte("isBlink")
    t.byte("isAlive")
    t.byte("isLoaded")
    t.byte("isUGround")
    t.byte("NumFPM")
    t.byte("step")
    t.byte("r_value")
    t.byte("prev_x")
    t.byte("prev_y")
    t.string("target_sort")
    t.byte("isAnime")
    t.byte("NumBullets")
    t.byte("image_xscale")


def parse_icon_enemy(t: TrackedReader, icon_idx: int) -> None:
    t.section(f"icon_enemy[{icon_idx}]")
    marker = t.string("marker")
    assert marker == "<enemy>", f"Expected <enemy>, got {marker!r}"
    n_units = t.byte("n_units")
    t.short("icon_x")
    t.short("icon_y")

    for i in range(n_units):
        t.string(f"unit[{i}].data")
        num_weps = t.byte(f"unit[{i}].NumWeps")
        t.byte(f"unit[{i}].level")
        t.byte(f"unit[{i}].tune_rate")
        t.string(f"unit[{i}].item")
        t.byte(f"unit[{i}].isOwnBomb")
        t.byte(f"unit[{i}].tune_add")
        t.string(f"unit[{i}].target_sort")
        t.string(f"unit[{i}].landscape")
        t.string(f"unit[{i}].sort")
        uval_str = t.string(f"unit[{i}].uval")
        uval_type_str = t.string(f"unit[{i}].uval_type")
        t.int_(f"unit[{i}].HP")
        t.int_(f"unit[{i}].MP")
        t.int_(f"unit[{i}].max_HP")
        t.int_(f"unit[{i}].max_MP")
        t.int_(f"unit[{i}].song_ID")
        t.string(f"unit[{i}].state_ID")

        num_pilots = 1
        for j in range(num_pilots):
            t.short(f"unit[{i}].pilot[{j}].level")
            t.short(f"unit[{i}].pilot[{j}].reserved")
            t.short(f"unit[{i}].pilot[{j}].PP")
            t.short(f"unit[{i}].pilot[{j}].geki")
            t.short(f"unit[{i}].pilot[{j}].SP")
            t.short(f"unit[{i}].pilot[{j}].PW")
            t.short(f"unit[{i}].pilot[{j}].num_SA")
            t.short(f"unit[{i}].pilot[{j}].num_SG")
            t.double(f"unit[{i}].pilot[{j}].spirit_act")

        for j in range(num_weps):
            t.byte(f"unit[{i}].ammo[{j}]")
        num_slots = 1
        for j in range(num_slots):
            t.string(f"unit[{i}].equip[{j}]")

        num_ucs = t.byte(f"unit[{i}].NumUCs")
        for j in range(num_ucs):
            t.byte(f"unit[{i}].UC[{j}].count")
            t.byte(f"unit[{i}].UC[{j}].max")

        n_uvals = uval_str.count("|") - 1
        for k in range(n_uvals):
            uval_type_val = int(uval_type_str.split("|")[k]) if k < len(uval_type_str.split("|")) else 0
            if uval_type_val == 0:
                t.byte(f"unit[{i}].uval_val[{k}]")
            else:
                t.string(f"unit[{i}].uval_val[{k}]")

    t.short("AI_move_x")
    t.short("AI_move_y")
    t.byte("control_id")
    t.byte("unit_id")
    t.byte("isActed")
    t.byte("isMoved")
    t.byte("isSelected")
    t.byte("isSlow")
    t.byte("isBlink")
    t.byte("isAlive")
    t.byte("step")
    t.byte("r_value")
    t.byte("NumBullets")
    t.byte("bullet_id")
    t.byte("isBattled")
    t.byte("AI_turns")
    t.byte("AI_move")
    t.byte("AI_attack")
    t.byte("AI_bullet")
    t.byte("AI_def")
    t.byte("AI_spirit")
    t.byte("AI_timer")
    t.byte("AI_move2")
    t.byte("AI_attack0")
    t.byte("AI_move0")
    t.string("target_sort")
    t.string("souki")
    t.string("AI_move_unit")
    t.string("AI_attack_unit")
    t.byte("image_xscale")


def parse_icons(t: TrackedReader) -> None:
    player_idx = 0
    while True:
        peek_pos = t.r.pos
        peek_end = t.r.buf.find(0, peek_pos)
        peek_str = t.r.buf[peek_pos:peek_end].decode("utf-8", errors="replace")
        if peek_str == "</players>":
            t.section("save_icons")
            t.string("end_players")
            break
        parse_icon_player(t, player_idx)
        player_idx += 1

    enemy_idx = 0
    while True:
        peek_pos = t.r.pos
        peek_end = t.r.buf.find(0, peek_pos)
        peek_str = t.r.buf[peek_pos:peek_end].decode("utf-8", errors="replace")
        if peek_str == "</enemies>":
            t.section("save_icons")
            t.string("end_enemies")
            break
        parse_icon_enemy(t, enemy_idx)
        enemy_idx += 1


def parse_objects(t: TrackedReader) -> None:
    t.section("save_objects")
    while True:
        peek_pos = t.r.pos
        peek_end = t.r.buf.find(0, peek_pos)
        peek_str = t.r.buf[peek_pos:peek_end].decode("utf-8", errors="replace")
        if peek_str == "</object>":
            t.string("end_objects")
            break
        t.string("object_marker")
        t.short("obj_x")
        t.short("obj_y")
        t.short("obj_index")

    while True:
        peek_pos = t.r.pos
        peek_end = t.r.buf.find(0, peek_pos)
        peek_str = t.r.buf[peek_pos:peek_end].decode("utf-8", errors="replace")
        if peek_str == "</item>":
            t.string("end_items")
            break
        t.string("item_marker")
        t.short("item_x")
        t.short("item_y")
        t.string("item_name")


def parse_save_etc(t: TrackedReader) -> None:
    t.section("save_etc")
    t.grid("SpellTotTent", 0)
    t.grid("SpellGotTent", 0)
    t.byte("beaten_count")
    t.byte("etc_stage_wp_bonus")
    t.byte("etc_stage_tot_spells_acquired")
    t.byte("etc_stage_tot_spells")
    t.int_("etc_num_of_turns")
    t.int_("etc_stage_num")
    t.byte("stage_is_clear")
    t.double("etc_sec")
    t.int_("etc_stage_tot_sec")
    t.int_("etc_stage_tot_reset")


def render_csv(regions: list[ByteRegion], total_size: int, out=sys.stdout) -> None:
    import csv

    w = csv.writer(out)
    w.writerow(["offset", "end", "size", "section", "field", "type", "value"])
    for r in regions:
        w.writerow([f"0x{r.start:04X}", f"0x{r.end:04X}", r.end - r.start, r.section, r.field, r.type_name, r.value])
    print(file=out)
    parsed = regions[-1].end
    print(f"# Total parsed: 0x{parsed:04X} / 0x{total_size:04X} bytes", file=out)
    if parsed == total_size:
        print("# Complete parse — no leftover bytes.", file=out)
    else:
        print(f"# Unparsed tail: {total_size - parsed} bytes", file=out)


def render_equipment_summary(
    u_code: list[str], item_w: int, item_h: int, item_grid: list[list], out=sys.stdout
) -> None:
    import csv

    print(file=out)
    print("# === Equipment Allocation (item_id grid) ===", file=out)
    w = csv.writer(out)
    headers = ["unit"] + [f"slot_{j}" for j in range(item_h)]
    w.writerow(headers)
    for col in range(item_w):
        name = u_code[col] if col < len(u_code) else f"?{col}"
        row_data = [item_grid[col][row] for row in range(item_h)]
        w.writerow([name] + row_data)


def render_section_summary(regions: list[ByteRegion], out=sys.stdout) -> None:
    print(file=out)
    print("# === Section Summary ===", file=out)
    import csv

    w = csv.writer(out)
    w.writerow(["section", "start", "end", "size", "fields"])
    current = None
    sec_start = 0
    sec_count = 0
    for r in regions:
        if r.section != current:
            if current is not None:
                w.writerow([current, f"0x{sec_start:04X}", f"0x{r.start:04X}", r.start - sec_start, sec_count])
            current = r.section
            sec_start = r.start
            sec_count = 0
        sec_count += 1
    if current is not None:
        w.writerow([current, f"0x{sec_start:04X}", f"0x{regions[-1].end:04X}", regions[-1].end - sec_start, sec_count])


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <quicksave.sav>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    raw = path.read_bytes()
    dec = decrypt_slg(raw)
    total_size = struct.unpack_from("<i", dec, 0)[0]

    print(f"# File: {path}  ({len(raw)} bytes encrypted, {total_size} bytes payload)", file=sys.stderr)

    t = TrackedReader(bytes(dec))
    u_code: list[str] = []
    item_w = item_h = 0
    item_grid: list[list] = []

    t.section("size_prefix")
    t.int_("total_size")

    try:
        parse_slg_header(t)
        parse_version_block(t)
        u_code, item_w, item_h, item_grid = parse_file_save(t)
        parse_save_control(t)
        parse_save_draw(t)
        parse_icons(t)
        parse_objects(t)
        parse_save_etc(t)
    except Exception as e:
        print(f"Parse error at offset 0x{t.pos:04X}: {e}", file=sys.stderr)
        print(f"Parsed {len(t.regions)} regions before failure", file=sys.stderr)

    render_csv(t.regions, total_size)
    render_section_summary(t.regions)
    if u_code and item_grid:
        render_equipment_summary(u_code, item_w, item_h, item_grid)


if __name__ == "__main__":
    main()
