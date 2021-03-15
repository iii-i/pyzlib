#!/usr/bin/env python3
import argparse
import ctypes
import sys

import pyzlib


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-bits", type=int, default=15)
    args = parser.parse_args()
    strm = pyzlib.z_stream(
        zalloc=pyzlib.Z_NULL, free=pyzlib.Z_NULL, opaque=pyzlib.Z_NULL
    )
    if args.window_bits == 15:
        init_func_name = "deflateInit"
        rc = pyzlib.deflateInit(strm, pyzlib.Z_DEFAULT_COMPRESSION)
    else:
        init_func_name = "deflateInit2"
        rc = pyzlib.deflateInit2(
            strm=strm,
            level=pyzlib.Z_DEFAULT_COMPRESSION,
            method=pyzlib.Z_DEFLATED,
            windowBits=args.window_bits,
            memLevel=8,
            strategy=pyzlib.Z_DEFAULT_STRATEGY,
        )
    if rc != pyzlib.Z_OK:
        raise Exception("{}() failed with error {}".format(init_func_name, rc))
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
                raise Exception("deflate() failed with error {}".format(rc))
            sys.stdout.buffer.write(obuf[: len(obuf) - strm.avail_out])
    rc = pyzlib.deflateEnd(strm)
    if rc != pyzlib.Z_OK:
        raise Exception("deflateEnd() failed with error {}".format(rc))


if __name__ == "__main__":
    main()
