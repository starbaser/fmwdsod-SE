function save_icons(arg0)
{
    var fid = arg0;
    with (all)
    {
        if (object_index == ObjIcon)
        {
            if (sort == "player")
            {
                save_icon_player2(fid);
            }
        }
    }
    GMBINWriteString(fid, "</players>");
    with (all)
    {
        if (object_index == ObjIcon)
        {
            if (sort != "player")
            {
                save_icon_enemy2(fid);
            }
        }
    }
    GMBINWriteString(fid, "</enemies>");
}
