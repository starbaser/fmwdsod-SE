function GMBINOpenFileReadPW(arg0, arg1, arg2)
{
    global.GMBIN_MODE = 0;
    global.GMBIN_FILENAME = arg0;
    global.GMBIN_PASSWORD = arg1;
    global.GMBIN_IS_DEBUG = arg2;
    var buf = buffer_load(arg0);
    var buf_dec = buffer_encode_ext(buf, false, arg1);
    var size = buffer_read(buf_dec, buffer_s32);
    return buf_dec;
}
