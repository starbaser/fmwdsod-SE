function save_global_init()
{
    var debug = false;
    global.sav_exist = ds_list_create();
    global.sav_ver = ds_list_create();
    global.sav_route = ds_list_create();
    global.sav_level = ds_list_create();
    global.sav_stage = ds_list_create();
    global.sav_ID = ds_list_create();
    global.sav_turns = ds_list_create();
    global.sav_point = ds_list_create();
    global.sav_WP = ds_list_create();
    global.sav_date = ds_list_create();
    global.sav_time = ds_list_create();
    global.sav_NG = ds_list_create();
    global.sav_title = ds_list_create();
    global.sav_chg = ds_list_create();
    global.sav_date0 = ds_list_create();
    global.sav_locked = ds_list_create();
    global.sav_broken = ds_list_create();
    var date0 = 0;
    var ind = 0;
    if (debug)
    {
        print("save_global_init: Searching for IM save data...");
    }
    var create_meta = !file_exists(global.save_dir + "save.meta");
    if (debug)
    {
        print("create_meta:", create_meta);
    }
    for (var i = 0; i < global.sav_max; i++)
    {
        var fname = "gsw_" + zfill(i, 3) + ".sav";
        if (!file_exists(global.save_dir + fname) || !create_meta)
        {
            ds_list_set(global.sav_exist, i, false);
            ds_list_set(global.sav_ver, i, "");
            ds_list_set(global.sav_route, i, "");
            ds_list_set(global.sav_level, i, -1);
            ds_list_set(global.sav_stage, i, -1);
            ds_list_set(global.sav_ID, i, "");
            ds_list_set(global.sav_turns, i, -1);
            ds_list_set(global.sav_point, i, -1);
            ds_list_set(global.sav_WP, i, -1);
            ds_list_set(global.sav_date, i, "");
            ds_list_set(global.sav_date0, i, 0);
            ds_list_set(global.sav_time, i, 0);
            ds_list_set(global.sav_NG, i, 0);
            ds_list_set(global.sav_title, i, "");
            ds_list_set(global.sav_chg, i, false);
            ds_list_set(global.sav_locked, i, false);
            ds_list_set(global.sav_broken, i, false);
        }
        else
        {
            if (debug)
            {
                print("-- Found", fname);
            }
            var date = save_global_update(i);
            if (date != -4 && date > date0)
            {
                ind = i;
                date0 = date;
            }
        }
    }
    if (create_meta)
    {
        save_meta_create();
    }
    else
    {
    }
    global.sav_index = ind;
}

function save_global_update(arg0)
{
    var date0 = 0;
    var ind = 0;
    var fname = "gsw_" + zfill(arg0, 3) + ".sav";
    var date;
    try
    {
        var fid = GMBINOpenFileReadPW(global.save_dir + fname, "avAVqqFDy2", false);
        var exist = true;
        var ver = GMBINReadString(fid);
        var route = GMBINReadString(fid);
        var level = GMBINReadByte(fid);
        var stage = GMBINReadFloat(fid);
        var ID = GMBINReadString(fid);
        var turns = GMBINReadUShort(fid);
        var point = GMBINReadInt(fid);
        var WP = GMBINReadUShort(fid);
        date = GMBINReadDouble(fid);
        var d_str = date_datetime_string2(date, 0);
        var time = GMBINReadDouble(fid);
        var NG = GMBINReadUByte(fid);
        var chg = GMBINReadByte(fid);
        var str = get_stage_title(ID);
        var title = get_stage_title_full(str, stage, ID, -1, route);
        GMBINCloseFile(fid);
        if (get_version(global.version) < 120)
        {
            if (get_version(ver) >= 100)
            {
                return -4;
            }
        }
        ds_list_set(global.sav_exist, arg0, exist);
        ds_list_set(global.sav_ver, arg0, ver);
        ds_list_set(global.sav_route, arg0, route);
        ds_list_set(global.sav_level, arg0, level);
        ds_list_set(global.sav_stage, arg0, stage);
        ds_list_set(global.sav_ID, arg0, ID);
        ds_list_set(global.sav_turns, arg0, turns);
        ds_list_set(global.sav_point, arg0, point);
        ds_list_set(global.sav_WP, arg0, WP);
        ds_list_set(global.sav_date, arg0, d_str);
        ds_list_set(global.sav_time, arg0, time);
        ds_list_set(global.sav_NG, arg0, NG);
        ds_list_set(global.sav_title, arg0, title);
        ds_list_set(global.sav_chg, arg0, chg);
        ds_list_set(global.sav_date0, arg0, date);
        ds_list_set(global.sav_locked, arg0, false);
        ds_list_set(global.sav_broken, arg0, false);
        global.sav_index = arg0;
    }
    catch (_exception)
    {
        ds_list_set(global.sav_exist, arg0, false);
        ds_list_set(global.sav_ver, arg0, "");
        ds_list_set(global.sav_route, arg0, "");
        ds_list_set(global.sav_level, arg0, -1);
        ds_list_set(global.sav_stage, arg0, -1);
        ds_list_set(global.sav_ID, arg0, "");
        ds_list_set(global.sav_turns, arg0, -1);
        ds_list_set(global.sav_point, arg0, -1);
        ds_list_set(global.sav_WP, arg0, -1);
        ds_list_set(global.sav_date, arg0, "");
        ds_list_set(global.sav_date0, arg0, 0);
        ds_list_set(global.sav_time, arg0, 0);
        ds_list_set(global.sav_NG, arg0, 0);
        ds_list_set(global.sav_title, arg0, "");
        ds_list_set(global.sav_chg, arg0, false);
        ds_list_set(global.sav_locked, arg0, false);
        ds_list_set(global.sav_broken, arg0, true);
        date = -4;
    }
    return date;
}

