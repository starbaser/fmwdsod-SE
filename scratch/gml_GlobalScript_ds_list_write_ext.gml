function ds_list_write_ext(arg0, arg1, arg2)
{
    var fid = arg0;
    var list = arg1;
    var type = arg2;
    GMBINWriteShort(fid, ds_list_size(list));
    switch (type)
    {
        case 0:
            for (var i = 0; i < ds_list_size(list); i += 1)
            {
                GMBINWriteByte(fid, ds_list_find_value(list, i));
            }
            break;
        case 2:
            for (var i = 0; i < ds_list_size(list); i += 1)
            {
                GMBINWriteShort(fid, ds_list_find_value(list, i));
            }
            break;
        case 4:
            for (var i = 0; i < ds_list_size(list); i += 1)
            {
                GMBINWriteInt(fid, ds_list_find_value(list, i));
            }
            break;
        case 6:
            for (var i = 0; i < ds_list_size(list); i += 1)
            {
                GMBINWriteFloat(fid, ds_list_find_value(list, i));
            }
            break;
        case 7:
            for (var i = 0; i < ds_list_size(list); i += 1)
            {
                GMBINWriteDouble(fid, ds_list_find_value(list, i));
            }
            break;
        case 8:
            for (var i = 0; i < ds_list_size(list); i += 1)
            {
                GMBINWriteString(fid, ds_list_find_value(list, i));
            }
            break;
    }
}
