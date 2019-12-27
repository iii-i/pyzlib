#!/usr/bin/env python3
import ctypes
import lzma
import os
import time

import pyzlib
import termplotlib as tpl

CANTERBURY = [
    'alice29.txt',
    'asyoulik.txt',
    'cp.html',
    'fields.c',
    'grammar.lsp',
    'kennedy.xls',
    'lcet10.txt',
    'plrabn12.txt',
    'ptt5',
    'sum',
    'xargs.1',
]

SILESA = [
    'dickens',
    'mozilla',
    'mr',
    'nci',
    'ooffice',
    'osdb',
    'reymont',
    'samba',
    'sao',
    'webster',
    'xml',
    'x-ray',
]

LTCB = [
    'enwik8',
]

SNAPPY = [
    'fireworks.jpeg',
    'geo.protodata',
    'paper-100k.pdf',
    'urls.10K',
]

DATA = CANTERBURY + SILESA + LTCB + SNAPPY


def addressof_bytearray(buf):
    return ctypes.cast(ctypes.addressof(
        (ctypes.c_char * len(buf)).from_buffer(buf)),
        ctypes.c_char_p)


def timeit_once(content, bufsize, dest):
    tc = 0.
    tu = 0.
    compress_dest = addressof_bytearray(dest)
    compress_dest_len = len(dest)
    uncompress_buf = bytearray(bufsize)
    uncompress_dest = addressof_bytearray(uncompress_buf)
    for off in range(0, len(content), bufsize):
        compress_source = content[off:off + bufsize]
        compress_source_len = min(len(content) - off, bufsize)
        t0 = time.time()
        ret, compressed_len = pyzlib.compress(
            compress_dest,
            compress_dest_len,
            compress_source,
            compress_source_len)
        tc += time.time() - t0
        if ret != pyzlib.Z_OK:
            raise Exception('compress() failed')
        t0 = time.time()
        ret, uncompressed_len = pyzlib.uncompress(
            uncompress_dest,
            bufsize,
            compress_dest,
            compressed_len)
        tu += time.time() - t0
        if ret != pyzlib.Z_OK:
            raise Exception('uncompress() failed')
    return tc, tu


def timeit_bo3(content, bufsize, dest):
    times = [timeit_once(content, bufsize, dest) for _ in range(3)]
    return min(tc for tc, _ in times), min(tu for _, tu in times)


def main():
    dest = bytearray(1 << 21)
    for data in DATA:
        xz_path = os.path.join(
            os.path.dirname(__file__),
            'squash-benchmark',
            f'{data}.xz')
        with lzma.LZMAFile(xz_path) as fp:
            content = fp.read()
        log_bufsizes = range(20)
        bufsizes = [1 << log_bufsize for log_bufsize in log_bufsizes]
        tcs = []
        tus = []
        for bufsize in bufsizes:
            tc, tu = timeit_bo3(content, bufsize, dest)
            tcs.append(len(content) / tc)
            tus.append(len(content) / tu)
        fig = tpl.figure()
        fig.plot(log_bufsizes, tcs, label=f'compress {data}')
        fig.show()
        fig = tpl.figure()
        fig.plot(log_bufsizes, tus, label=f'uncompress {data}')
        fig.show()


if __name__ == '__main__':
    main()
