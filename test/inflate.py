#!/usr/bin/env python3
import ctypes
import sys

import pyzlib

strm = pyzlib.z_stream(
    next_in=pyzlib.Z_NULL, avail_in=0,
    zalloc=pyzlib.Z_NULL, free=pyzlib.Z_NULL, opaque=pyzlib.Z_NULL)
rc = pyzlib.inflateInit(strm)
if rc != pyzlib.Z_OK:
    raise Exception('inflateInit() failed with error {}'.format(rc))
stream_end = False
obuf = ctypes.create_string_buffer(16384)
while not stream_end:
    ibuf = sys.stdin.buffer.read(8192)
    strm.next_in = ibuf
    strm.avail_in = len(ibuf)
    while not stream_end:
        strm.next_out = ctypes.addressof(obuf)
        strm.avail_out = ctypes.sizeof(obuf)
        rc = pyzlib.inflate(strm, pyzlib.Z_NO_FLUSH)
        if rc == pyzlib.Z_STREAM_END:
            stream_end = True
        elif rc == pyzlib.Z_BUF_ERROR:
            break
        elif rc != pyzlib.Z_OK:
            raise Exception('inflate() failed with error {}'.format(rc))
        sys.stdout.buffer.write(obuf[:len(obuf) - strm.avail_out])
rc = pyzlib.inflateEnd(strm)
if rc != pyzlib.Z_OK:
    raise Exception('inflateEnd() failed with error {}'.format(rc))
