function save_etc(arg0)
{
    ds_grid_write_ext(arg0, ObjData.SpellTotTent, 0);
    ds_grid_write_ext(arg0, ObjData.SpellGotTent, 0);
    GMBINWriteByte(arg0, ds_list_size(ObjControl.beaten_id));
    GMBINWriteByte(arg0, ObjControl.stage_wp_bonus);
    GMBINWriteByte(arg0, ObjControl.stage_tot_spells_acquired);
    GMBINWriteByte(arg0, ObjControl.stage_tot_spells);
    GMBINWriteInt(arg0, ObjControl.num_of_turns);
    GMBINWriteInt(arg0, global.stage_num);
    GMBINWriteByte(arg0, ObjControl.stage_is_clear);
    GMBINWriteDouble(arg0, global.sec);
    GMBINWriteInt(arg0, ObjControl.stage_tot_sec);
    GMBINWriteInt(arg0, ObjControl.stage_tot_reset);
}
