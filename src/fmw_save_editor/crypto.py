"""FMW DOSD save file encryption/decryption.

Implements GameMaker's buffer_encode_ext cipher with the hex_to_dec_fast quirk.
Reference: decompiled/CodeEntries/gml_GlobalScript_buffer_encode_ext.gml
"""
import hashlib

INTERMISSION_KEY = "avAVqqFDy2"
SLG_KEY = "aVb"


def hex_to_dec_fast(h: str) -> int:
    """Convert hex string using GameMaker's quirky formula.

    GM uses (((ord(c)+4)%23)-6)&15 which maps lowercase a-f to 3-8,
    NOT the standard 10-15. All hashlib digests are lowercase, so this
    must be used instead of int(h, 16).

    Reference: gml_GlobalScript_hex_to_dec_fast.gml
    """
    r = 0
    for c in h:
        r = (r << 4) + (((ord(c) + 4) % 23 - 6) & 15)
    return r


def _derive_key_array(key_hash: str) -> list[int]:
    key_len = len(key_hash) // 2
    return [hex_to_dec_fast(key_hash[i * 2 : i * 2 + 2]) for i in range(key_len)]


def codec_ext(data: bytes | bytearray, is_encrypting: bool, enc_key: str) -> bytes:
    """Implement GameMaker's buffer_encode_ext XOR cipher.

    Reference: gml_GlobalScript_file_fast_crypt_ultra.gml
    """
    md5u = lambda s: hashlib.md5(s.encode("utf-16-le")).hexdigest()
    sha1u = lambda s: hashlib.sha1(s.encode("utf-16-le")).hexdigest()
    md5f = lambda s: hashlib.md5(s.encode("utf-8")).hexdigest()
    sha1f = lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest()

    kh = md5u(enc_key) + sha1u(enc_key) + md5f(enc_key) + sha1f(enc_key)
    kh2 = md5u(kh) + sha1u(kh) + md5f(kh) + sha1f(kh)
    kf = kh + kh2
    kl = len(kf) // 2
    ka = _derive_key_array(kf)

    sd = 1 if is_encrypting else -1
    bs = 128
    xs = 1
    kp = 0
    out = bytearray(len(data))

    for p in range(len(data)):
        if is_encrypting:
            out[p] = (((data[p] + bs + ka[kp]) % 256) ^ xs ^ ka[kp]) & 0xFF
        else:
            out[p] = (((data[p] ^ xs ^ ka[kp]) + bs) - ka[kp]) % 256
        xs += 1
        if xs > 5000:
            xs = 1
            kh = md5u(kh2) + sha1u(kh2) + md5f(kh2) + sha1f(kh2)
            kh2 = md5u(kh) + sha1u(kh) + md5f(kh) + sha1f(kh)
            kf = kh + kh2
            ka = _derive_key_array(kf)
        bs += sd * (ka[kl - 1 - kp] % 2)
        if bs > 255:
            bs = 1
        elif bs < 1:
            bs = 255
        kp = (kp + 1) % kl

    return bytes(out)


def decrypt_intermission(data: bytes | bytearray) -> bytearray:
    return bytearray(codec_ext(data, False, INTERMISSION_KEY))


def encrypt_intermission(data: bytes | bytearray) -> bytes:
    return codec_ext(data, True, INTERMISSION_KEY)


def decrypt_slg(data: bytes | bytearray) -> bytearray:
    return bytearray(codec_ext(data, False, SLG_KEY))


def encrypt_slg(data: bytes | bytearray) -> bytes:
    return codec_ext(data, True, SLG_KEY)
