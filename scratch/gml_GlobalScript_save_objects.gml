function save_objects(arg0)
{
    var fid = arg0;
    with (all)
    {
        if (string_count(sort, "obj_save|obj_marker|object") > 0)
        {
            GMBINWriteString(fid, "<object>");
            GMBINWriteShort(fid, x);
            GMBINWriteShort(fid, y);
            GMBINWriteShort(fid, object_index);
        }
    }
    GMBINWriteString(fid, "</object>");
    with (all)
    {
        if (string_count(sort, "item") > 0)
        {
            GMBINWriteString(fid, "<item>");
            GMBINWriteShort(fid, x);
            GMBINWriteShort(fid, y);
            GMBINWriteString(fid, item_name);
        }
    }
    GMBINWriteString(fid, "</item>");
}
