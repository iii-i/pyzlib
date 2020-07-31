#!/usr/bin/env python3
import contextlib
import ctypes
import itertools
import os
import random
import subprocess
import tempfile
import unittest
import zlib

import parameterized
import pyzlib


def gen_hello(r):
    while True:
        yield b'hello\n'


def gen_seq(r):
    i = 0
    while True:
        yield ('%d\n' % i).encode()
        i += 1


def gen_nulls(r):
    while True:
        yield b'\0' * 4096


def gen_zeros_ones(r):
    while True:
        yield bytes(r.choice((b'0', b'1'), 4096))


def gen_random(r):
    while True:
        yield bytes(r.getrandbits(8) for _ in range(4096))


class Gen(object):
    def __init__(self, chunks):
        self.chunks = chunks
        self.buffer = bytearray()

    def __call__(self, n):
        while len(self.buffer) < n:
            self.buffer.extend(next(self.chunks))
        result = self.buffer[:n]
        del self.buffer[:n]
        return result


def gen_mix(r):
    gs = [
        Gen(f(r))
        for f in (
            gen_hello,
            gen_seq,
            gen_nulls,
            gen_zeros_ones,
            gen_random,
        )
    ]
    while True:
        yield r.choice(gs)(r.randint(1, 65536))


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
    def _make_deflate_stream(
            raw=False,
            level=pyzlib.Z_DEFAULT_COMPRESSION,
            mem_level=8,
            strategy=pyzlib.Z_DEFAULT_STRATEGY,
    ):
        strm = pyzlib.z_stream(
            zalloc=pyzlib.Z_NULL, free=pyzlib.Z_NULL,
            opaque=pyzlib.Z_NULL)
        if raw:
            err = pyzlib.deflateInit2(
                strm,
                level=level,
                method=pyzlib.Z_DEFLATED,
                windowBits=-15,
                memLevel=mem_level,
                strategy=strategy,
            )
        else:
            err = pyzlib.deflateInit(strm, level)
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
    def _addressof_bytearray(buf):
        return ctypes.cast(ctypes.addressof(
            (ctypes.c_char * len(buf)).from_buffer(buf)),
            ctypes.c_char_p)

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
            zbuf_len = len(zbuf) - strm.avail_out
        value, zbuf_pos = self._shl(zbuf, bits)
        with self._make_inflate_stream(raw=True) as strm:
            strm.next_in = self._addressof_string_buffer(zbuf, offset=zbuf_pos)
            strm.avail_in = zbuf_len - zbuf_pos
            buf = ctypes.create_string_buffer(len(buf))
            strm.next_out = self._addressof_string_buffer(buf)
            strm.avail_out = len(buf)
            pyzlib.inflatePrime(strm, bits, value)
            err = pyzlib.inflate(strm, pyzlib.Z_NO_FLUSH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
            self.assertEqual(b'hello\0', bytes(buf))

    def _set_dictionary(self, strm, gen, size):
        buf = bytearray(gen(size))
        err = pyzlib.deflateSetDictionary(
            strm, self._addressof_bytearray(buf), len(buf))
        self.assertEqual(pyzlib.Z_OK, err)
        return buf

    def _gen_buf(self, gen, size, dict):
        result = bytearray()
        result += gen(size // 3)
        result += dict[:size // 3]
        result += gen(size - len(result))
        return result

    SET_DICTIONARY_SIZES = [1 << x for x in range(0, 17, 4)]

    @parameterized.parameterized.expand(
        itertools.product(*([SET_DICTIONARY_SIZES] * 4)))
    def test_set_dictionary(
            self, dict1_size, buf2_size, dict3_size, buf4_size):
        gen = Gen(gen_random(random.Random(2024749321)))
        with tempfile.NamedTemporaryFile() as zfp:
            with self._make_deflate_stream(raw=True) as strm:
                dict1 = self._set_dictionary(strm, gen, dict1_size)
                buf2 = self._gen_buf(gen, buf2_size, dict1)
                strm.next_in = self._addressof_bytearray(buf2)
                strm.avail_in = len(buf2)
                while True:
                    zbuf = ctypes.create_string_buffer(4096)
                    strm.next_out = ctypes.cast(
                        ctypes.addressof(zbuf),
                        ctypes.c_char_p)
                    strm.avail_out = len(zbuf)
                    err = pyzlib.deflate(strm, pyzlib.Z_BLOCK)
                    self.assertEqual(pyzlib.Z_OK, err)
                    zfp.write(zbuf[:len(zbuf) - strm.avail_out])
                    if strm.avail_out != 0:
                        break
                dict3 = self._set_dictionary(strm, gen, dict3_size)
                buf4 = self._gen_buf(gen, buf4_size, dict1 + dict3)
                strm.next_in = self._addressof_bytearray(buf4)
                strm.avail_in = len(buf4)
                stream_end = False
                while not stream_end:
                    zbuf = ctypes.create_string_buffer(4096)
                    strm.next_out = ctypes.cast(
                        ctypes.addressof(zbuf),
                        ctypes.c_char_p)
                    strm.avail_out = len(zbuf)
                    err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
                    if err == pyzlib.Z_STREAM_END:
                        stream_end = True
                    else:
                        self.assertEqual(pyzlib.Z_OK, err)
                    zfp.write(zbuf[:len(zbuf) - strm.avail_out])
            zfp.flush()
            zfp.seek(0)
            inflated = bytearray()
            with self._make_inflate_stream(raw=True) as strm:
                err = pyzlib.inflateSetDictionary(
                    strm, self._addressof_bytearray(dict1), len(dict1))
                self.assertEqual(pyzlib.Z_OK, err)
                stream_end = False
                while not stream_end:
                    zbuf = bytearray(zfp.read(256))
                    if len(zbuf) == 0:
                        break
                    strm.next_in = ctypes.addressof(
                        (ctypes.c_char * len(zbuf)).from_buffer(zbuf))
                    strm.avail_in = len(zbuf)
                    while True:
                        buf = ctypes.create_string_buffer(4096)
                        strm.next_out = ctypes.cast(
                            ctypes.addressof(buf),
                            ctypes.c_char_p)
                        strm.avail_out = len(buf)
                        err = pyzlib.inflate(strm, pyzlib.Z_BLOCK)
                        inflated += buf[:len(buf) - strm.avail_out]
                        if err == pyzlib.Z_STREAM_END:
                            stream_end = True
                            break
                        if err == pyzlib.Z_BUF_ERROR:
                            break
                        self.assertEqual(pyzlib.Z_OK, err)
                        if strm.data_type & 128 != 0:
                            if strm.total_out == len(buf2):
                                err = pyzlib.inflateSetDictionary(
                                    strm, self._addressof_bytearray(dict3),
                                    len(dict3))
                                self.assertEqual(pyzlib.Z_OK, err)
                self.assertEqual(buf2 + buf4, inflated)

    def test_compress(self):
        dest = bytearray(pyzlib.compressBound(4096))
        source = bytearray(b'A' * 4096)
        err, dest_len = pyzlib.compress(
            self._addressof_bytearray(dest),
            len(dest),
            self._addressof_bytearray(source),
            len(source))
        self.assertEqual(pyzlib.Z_OK, err)
        self.assertLessEqual(dest_len, len(dest))
        self.assertEqual(source, zlib.decompress(dest[:dest_len]))

    @parameterized.parameterized.expand(((level,) for level in range(1, 10)))
    def test_compress2(self, level):
        dest = bytearray(128)
        source = bytearray(b'A' * 4096)
        err, dest_len = pyzlib.compress2(
            self._addressof_bytearray(dest),
            len(dest),
            self._addressof_bytearray(source),
            len(source),
            level)
        self.assertEqual(pyzlib.Z_OK, err)
        self.assertLessEqual(dest_len, len(dest))
        self.assertEqual(source, zlib.decompress(dest[:dest_len]))

    def test_uncompress(self):
        plain = bytearray(b'A' * 4096)
        source = bytearray(zlib.compress(plain))
        dest = bytearray(len(plain))
        err, dest_len = pyzlib.uncompress(
            self._addressof_bytearray(dest),
            len(dest),
            self._addressof_bytearray(source),
            len(source))
        self.assertEqual(pyzlib.Z_OK, err)
        self.assertLessEqual(dest_len, len(dest))
        self.assertEqual(plain, dest)

    def test_uncompress2(self):
        plain = bytearray(b'A' * 4096)
        source = bytearray(zlib.compress(plain))
        dest = bytearray(len(plain))
        err, dest_len, source_len = pyzlib.uncompress2(
            self._addressof_bytearray(dest),
            len(dest),
            self._addressof_bytearray(source),
            len(source))
        self.assertEqual(pyzlib.Z_OK, err)
        self.assertLessEqual(dest_len, len(dest))
        self.assertEqual(source_len, len(source))
        self.assertEqual(plain, dest)

    @staticmethod
    @contextlib.contextmanager
    def limit_avail_in(strm, max_size):
        avail_in0 = strm.avail_in
        avail_in1 = min(avail_in0, max_size)
        strm.avail_in = avail_in1
        yield
        consumed = avail_in1 - strm.avail_in
        strm.avail_in = avail_in0 - consumed

    @staticmethod
    @contextlib.contextmanager
    def limit_avail_out(strm, max_size):
        avail_out0 = strm.avail_out
        avail_out1 = min(avail_out0, max_size)
        strm.avail_out = avail_out1
        yield
        consumed = avail_out1 - strm.avail_out
        strm.avail_out = avail_out0 - consumed

    def _check_inflate(
            self, dest, compressed_size, plain, raw=False, dictionary=None):
        plain2 = bytearray(len(plain))
        with self._make_inflate_stream(raw=raw) as strm:
            if raw and dictionary is not None:
                err = pyzlib.inflateSetDictionary(
                    strm, dictionary, len(dictionary))
                self.assertEqual(pyzlib.Z_OK, err)
            strm.next_in = self._addressof_bytearray(dest)
            strm.avail_in = compressed_size
            strm.next_out = self._addressof_bytearray(plain2)
            strm.avail_out = len(plain2)
            err = pyzlib.inflate(strm, pyzlib.Z_NO_FLUSH)
            if not raw and dictionary is not None:
                self.assertEqual(pyzlib.Z_NEED_DICT, err)
                err = pyzlib.inflateSetDictionary(
                    strm, dictionary, len(dictionary))
                self.assertEqual(pyzlib.Z_OK, err)
                err = pyzlib.inflate(strm, pyzlib.Z_NO_FLUSH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
            self.assertEqual(0, strm.avail_out)
            self.assertEqual(plain, plain2)

    def test_deflate_params(self):
        gen = Gen(gen_random(random.Random(2097987671)))
        plain = gen(1024 * 1024)
        dest = bytearray(len(plain) * 2)
        chunk_size = len(plain) // 400
        with self._make_deflate_stream() as strm:
            strm.next_in = self._addressof_bytearray(plain)
            strm.avail_in = len(plain)
            strm.next_out = self._addressof_bytearray(dest)
            strm.avail_out = len(dest)
            for level1 in range(10):
                for level2 in range(10):
                    with self.limit_avail_in(strm, chunk_size):
                        err = pyzlib.deflateParams(
                            strm, level1, pyzlib.Z_DEFAULT_STRATEGY)
                        self.assertEqual(pyzlib.Z_OK, err)
                    with self.limit_avail_in(strm, chunk_size):
                        err = pyzlib.deflate(
                            strm, pyzlib.Z_NO_FLUSH)
                        self.assertEqual(pyzlib.Z_OK, err)
                    with self.limit_avail_in(strm, chunk_size):
                        err = pyzlib.deflateParams(
                            strm, level2, pyzlib.Z_DEFAULT_STRATEGY)
                        msg = 'deflateParams({} -> {})'.format(level1, level2)
                        self.assertEqual(pyzlib.Z_OK, err, msg)
                    with self.limit_avail_in(strm, chunk_size):
                        err = pyzlib.deflate(
                            strm, pyzlib.Z_NO_FLUSH)
                        self.assertEqual(pyzlib.Z_OK, err)
            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
            compressed_size = len(dest) - strm.avail_out
        self._check_inflate(dest, compressed_size, plain)

    def test_deflate_reset(self):
        strm = pyzlib.z_stream(
            zalloc=pyzlib.Z_NULL, free=pyzlib.Z_NULL,
            opaque=pyzlib.Z_NULL)
        err = pyzlib.deflateInit(strm, pyzlib.Z_BEST_SPEED)
        self.assertEqual(pyzlib.Z_OK, err)
        try:
            for _ in range(2):
                plain = bytearray(b'AAAA')
                compressed = bytearray(1024)
                strm.next_in = self._addressof_bytearray(plain)
                strm.avail_in = len(plain)
                strm.next_out = self._addressof_bytearray(compressed)
                strm.avail_out = len(compressed)
                err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
                self.assertEqual(pyzlib.Z_STREAM_END, err)
                self.assertEqual(b'\x78\x01', compressed[0:2])
                # deflateReset should preserve the compression level
                pyzlib.deflateReset(strm)
        finally:
            pyzlib.deflateEnd(strm)

    def test_small_out(self):
        plain = bytearray(b'\x05\x4e')
        dest = bytearray(16)
        sizeof_zlib_header = 2
        with self._make_deflate_stream() as strm:
            strm.next_in = self._addressof_bytearray(plain)
            strm.avail_in = len(plain)
            strm.next_out = self._addressof_bytearray(dest)
            strm.avail_out = sizeof_zlib_header
            err = pyzlib.deflate(strm, pyzlib.Z_PARTIAL_FLUSH)
            self.assertEqual(pyzlib.Z_OK, err)
            self.assertEqual(0, strm.avail_out)
            strm.avail_out = len(dest) - sizeof_zlib_header
            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
            compressed_size = len(dest) - strm.avail_out
        self._check_inflate(dest, compressed_size, plain)

    def test_small_out2(self):
        plain = bytearray(b'\xff\xff\x60\xff\x00\x7b')
        dest = bytearray(16)
        with self._make_deflate_stream(level=pyzlib.Z_BEST_SPEED) as strm:
            strm.next_in = self._addressof_bytearray(plain)
            strm.avail_in = 3
            strm.next_out = self._addressof_bytearray(dest)
            strm.avail_out = 1
            err = pyzlib.deflate(strm, pyzlib.Z_PARTIAL_FLUSH)
            self.assertEqual(pyzlib.Z_OK, err)
            consumed_in = 3 - strm.avail_in
            consumed_out = 1 - strm.avail_out

            strm.avail_in = 3
            strm.avail_out = 4
            err = pyzlib.deflateParams(
                strm,
                level=pyzlib.Z_DEFAULT_COMPRESSION,
                strategy=pyzlib.Z_DEFAULT_STRATEGY,
            )
            self.assertIn(err, (pyzlib.Z_OK, pyzlib.Z_BUF_ERROR))
            consumed_in += 3 - strm.avail_in
            consumed_out += 4 - strm.avail_out

            strm.avail_in = len(plain) - consumed_in
            strm.avail_out = len(dest) - consumed_out
            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
            consumed_out = len(dest) - strm.avail_out
        self._check_inflate(dest, consumed_out, plain)

    def test_small_out3(self):
        plain = bytearray(b'\x3f\xff\xf8\xff\xff\xff\xff\xff\xff')
        dest = bytearray(658)
        with self._make_deflate_stream(level=pyzlib.Z_BEST_SPEED) as strm:
            strm.next_in = self._addressof_bytearray(plain)
            strm.avail_in = len(plain)
            strm.next_out = self._addressof_bytearray(dest)
            strm.avail_out = len(dest)

            with self.limit_avail_in(strm, 1):
                with self.limit_avail_out(strm, 2):
                    err = pyzlib.deflate(strm, pyzlib.Z_PARTIAL_FLUSH)
                    self.assertEqual(pyzlib.Z_OK, err)
            with self.limit_avail_in(strm, 1):
                with self.limit_avail_out(strm, 2):
                    err = pyzlib.deflateParams(
                        strm,
                        level=pyzlib.Z_BEST_SPEED,
                        strategy=pyzlib.Z_HUFFMAN_ONLY,
                    )
                    self.assertIn(err, (pyzlib.Z_OK, pyzlib.Z_BUF_ERROR))
            with self.limit_avail_in(strm, 1):
                with self.limit_avail_out(strm, 2):
                    err = pyzlib.deflate(strm, pyzlib.Z_PARTIAL_FLUSH)
                    self.assertEqual(pyzlib.Z_OK, err)
            with self.limit_avail_in(strm, 1):
                with self.limit_avail_out(strm, 2):
                    err = pyzlib.deflateParams(
                        strm,
                        level=pyzlib.Z_BEST_SPEED,
                        strategy=pyzlib.Z_DEFAULT_STRATEGY,
                    )
                    self.assertIn(err, (pyzlib.Z_OK, pyzlib.Z_BUF_ERROR))
            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
        self._check_inflate(dest, len(dest) - strm.avail_out, plain)

    def test_set_dictionary2(self):
        plain = bytearray(b'\x2d')
        dest = bytearray(130)
        with self._make_deflate_stream(
                raw=True,
                level=pyzlib.Z_BEST_SPEED,
        ) as strm:
            strm.next_in = self._addressof_bytearray(plain)
            strm.avail_in = len(plain)
            strm.next_out = self._addressof_bytearray(dest)
            strm.avail_out = len(dest)

            dictionary = b'\xd7'
            err = pyzlib.deflateSetDictionary(
                strm, dictionary, len(dictionary))
            self.assertEqual(pyzlib.Z_OK, err)

            err = pyzlib.deflateParams(
                strm,
                level=pyzlib.Z_NO_COMPRESSION,
                strategy=pyzlib.Z_DEFAULT_STRATEGY,
            )
            self.assertEqual(pyzlib.Z_OK, err)

            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
        self._check_inflate(
            dest=dest,
            compressed_size=len(dest) - strm.avail_out,
            plain=plain,
            raw=True,
            dictionary=dictionary,
        )

    def test_set_dictionary3(self):
        plain = bytearray(b'\x00\x00\x00')
        dest = bytearray(134)
        with self._make_deflate_stream(
                raw=True,
                level=pyzlib.Z_BEST_SPEED,
                mem_level=1,
                strategy=pyzlib.Z_FIXED,
        ) as strm:
            strm.next_in = self._addressof_bytearray(plain)
            strm.avail_in = len(plain)
            strm.next_out = self._addressof_bytearray(dest)
            strm.avail_out = len(dest)

            dictionary = b'\x00\x09'
            err = pyzlib.deflateSetDictionary(
                strm, dictionary, len(dictionary))
            self.assertEqual(pyzlib.Z_OK, err)

            err = pyzlib.deflateParams(
                strm,
                level=pyzlib.Z_DEFAULT_COMPRESSION,
                strategy=pyzlib.Z_RLE,
            )
            self.assertEqual(pyzlib.Z_OK, err)

            err = pyzlib.deflate(strm, pyzlib.Z_FINISH)
            self.assertEqual(pyzlib.Z_STREAM_END, err)
        self._check_inflate(
            dest=dest,
            compressed_size=len(dest) - strm.avail_out,
            plain=plain,
            raw=True,
            dictionary=dictionary,
        )


if __name__ == '__main__':
    unittest.main()
