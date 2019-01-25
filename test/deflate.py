#!/usr/bin/env python3
import ctypes
import sys

import pyzlib

strm = pyzlib.z_stream()
strm.zalloc = pyzlib.Z_NULL
strm.free = pyzlib.Z_NULL
strm.opaque = pyzlib.Z_NULL
rc = pyzlib.deflateInit(strm, pyzlib.Z_DEFAULT_COMPRESSION)
if rc != pyzlib.Z_OK:
    raise Exception('deflateInit() failed with error {}'.format(rc))
stream_end = False
obuf = ctypes.create_string_buffer(8192)
while not stream_end:
    ibuf = sys.stdin.buffer.read(16384)
    strm.next_in = ibuf
    strm.avail_in = len(ibuf)
    flush = pyzlib.Z_FINISH if strm.avail_in == 0 else pyzlib.Z_NO_FLUSH
    while not stream_end:
        if flush != pyzlib.Z_FINISH and strm.avail_in == 0:
            break
        strm.next_out = ctypes.addressof(obuf)
        strm.avail_out = ctypes.sizeof(obuf)
        rc = pyzlib.deflate(strm, flush)
        stream_end = rc == pyzlib.Z_STREAM_END and flush == pyzlib.Z_FINISH
        if rc != pyzlib.Z_OK and not stream_end:
            raise Exception('deflate() failed with error {}'.format(rc))
        sys.stdout.buffer.write(obuf[:len(obuf) - strm.avail_out])
rc = pyzlib.deflateEnd(strm)
if rc != pyzlib.Z_OK:
    raise Exception('deflateEnd() failed with error {}'.format(rc))
