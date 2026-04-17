function ds_map_write_ext(arg0, arg1, arg2)
{
    var fid = arg0;
    var map = arg1;
    var type = arg2;
    GMBINWriteShort(fid, ds_map_size(map));
    if (ds_map_size(map) > 0)
    {
        var key = ds_map_find_first(map);
        while (true)
        {
            if (is_real(key))
            {
                show_message("ERROR: Cannot write map for keys being real!");
                break;
            }
            else
            {
                GMBINWriteString(fid, key);
                switch (type)
                {
                    case 0:
                        GMBINWriteByte(fid, ds_map_find_value(map, key));
                        break;
                    case 2:
                        GMBINWriteShort(fid, ds_map_find_value(map, key));
                        break;
                    case 4:
                        GMBINWriteInt(fid, ds_map_find_value(map, key));
                        break;
                    case 6:
                        GMBINWriteFloat(fid, ds_map_find_value(map, key));
                        break;
                    case 7:
                        GMBINWriteDouble(fid, ds_map_find_value(map, key));
                        break;
                    case 8:
                        GMBINWriteString(fid, ds_map_find_value(map, key));
                        break;
                }
            }
            if (key == ds_map_find_last(map))
            {
                break;
            }
            else
            {
                key = ds_map_find_next(map, key);
            }
        }
    }
}