function take_snapshot(arg0, arg1, arg2, arg3, arg4, arg5)
{
    var spr = sprite_create_from_surface(application_surface, arg0, arg1, arg2, arg3, false, true, 0, 0);
    var sur = surface_create(arg4, arg5);
    surface_set_target(sur);
    gpu_set_tex_filter(true);
    draw_sprite_ext(spr, 0, 0, 0, arg4 / sprite_get_width(spr), arg5 / sprite_get_height(spr), 0, c_white, 1);
    gpu_set_tex_filter(false);
    var spr_out = sprite_create_from_surface(sur, 0, 0, arg4, arg5, 0, 0, 0, 0);
    surface_reset_target();
    sprite_delete(spr);
    return [spr_out, sur];
}

function autosave_init()
{
    var debug = 0;
    global.as_data = ds_list_create();
    var list = ds_list_create();
    if (debug)
    {
        print("save_global_init: Searching for autosave data...");
    }
    var files = glob(global.save_dir + "gsw_as_*.sav");
    var i = array_length(files) - 1;
    while (i >= 0)
    {
        var file = global.save_dir + files[i];
        if (!file_exists(file))
        {
        }
        else
        {
            var map = autosave_get_data(file, debug);
            if (map != -1)
            {
                ds_list_add(global.as_data, map);
                ds_list_add(list, ds_map_find_value(map, "turns"));
            }
        }
        i--;
    }
    ds_list_sort_ext2(global.as_data, list, 1);
    ds_list_destroy(list);
}

function autosave_get_data(arg0, arg1 = false)
{
    var map = ds_map_create();
    try
    {
        var fid = GMBINOpenFileReadPW(arg0, "aVb", false);
        var ID = GMBINReadString(fid);
        var val = GMBINReadByte(fid);
        if (val == 0 || val == 5)
        {
            GMBINReadUByte(fid);
            ds_list_read_ext(-1, fid, 0);
        }
        var ver = GMBINReadString(fid);
        if (get_version(ver) < 80)
        {
            ds_map_destroy(map);
            var png = string_replace(arg0, ".sav", ".png");
            if (file_exists(png))
            {
                file_delete(png);
            }
            GMBINCloseFile(fid);
            return -1;
        }
        var img = buffer_read(fid, buffer_bool);
        var pos = buffer_read(fid, buffer_s32);
        var size = buffer_read(fid, buffer_s32);
        var buf = buffer_create(16, buffer_grow, 1);
        buffer_copy(fid, pos, size, buf, 0);
        var surf = surface_create(176, 99);
        var buf2 = buffer_decompress(buf);
        var spr = -1;
        if (buf2 != -1)
        {
            buffer_set_surface(buf2, surf, 0);
            spr = sprite_create_from_surface(surf, 0, 0, 176, 99, false, 0, 0, 0);
        }
        else
        {
            print(arg0, "error loading surface!");
            spr = -1;
        }
        surface_free(surf);
        buffer_delete(buf);
        buffer_delete(buf2);
        buffer_seek(fid, buffer_seek_relative, size);
        ver = GMBINReadString(fid);
        var route = GMBINReadString(fid);
        var level = GMBINReadByte(fid);
        var st_num = GMBINReadFloat(fid);
        var st_ID = GMBINReadString(fid);
        GMBINSeekEOF(fid);
        GMBINSeekFromCurrent(fid, -29);
        var beaten = GMBINReadUByte(fid);
        var got_wp = GMBINReadUByte(fid);
        var spell0 = GMBINReadByte(fid);
        var spell1 = GMBINReadByte(fid);
        var turns = GMBINReadInt(fid);
        var num = GMBINReadInt(fid);
        var clear = GMBINReadByte(fid);
        var tsec = GMBINReadDouble(fid);
        var time = GMBINReadInt(fid);
        if (val == 0)
        {
            turns = 0;
        }
        GMBINCloseFile(fid);
        if (arg1)
        {
            print("---- Filename :", arg0);
            print("---- SLG_ID   :", ID);
            print("---- turn     :", string(turns));
            print("---- image    :", spr);
        }
        ds_map_set(map, "fname", arg0);
        ds_map_set(map, "image", spr);
        ds_map_set(map, "SLG_ID", ID);
        ds_map_set(map, "stage_ID", st_ID);
        ds_map_set(map, "got_wp", got_wp > 0);
        ds_map_set(map, "spell0", spell0);
        ds_map_set(map, "spell1", spell1);
        ds_map_set(map, "turns", turns);
        ds_map_set(map, "time", time);
        ds_map_set(map, "beaten", beaten);
        ds_map_set(map, "phase_id", val);
        return map;
    }
    catch (_exception)
    {
        ds_map_destroy(map);
        return -1;
    }
}

