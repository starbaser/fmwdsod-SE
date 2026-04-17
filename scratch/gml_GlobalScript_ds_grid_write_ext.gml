function ds_grid_write_ext(arg0, arg1, arg2)
{
    var fid = arg0;
    var grid = arg1;
    var type = arg2;
    GMBINWriteShort(fid, ds_grid_width(grid));
    GMBINWriteShort(fid, ds_grid_height(grid));
    for (var i = 0; i < ds_grid_width(grid); i += 1)
    {
        for (var j = 0; j < ds_grid_height(grid); j += 1)
        {
            switch (type)
            {
                case 0:
                    GMBINWriteByte(fid, ds_grid_get(grid, i, j));
                    break;
                case 2:
                    GMBINWriteShort(fid, ds_grid_get(grid, i, j));
                    break;
                case 4:
                    GMBINWriteInt(fid, ds_grid_get(grid, i, j));
                    break;
                case 8:
                    GMBINWriteString(fid, ds_grid_get(grid, i, j));
                    break;
            }
        }
    }
}
