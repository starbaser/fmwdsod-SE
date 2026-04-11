"""GMBIN binary format reader/writer.

Reference: gml_GlobalScript_ds_list_write_ext.gml, gml_GlobalScript_ds_grid_write_ext.gml
"""
import struct

import attrs


@attrs.define
class GmbinReader:
    """Cursor-based reader over a decrypted GMBIN buffer."""

    buf: bytes
    pos: int = 0

    def read_string(self) -> str:
        end = self.buf.find(0, self.pos)
        s = self.buf[self.pos : end].decode("utf-8", errors="replace")
        self.pos = end + 1
        return s

    def read_byte(self) -> int:
        (v,) = struct.unpack_from("<b", self.buf, self.pos)
        self.pos += 1
        return v

    def read_ubyte(self) -> int:
        (v,) = struct.unpack_from("<B", self.buf, self.pos)
        self.pos += 1
        return v

    def read_short(self) -> int:
        (v,) = struct.unpack_from("<h", self.buf, self.pos)
        self.pos += 2
        return v

    def read_ushort(self) -> int:
        (v,) = struct.unpack_from("<H", self.buf, self.pos)
        self.pos += 2
        return v

    def read_int(self) -> int:
        (v,) = struct.unpack_from("<i", self.buf, self.pos)
        self.pos += 4
        return v

    def read_float(self) -> float:
        (v,) = struct.unpack_from("<f", self.buf, self.pos)
        self.pos += 4
        return v

    def read_double(self) -> float:
        (v,) = struct.unpack_from("<d", self.buf, self.pos)
        self.pos += 8
        return v

    def _read_element(self, type_code: int):
        if type_code == 0:
            return self.read_byte()
        elif type_code == 2:
            return self.read_short()
        elif type_code == 4:
            return self.read_int()
        elif type_code == 6:
            return self.read_float()
        elif type_code == 7:
            return self.read_double()
        elif type_code == 8:
            return self.read_string()
        raise ValueError(f"Unknown GMBIN type code: {type_code}")

    def read_list(self, type_code: int) -> tuple[list, list[int]]:
        """Read ds_list_write_ext: [int16 count] [elements...].

        Returns (values, element_byte_offsets).
        """
        count = self.read_short()
        values: list = []
        offsets: list[int] = []
        for _ in range(count):
            offsets.append(self.pos)
            values.append(self._read_element(type_code))
        return values, offsets

    def skip_list(self, type_code: int) -> None:
        self.read_list(type_code)

    def read_grid(self, type_code: int) -> tuple[int, int, list[list]]:
        """Read ds_grid_write_ext: [int16 w] [int16 h] [column-major elements].

        Returns (width, height, grid[col][row]).
        """
        w = self.read_short()
        h = self.read_short()
        grid: list[list] = [[None] * h for _ in range(w)]
        for col in range(w):
            for row in range(h):
                grid[col][row] = self._read_element(type_code)
        return w, h, grid

    def skip_grid(self, type_code: int) -> None:
        self.read_grid(type_code)


class GmbinWriter:
    """Builder for GMBIN binary data."""

    def __init__(self) -> None:
        self.buf = bytearray()

    def write_string(self, s: str) -> None:
        self.buf.extend(s.encode("utf-8"))
        self.buf.append(0)

    def write_byte(self, v: int) -> None:
        self.buf.extend(struct.pack("<b", v))

    def write_short(self, v: int) -> None:
        self.buf.extend(struct.pack("<h", v))

    def write_int(self, v: int) -> None:
        self.buf.extend(struct.pack("<i", v))

    def write_float(self, v: float) -> None:
        self.buf.extend(struct.pack("<f", v))

    def write_double(self, v: float) -> None:
        self.buf.extend(struct.pack("<d", v))

    def _write_element(self, v, type_code: int) -> None:
        if type_code == 0:
            self.write_byte(v)
        elif type_code == 2:
            self.write_short(v)
        elif type_code == 4:
            self.write_int(v)
        elif type_code == 6:
            self.write_float(v)
        elif type_code == 7:
            self.write_double(v)
        elif type_code == 8:
            self.write_string(v)

    def write_list(self, values: list, type_code: int) -> None:
        self.write_short(len(values))
        for v in values:
            self._write_element(v, type_code)

    def write_grid(self, w: int, h: int, grid: list[list], type_code: int) -> None:
        self.write_short(w)
        self.write_short(h)
        for col in range(w):
            for row in range(h):
                self._write_element(grid[col][row], type_code)

    def get_bytes(self) -> bytes:
        return bytes(self.buf)
