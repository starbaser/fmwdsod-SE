function save_icon_enemy2(arg0)
{
    var fid = arg0;
    var is_debug = false;
    GMBINWriteString(fid, "<enemy>");
    GMBINWriteByte(fid, n_units);
    GMBINWriteShort(fid, x);
    GMBINWriteShort(fid, y);
    for (var i = 0; i < n_units; i += 1)
    {
        GMBINWriteString(fid, unit_data[i]);
        GMBINWriteByte(fid, NumWeps[i]);
        GMBINWriteByte(fid, level[i][0]);
        GMBINWriteByte(fid, tune_rate[i]);
        GMBINWriteString(fid, ds_list_find_value(ObjData.ItemID, item_id[i][0]));
        GMBINWriteByte(fid, isOwnBomb);
        GMBINWriteByte(fid, tune_add[i]);
        GMBINWriteString(fid, target_sort);
        GMBINWriteString(fid, landscape);
        GMBINWriteString(fid, sort);
        GMBINWriteString(fid, uval[i]);
        GMBINWriteString(fid, uval_type[i]);
        GMBINWriteInt(fid, current_HP[i]);
        GMBINWriteInt(fid, current_MP[i]);
        GMBINWriteInt(fid, max_HP[i]);
        GMBINWriteInt(fid, max_MP[i]);
        GMBINWriteInt(fid, song_ID[i]);
        GMBINWriteString(fid, state_ID[i]);
        for (var j = 0; j < NumPilots[i]; j += 1)
        {
            GMBINWriteShort(fid, level[i][j]);
            GMBINWriteShort(fid, 0);
            GMBINWriteShort(fid, PP[i][j]);
            GMBINWriteShort(fid, geki[i][j]);
            GMBINWriteShort(fid, current_SP[i][j]);
            GMBINWriteShort(fid, current_PW[i][j]);
            GMBINWriteShort(fid, num_SA[i][j]);
            GMBINWriteShort(fid, num_SG[i][j]);
            GMBINWriteDouble(fid, spirit_act[i][j]);
        }
        for (var j = 0; j < NumWeps[i]; j += 1)
        {
            GMBINWriteByte(fid, current_BL[i][j]);
        }
        for (var j = 0; j < NumSlots[i]; j += 1)
        {
            GMBINWriteString(fid, ds_list_find_value(ObjData.ItemID, item_id[i][j]));
        }
        GMBINWriteByte(fid, NumUCs[i]);
        for (var j = 0; j < NumUCs[i]; j += 1)
        {
            GMBINWriteByte(fid, num_UC[i][j]);
            GMBINWriteByte(fid, num_UC_max[i][j]);
        }
        for (var j = 0; j < (string_count("|", uval[i]) - 1); j += 1)
        {
            if (real(string_element(uval_type[i], j, 0)) == 0)
            {
                GMBINWriteByte(fid, uval_val[i][j]);
            }
            else
            {
                GMBINWriteString(fid, uval_val[i][j]);
            }
        }
    }
    GMBINWriteShort(fid, AI_move_x);
    GMBINWriteShort(fid, AI_move_y);
    GMBINWriteByte(fid, control_id);
    GMBINWriteByte(fid, unit_id);
    GMBINWriteByte(fid, isActed);
    GMBINWriteByte(fid, isMoved);
    GMBINWriteByte(fid, isSelected);
    GMBINWriteByte(fid, isSlow);
    GMBINWriteByte(fid, isBlink);
    GMBINWriteByte(fid, isAlive);
    GMBINWriteByte(fid, step);
    GMBINWriteByte(fid, r_value);
    GMBINWriteByte(fid, NumBullets);
    GMBINWriteByte(fid, bullet_id);
    GMBINWriteByte(fid, isBattled);
    GMBINWriteByte(fid, AI_turns);
    GMBINWriteByte(fid, AI_move);
    GMBINWriteByte(fid, AI_attack);
    GMBINWriteByte(fid, AI_bullet);
    GMBINWriteByte(fid, AI_def);
    GMBINWriteByte(fid, AI_spirit);
    GMBINWriteByte(fid, AI_timer);
    GMBINWriteByte(fid, AI_move2);
    GMBINWriteByte(fid, AI_attack0);
    GMBINWriteByte(fid, AI_move0);
    GMBINWriteString(fid, target_sort);
    GMBINWriteString(fid, souki);
    GMBINWriteString(fid, AI_move_unit);
    GMBINWriteString(fid, AI_attack_unit);
    GMBINWriteByte(fid, image_xscale);
    if (is_debug)
    {
        show_message("saving of " + char_code + " done");
    }
}
