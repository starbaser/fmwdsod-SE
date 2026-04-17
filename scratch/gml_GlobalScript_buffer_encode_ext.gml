function buffer_encode_ext(arg0, arg1, arg2)
{
    var _filename_in = arg0;
    var _key_pos = 0;
    var _pos = 0;
    var _bit_shift = 128;
    var _xor_shift = 1;
    var _is_encrypting = arg1;
    var _enc_key = arg2;
    var _key_hash = md5_string_unicode(_enc_key) + sha1_string_unicode(_enc_key) + md5_string_utf8(_enc_key) + sha1_string_utf8(_enc_key);
    var _key_hash2 = md5_string_unicode(_key_hash) + sha1_string_unicode(_key_hash) + md5_string_utf8(_key_hash) + sha1_string_utf8(_key_hash);
    _key_hash = _key_hash + _key_hash2;
    var _key_len = string_length(_key_hash) div 2;
    var _shift_direction;
    if (_is_encrypting == true)
    {
        _shift_direction = 1;
    }
    else
    {
        _shift_direction = -1;
    }
    var _key_arr;
    for (var _i = 0; _i < _key_len; _i++)
    {
        _key_arr[_i] = hex_to_dec_fast(string_copy(_key_hash, (_i * 2) + 1, 2));
    }
    _xor_shift = _xor_shift % 10;
    var _file_buffer = _filename_in;
    var _len = buffer_get_size(_file_buffer);
    buffer_seek(_file_buffer, buffer_seek_start, _pos);
    while (_pos != _len)
    {
        var _data;
        switch (_shift_direction)
        {
            case 1:
                _data = ((buffer_read(_file_buffer, buffer_u8) + _bit_shift + _key_arr[_key_pos]) % 256) ^ _xor_shift ^ _key_arr[_key_pos];
                break;
            case -1:
                _data = (((buffer_read(_file_buffer, buffer_u8) ^ _xor_shift ^ _key_arr[_key_pos]) + _bit_shift) - _key_arr[_key_pos]) % 256;
                break;
        }
        _xor_shift += 1;
        if (_xor_shift > 5000)
        {
            _xor_shift = 1;
            _key_hash = md5_string_unicode(_key_hash2) + sha1_string_unicode(_key_hash2) + md5_string_utf8(_key_hash2) + sha1_string_utf8(_key_hash2);
            _key_hash2 = md5_string_unicode(_key_hash) + sha1_string_unicode(_key_hash) + md5_string_utf8(_key_hash) + sha1_string_utf8(_key_hash);
            _key_hash = _key_hash + _key_hash2;
            for (var _i = 0; _i < _key_len; _i++)
            {
                _key_arr[_i] = hex_to_dec_fast(string_copy(_key_hash, (_i * 2) + 1, 2));
            }
        }
        _bit_shift += (_shift_direction * (_key_arr[_key_len - 1 - _key_pos] % 2));
        if (_bit_shift > 255)
        {
            _bit_shift = 1;
        }
        else if (_bit_shift < 1)
        {
            _bit_shift = 255;
        }
        _key_pos += 1;
        if (_key_pos > (_key_len - 1))
        {
            _key_pos = 0;
        }
        buffer_seek(_file_buffer, buffer_seek_start, _pos);
        buffer_write(_file_buffer, buffer_u8, _data);
        _pos = buffer_tell(_file_buffer);
    }
    buffer_seek(_file_buffer, buffer_seek_start, 0);
    return _file_buffer;
}
