function GMBINCloseFile(arg0)
{
    var buf = arg0;
    var pos = buffer_tell(buf);
    buffer_poke(buf, 0, buffer_s32, pos);
    if (global.GMBIN_MODE >= 1)
    {
        if (global.GMBIN_PASSWORD != "")
        {
            debug_write("GMBINCloseFile (write mode): encoding with password " + global.GMBIN_PASSWORD);
            var buf_enc = buffer_encode_ext(buf, true, global.GMBIN_PASSWORD);
            debug_write("Encoded buffer : size " + string(buffer_get_size(buf_enc)));
            buffer_save_os(buf_enc, global.GMBIN_FILENAME);
        }
        else
        {
            buffer_save_os(buf, global.GMBIN_FILENAME);
        }
    }
    buffer_delete(buf);
    global.GMBIN_MODE = 0;
    global.GMBIN_FILENAME = "";
    global.GMBIN_PASSWORD = "";
    global.GMBIN_IS_DEBUG = false;
}
