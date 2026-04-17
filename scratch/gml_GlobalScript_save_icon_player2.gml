function save_icon_player2(arg0)
{
    var fid = arg0;
    var is_debug = false;
    GMBINWriteString(fid, "<player>");
    GMBINWriteByte(fid, n_units);
    GMBINWriteShort(fid, x);
    GMBINWriteShort(fid, y);
    for (var i = 0; i < n_units; i += 1)
    {
        GMBINWriteString(fid, unit_data[i]);
        GMBINWriteByte(fid, NumWeps[i]);
        GMBINWriteString(fid, sort);
        GMBINWriteString(fid, landscape);
        GMBINWriteString(fid, uval[i]);
        GMBINWriteString(fid, uval_type[i]);
        GMBINWriteShort(fid, current_HP[i]);
        GMBINWriteShort(fid, current_MP[i]);
        GMBINWriteShort(fid, song_ID[i]);
        GMBINWriteShort(fid, song_lv[i]);
        GMBINWriteShort(fid, NumAct[i]);
        GMBINWriteString(fid, state_ID[i]);
        GMBINWriteDouble(fid, spirit_del[i]);
        for (var j = 0; j < NumPilots[i]; j += 1)
        {
            GMBINWriteShort(fid, level[i][j]);
            GMBINWriteShort(fid, 0);
            GMBINWriteInt(fid, PP[i][j]);
            GMBINWriteShort(fid, geki[i][j]);
            GMBINWriteShort(fid, current_SP[i][j]);
            GMBINWriteShort(fid, current_PW[i][j]);
            GMBINWriteShort(fid, num_SA[i][j]);
            GMBINWriteShort(fid, num_SG[i][j]);
            GMBINWriteDouble(fid, spirit_act[i][j]);
        }
        GMBINWriteByte(fid, NumSlots[i]);
        for (var j = 0; j < NumWeps[i]; j += 1)
        {
            GMBINWriteByte(fid, current_BL[i][j]);
        }
        for (var j = 0; j < NumSlots[i]; j += 1)
        {
            GMBINWriteString(fid, ds_list_find_value(ObjData.ItemID, item_id[i][j]));
        }
        GMBINWriteByte(fid, NumUCs[i]);
        for (var k = 0; k < NumUCs[i]; k += 1)
        {
            GMBINWriteString(fid, UC_ID[i][k]);
            GMBINWriteByte(fid, UC_lv[i][k]);
            GMBINWriteByte(fid, num_UC[i][k]);
            GMBINWriteByte(fid, num_UC_max[i][k]);
        }
        for (var k = 0; k < (string_count("|", uval[i]) - 1); k += 1)
        {
            if (real(string_element(uval_type[i], k, 0)) == 0)
            {
                GMBINWriteByte(fid, uval_val[i][k]);
            }
            else
            {
                GMBINWriteString(fid, uval_val[i][k]);
            }
        }
    }
    GMBINWriteByte(fid, pair_id);
    GMBINWriteByte(fid, control_id);
    GMBINWriteByte(fid, unit_id);
    GMBINWriteByte(fid, isActed);
    GMBINWriteByte(fid, isMoved);
    GMBINWriteByte(fid, isSlow);
    GMBINWriteByte(fid, isBlink);
    GMBINWriteByte(fid, isAlive);
    GMBINWriteByte(fid, isLoaded);
    GMBINWriteByte(fid, isUGround);
    GMBINWriteByte(fid, NumFPM);
    GMBINWriteByte(fid, step);
    GMBINWriteByte(fid, r_value);
    GMBINWriteByte(fid, prev_x);
    GMBINWriteByte(fid, prev_y);
    GMBINWriteString(fid, target_sort);
    GMBINWriteByte(fid, isAnime);
    GMBINWriteByte(fid, NumBullets);
    GMBINWriteByte(fid, image_xscale);
    if (is_debug)
    {
        show_message("saving of " + char_code + " done");
    }
}
