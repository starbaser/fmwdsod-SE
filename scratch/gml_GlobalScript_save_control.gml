function save_control(arg0)
{
    var fid = arg0;
    var is_debug = false;
    GMBINWriteByte(fid, step);
    GMBINWriteShort(fid, obj_cursor.x);
    GMBINWriteShort(fid, obj_cursor.y);
    GMBINWriteInt(fid, x);
    GMBINWriteInt(fid, y);
    GMBINWriteInt(fid, num_of_bombs);
    GMBINWriteInt(fid, demo_on);
    GMBINWriteInt(fid, num_of_players);
    GMBINWriteInt(fid, num_of_enemies);
    GMBINWriteInt(fid, num_of_npcs);
    GMBINWriteInt(fid, num_of_turns);
    GMBINWriteInt(fid, stage_num_of_players);
    GMBINWriteInt(fid, stage_num_of_enemies);
    GMBINWriteInt(fid, stage_num_of_npcs);
    GMBINWriteInt(fid, stage_tot_turns);
    GMBINWriteInt(fid, stage_tot_beat);
    GMBINWriteInt(fid, stage_tot_beaten);
    GMBINWriteInt(fid, stage_tot_exp);
    GMBINWriteInt(fid, stage_tot_pp);
    GMBINWriteInt(fid, stage_tot_points);
    GMBINWriteInt(fid, stage_tot_spells_acquired);
    GMBINWriteInt(fid, stage_tot_spells);
    GMBINWriteInt(fid, stage_tot_cost0 * 2);
    GMBINWriteInt(fid, stage_tot_cost1 * 2);
    GMBINWriteInt(fid, stage_tot_bombs);
    GMBINWriteInt(fid, stage_wp_bonus);
    GMBINWriteInt(fid, stage_tot_spirits);
    GMBINWriteInt(fid, stage_tot_save);
    GMBINWriteInt(fid, stage_tot_reset);
    GMBINWriteInt(fid, sort_id);
    GMBINWriteInt(fid, sort_desc);
    GMBINWriteInt(fid, sort_rep);
    GMBINWriteInt(fid, sort_mode);
    GMBINWriteString(fid, purpose);
    GMBINWriteString(fid, defeat);
    GMBINWriteString(fid, WP_cond);
    GMBINWriteString(fid, sound_default_pp);
    GMBINWriteString(fid, sound_default_ep);
    GMBINWriteString(fid, sound_fix);
    GMBINWriteString(fid, ship_init);
    for (var i = 0; i < 2; i += 1)
    {
        GMBINWriteShort(fid, WP_val[i]);
    }
    ds_list_write_ext(fid, l_extended, 0);
    ds_list_write_ext(fid, tent_ID, 8);
    ds_list_write_ext(fid, tent_PP, 2);
    ds_list_write_ext(fid, tent_geki, 2);
    ds_list_write_ext(fid, tent_item, 8);
    ds_list_write_ext(fid, event_done, 0);
    ds_list_write_ext(fid, beaten_id, 8);
    ds_list_write_ext(fid, beaten_cost, 2);
    ds_map_write_ext(fid, tent_vnames, 7);
    ds_map_write_ext(fid, tent_snames, 8);
}
