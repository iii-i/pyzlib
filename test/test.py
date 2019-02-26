import contextlib
import ctypes
import os
import subprocess
import tempfile
import unittest

import parameterized
import pyzlib


class TestCase(unittest.TestCase):
    def test_version(self):
        print(pyzlib.zlibVersion())

    def test_compile_flags(self):
        print(hex(pyzlib.zlibCompileFlags()))

    def test_inflate_deflate(self):
        with tempfile.TemporaryFile() as ifp:
            data = b'\n'.join([str(x).encode() for x in range(5000)])
            ifp.write(data)
            ifp.flush()
            ifp.seek(0)
            basedir = os.path.dirname(__file__)
            deflate = subprocess.Popen(
                [os.path.join(basedir, 'deflate.py')],
                stdin=ifp,
                stdout=subprocess.PIPE)
            try:
                with tempfile.TemporaryFile() as ofp:
                    subprocess.check_call(
                        [os.path.join(basedir, 'inflate.py')],
                        stdin=deflate.stdout,
                        stdout=ofp)
                    ofp.seek(0)
                    self.assertEqual(data, ofp.read())
            finally:
                if deflate.wait() != 0:
                    raise Exception('deflate failed')

    @staticmethod
    @contextlib.contextmanager
    def _make_deflate_stream(raw=False):
        strm = pyzlib.z_stream(
            zalloc=pyzlib.Z_NULL, free=pyzlib.Z_NULL,
            opaque=pyzlib.Z_NULL)
        if raw:
            err = pyzlib.deflateInit2(
                strm,
                level=pyzlib.Z_DEFAULT_COMPRESSION,
                method=pyzlib.Z_DEFLATED,
                windowBits=-15,
                memLevel=8,
                strategy=pyzlib.Z_DEFAULT_STRATEGY)
        else:
            err = pyzlib.deflateInit(strm, pyzlib.Z_DEFAULT_COMPRESSION)
        if err != pyzlib.Z_OK:
            raise Exception('deflateInit() failed: error %d' % err)
        try:
            yield strm
        finally:
            err = pyzlib.deflateEnd(strm)
            if err != pyzlib.Z_OK:
                raise Exception('deflateEnd() failed: error %d' % err)

    @staticmethod
    @contextlib.contextmanager
    def _make_inflate_stream(raw=False):
        strm = pyzlib.z_stream(
            next_in=pyzlib.Z_NULL, avail_in=0,
            zalloc=pyzlib.Z_NULL, free=pyzlib.Z_NULL,
            opaque=pyzlib.Z_NULL)
        if raw:
            err = pyzlib.inflateInit2(strm, windowBits=-15)
        else:
            err = pyzlib.inflateInit(strm)
        if err != pyzlib.Z_OK:
            raise Exception('inflateInit() failed: error %d' % err)
        try:
            yield strm
        finally:
            err = pyzlib.inflateEnd(strm)
            if err != pyzlib.Z_OK:
                raise Exception('inflateEnd() failed: error %d' % err)

    @staticmethod
    def _addressof_string_buffer(buf, offset=0):
        return ctypes.cast(ctypes.addressof(buf) + offset, ctypes.c_char_p)

    @staticmethod
    def _shl(buf, bits):
        buf_pos = 0
        value = 0
        value_bits = 0
        while bits >= 8:
            value |= ord(buf[buf_pos]) << value_bits
            buf_pos += 1
            value_bits += 8
            bits -= 8
        carry = 0
        for i in range(len(buf) - 1, buf_pos - 1, -1):
            next_carry = ord(buf[i]) & ((1 << bits) - 1)
            buf[i] = (ord(buf[i]) >> bits) | (carry << (8 - bits))
            carry = next_carry
        value |= carry << value_bits
        return value, buf_pos

    @parameterized.parameterized.expand(((bits,) for bits in range(0, 17)))
    def test_inflate_prime(self, bits):
        with self._make_deflate_stream(raw=True) as strm:
            buf = ctypes.create_string_buffer(b'hello')
            strm.next_in = self._addressof_string_buffer(buf)
            strm.avail_in = len(buf)
            zbuf = ctypes.create_string_buffer(
                pyzlib.deflateBound(strm, strm.avail_in))
            strm.next_out = self._addressof_string_buffer(zbuf)
            strm.avail_out = len(zbuf)
            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
        value, zbuf_pos = self._shl(zbuf, bits)
        with self._make_inflate_stream(raw=True) as strm:
            strm.next_in = self._addressof_string_buffer(zbuf, offset=zbuf_pos)
            strm.avail_in = len(zbuf) - zbuf_pos
            buf = ctypes.create_string_buffer(len(buf))
            strm.next_out = self._addressof_string_buffer(buf)
            strm.avail_out = len(buf)
            pyzlib.inflatePrime(strm, bits, value)
            err = pyzlib.inflate(strm, pyzlib.Z_NO_FLUSH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
            self.assertEqual(b'hello\0', bytes(buf))


if __name__ == '__main__':
    unittest.main()
