function save_draw(arg0)
{
    var fid = arg0;
    var is_debug = false;
    GMBINWriteByte(fid, bg_spell_alpha * 100);
    GMBINWriteByte(fid, floor(room_width / 16));
    GMBINWriteByte(fid, floor(room_height / 16));
    for (var i = 0; i < floor(room_width / 16); i += 1)
    {
        for (var j = 0; j < floor(room_height / 16); j += 1)
        {
            GMBINWriteShort(fid, spot_MOV_total[i][j] * 100);
            GMBINWriteByte(fid, spot_wall[i][j]);
        }
    }
    GMBINWriteByte(fid, num_of_bullets);
    GMBINWriteByte(fid, num_of_spells);
    GMBINWriteByte(fid, num_of_skills);
    for (var i = 0; i < num_of_bullets; i += 1)
    {
        GMBINWriteByte(fid, floor(bullet_x0[i] / 16));
        GMBINWriteByte(fid, floor(bullet_y0[i] / 16));
        GMBINWriteShort(fid, bullet_PRY[i]);
        GMBINWriteShort(fid, bullet_DEF[i]);
        GMBINWriteShort(fid, bullet_MOV[i] * 100);
        GMBINWriteString(fid, bullet_ID[i]);
        GMBINWriteByte(fid, bullet_sort[i]);
        GMBINWriteShort(fid, num_spots_bullet[i]);
        for (var j = 0; j < num_spots_bullet[i]; j += 1)
        {
            GMBINWriteByte(fid, floor(bullet_x[i][j] / 16));
            GMBINWriteByte(fid, floor(bullet_y[i][j] / 16));
            GMBINWriteByte(fid, bullet_is_exists[i][j]);
        }
    }
    if (is_debug)
    {
        show_message("bullet done");
    }
    for (var i = 0; i < num_of_spells; i += 1)
    {
        GMBINWriteShort(fid, spell_char_id[i]);
        GMBINWriteString(fid, spell_name[i]);
        GMBINWriteByte(fid, spell_turns[i]);
        GMBINWriteByte(fid, spell_turns_max[i]);
        GMBINWriteByte(fid, spell_is_update[i]);
        GMBINWriteByte(fid, spell_is_bombed[i]);
        GMBINWriteByte(fid, spell_n_slots[i]);
        GMBINWriteByte(fid, spell_sort[i]);
        GMBINWriteDouble(fid, spell_color[i]);
        GMBINWriteShort(fid, spell_x0[i]);
        GMBINWriteShort(fid, spell_y0[i]);
        for (var j = 0; j < spell_n_slots[i]; j += 1)
        {
            GMBINWriteShort(fid, spell_PRY[i][j]);
            GMBINWriteShort(fid, spell_DEF[i][j]);
            GMBINWriteShort(fid, spell_MOV[i][j] * 100);
            GMBINWriteString(fid, spell_ID[i][j]);
        }
        GMBINWriteShort(fid, num_spots_spell[i]);
        for (var j = 0; j < num_spots_spell[i]; j += 1)
        {
            GMBINWriteByte(fid, floor(spell_x[i][j] / 16));
            GMBINWriteByte(fid, floor(spell_y[i][j] / 16));
            GMBINWriteByte(fid, spell_n[i][j]);
            GMBINWriteByte(fid, spell_is_exists[i][j]);
        }
    }
    for (var i = 0; i < num_of_skills; i += 1)
    {
        GMBINWriteShort(fid, skill_char_id[i]);
        GMBINWriteShort(fid, num_spots_skill[i]);
        GMBINWriteShort(fid, skill_val[i]);
        GMBINWriteString(fid, skill_ID[i]);
        GMBINWriteByte(fid, skill_sort[i]);
        for (var j = 0; j < num_spots_skill[i]; j += 1)
        {
            GMBINWriteByte(fid, floor(skill_x[i][j] / 16));
            GMBINWriteByte(fid, floor(skill_y[i][j] / 16));
        }
    }
    if (is_debug)
    {
        show_message("spell done");
    }
}
