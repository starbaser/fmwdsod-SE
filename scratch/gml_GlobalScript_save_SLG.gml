function save_SLG(arg0, arg1)
{
    var buf = GMBINOpenFileWritePW(global.save_dir + arg0, "aVb", false);
    print("save_SLG: saving", arg0);
    print("-- SLG_ID  :", ObjControl.SLG_ID);
    print("-- phase_id:", ObjControl.phase_id);
    GMBINWriteString(buf, ObjControl.SLG_ID);
    GMBINWriteByte(buf, ObjControl.phase_id);
    if (arg1)
    {
        GMBINWriteByte(buf, cost * 2);
        ds_list_write_ext(buf, l_final, 0);
    }
    GMBINWriteString(buf, global.version);
    if (string_pos("_as", arg0) > 0)
    {
        buffer_write(buf, buffer_bool, true);
        autosave_add(global.save_dir + arg0, buf);
    }
    else
    {
        buffer_write(buf, buffer_bool, false);
    }
    save_global(buf);
    with (ObjControl)
    {
        save_control(buf);
    }
    with (ObjDraw)
    {
        save_draw(buf);
    }
    save_icons(buf);
    save_objects(buf);
    save_etc(buf);
    GMBINCloseFile(buf);
}

function load_SLG(arg0)
{
    var fid = GMBINOpenFileReadPW(arg0, "aVb", false);
    var debug = false;
    SLG_ID = GMBINReadString(fid);
    prev_phase_id = GMBINReadByte(fid);
    print("load_SLG: loading", arg0);
    print("-- SLG_ID  :", SLG_ID);
    print("-- phase id:", string(prev_phase_id));
    if (prev_phase_id == 0 || prev_phase_id == 5)
    {
        cost = GMBINReadUByte(fid) / 2;
        is_loaded = true;
        ds_list_read_ext(l_final, fid, 0);
    }
    var pos = GMBINGetPosition(fid);
    var ver = GMBINReadString(fid);
    if (get_version(ver) < 80)
    {
        GMBINSetPosition(fid, pos);
    }
    else
    {
        var img = buffer_read(fid, buffer_bool);
        if (img)
        {
            pos = buffer_read(fid, buffer_s32);
            var size = buffer_read(fid, buffer_s32);
            buffer_seek(fid, buffer_seek_relative, size);
        }
    }
    load_global(fid);
    load_control(fid);
    with (ObjDraw)
    {
        load_draw(fid);
    }
    load_icon_players2(fid);
    load_icon_enemies2(fid);
    load_objects(fid);
    load_etc(fid);
    GMBINCloseFile(fid);
    global.sys_stage_now = global.stage_num;
}

function load_SLG_meta(arg0)
{
    var fid = GMBINOpenFileReadPW(arg0, "aVb", false);
    var SLG_ID = GMBINReadString(fid);
    var p_id = GMBINReadByte(fid);
    print("load_SLG_meta: loading", arg0);
    print("-- SLG_ID  :", SLG_ID);
    print("-- phase id:", string(p_id));
    if (p_id == 0 || p_id == 5)
    {
        var list = ds_list_create();
        GMBINReadUByte(fid);
        ds_list_read_ext(list, fid, 0);
        ds_list_destroy(list);
    }
    var ver = GMBINReadString(fid);
    if (get_version(ver) >= 80)
    {
        var img = buffer_read(fid, buffer_bool);
        if (img)
        {
            var pos = buffer_read(fid, buffer_s32);
            var size = buffer_read(fid, buffer_s32);
            buffer_seek(fid, buffer_seek_relative, size);
        }
        else
        {
        }
        ver = GMBINReadString(fid);
        print(ver);
    }
    global.route = GMBINReadString(fid);
    GMBINReadByte(fid);
    global.stage_num = GMBINReadFloat(fid);
    global.stage_ID = GMBINReadString(fid);
    print("-- version  :", ver);
    print("-- route    :", global.route);
    print("-- stage_ID :", global.stage_ID);
    GMBINCloseFile(fid);
}

function SLG_generate_ID(arg0)
{
    var ID = string(current_year) + zfill(current_month, 2) + zfill(current_day, 2) + "_" + zfill(current_hour, 2) + zfill(current_minute, 2) + zfill(current_second, 2);
    return ID + "_" + arg0;
}

function SLG_check_data(arg0)
{
    var fid = GMBINOpenFileReadPW(arg0, "aVb", false);
    var SLG_ID = GMBINReadString(fid);
    var p_id = GMBINReadByte(fid);
    if (p_id == 0 || p_id == 5)
    {
        var list = ds_list_create();
        GMBINReadUByte(fid);
        ds_list_read_ext(list, fid, 0);
        ds_list_destroy(list);
    }
    var ver = GMBINReadString(fid);
    if (get_version(ver) >= 80)
    {
        var img = buffer_read(fid, buffer_bool);
        if (img)
        {
            var pos = buffer_read(fid, buffer_s32);
            var size = buffer_read(fid, buffer_s32);
            buffer_seek(fid, buffer_seek_relative, size);
        }
        else
        {
        }
        ver = GMBINReadString(fid);
    }
    GMBINReadString(fid);
    GMBINReadByte(fid);
    var stage_num = GMBINReadFloat(fid);
    var stage_ID = GMBINReadString(fid);
    GMBINReadShort(fid);
    GMBINReadInt(fid);
    GMBINReadShort(fid);
    GMBINReadDouble(fid);
    GMBINReadDouble(fid);
    var is_NG = GMBINReadUByte(fid);
    GMBINCloseFile(fid);
    return 
    {
        STAGE_NUM: stage_num,
        STAGE_ID: stage_ID,
        IS_NG: is_NG
    };
}