function autosave_clear(arg0, arg1)
{
    var debug = 0;
    if (debug)
    {
        print("autosave_clear: searching invalid data...");
    }
    var i = ds_list_size(global.as_data) - 1;
    while (i >= 0)
    {
        var map = ds_list_find_value(global.as_data, i);
        if (ds_map_find_value(map, "SLG_ID") != arg0 || ds_map_find_value(map, "turns") >= arg1)
        {
            var file = ds_map_find_value(map, "fname");
            var spr = ds_map_find_value(map, "image");
            var img = string_replace(file, ".sav", ".png");
            if (file_exists(file))
            {
                file_delete(file);
            }
            if (surface_exists(spr))
            {
                surface_free(spr);
            }
            if (file_exists(img))
            {
                file_delete(img);
            }
            if (debug)
            {
                print("Deleted", file, "(SLG_ID", ds_map_find_value(map, "SLG_ID"), ", turn", string(ds_map_find_value(map, "turns")) + ")");
            }
            ds_map_destroy(map);
            ds_list_delete(global.as_data, i);
        }
        i--;
    }
}

function autosave_add(arg0, arg1)
{
    var map = ds_map_create();
    var sprs = take_snapshot(320, 180, 640, 360, 176, 99);
    ds_map_set(map, "fname", arg0);
    ds_map_set(map, "image", sprs[0]);
    ds_map_set(map, "SLG_ID", ObjControl.SLG_ID);
    ds_map_set(map, "stage_ID", global.stage_ID);
    ds_map_set(map, "got_wp", ObjControl.stage_wp_bonus > 0);
    ds_map_set(map, "spell0", ObjControl.stage_tot_spells_acquired);
    ds_map_set(map, "spell1", ObjControl.stage_tot_spells);
    ds_map_set(map, "turns", ObjControl.num_of_turns * (ObjControl.phase_id > 0) * 1);
    ds_map_set(map, "time", ObjControl.stage_tot_sec);
    ds_map_set(map, "beaten", ds_list_size(ObjControl.beaten_id));
    ds_map_set(map, "phase_id", ObjControl.phase_id);
    var buf_img = buffer_create(16, buffer_grow, 1);
    buffer_get_surface(buf_img, sprs[1], 0);
    surface_free(sprs[1]);
    var buf_img2 = buffer_compress(buf_img, 0, buffer_get_size(buf_img));
    var pos0 = buffer_tell(arg1);
    var pos = buffer_get_size(arg1);
    var size = buffer_get_size(buf_img2);
    buffer_write(arg1, buffer_s32, pos);
    buffer_write(arg1, buffer_s32, size);
    var pos2 = buffer_tell(arg1);
    buffer_poke(arg1, pos0, buffer_s32, pos2);
    buffer_copy(buf_img2, 0, size, arg1, pos2);
    buffer_seek(arg1, buffer_seek_relative, size);
    buffer_delete(buf_img);
    buffer_delete(buf_img2);
    ds_list_add(global.as_data, map);
}

function save_limit_stages()
{
    var allowed_IDs = ["01Reimu", "02Reimu", "01Marisa", "02Marisa", "03Common"];
    for (var i = 0; i < ds_list_size(global.sav_exist); i++)
    {
        if (array_in(ds_list_find_value(global.sav_ID, i), allowed_IDs) < 0 || ds_list_find_value(global.sav_NG, i))
        {
            ds_list_set(global.sav_locked, i, true);
        }
    }
}
