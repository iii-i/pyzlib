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
        next_in=pyzlib.Z_NULL,
        avail_in=0,
        zalloc=pyzlib.Z_NULL,
        free=pyzlib.Z_NULL,
        opaque=pyzlib.Z_NULL,
    )
    if args.window_bits == 15:
        init_func_name = "inflateInit"
        rc = pyzlib.inflateInit(strm)
    else:
        init_func_name = "inflateInit2"
        rc = pyzlib.inflateInit2(strm, args.window_bits)
    if rc != pyzlib.Z_OK:
        raise Exception("{}() failed with error {}".format(init_func_name, rc))
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
                raise Exception("inflate() failed with error {}".format(rc))
            sys.stdout.buffer.write(obuf[: len(obuf) - strm.avail_out])
    rc = pyzlib.inflateEnd(strm)
    if rc != pyzlib.Z_OK:
        raise Exception("inflateEnd() failed with error {}".format(rc))


if __name__ == "__main__":
    main()
