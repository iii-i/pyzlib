import ctypes
import ctypes.util
import os

ZLIB_VERSION = b'1.2.11'
ZLIB_VERNUM = 0x12b0
ZLIB_VER_MAJOR = 1
ZLIB_VER_MINOR = 2
ZLIB_VER_REVISION = 11
ZLIB_VER_SUBREVISION = 0


class z_stream(ctypes.Structure):
    _fields_ = [
        ('next_in', ctypes.c_char_p),
        ('avail_in', ctypes.c_uint),
        ('total_in', ctypes.c_ulong),
        ('next_out', ctypes.c_char_p),
        ('avail_out', ctypes.c_uint),
        ('total_out', ctypes.c_ulong),
        ('msg', ctypes.c_char_p),
        ('state', ctypes.c_void_p),
        ('zalloc', ctypes.c_void_p),
        ('zfree', ctypes.c_void_p),
        ('opaque', ctypes.c_void_p),
        ('data_type', ctypes.c_int),
        ('adler', ctypes.c_ulong),
        ('reserved', ctypes.c_ulong),
    ]


Z_NO_FLUSH = 0
Z_PARTIAL_FLUSH = 1
Z_SYNC_FLUSH = 2
Z_FULL_FLUSH = 3
Z_FINISH = 4
Z_BLOCK = 5
Z_TREES = 6

Z_OK = 0
Z_STREAM_END = 1
Z_NEED_DICT = 2
Z_ERRNO = -1
Z_STREAM_ERROR = -2
Z_DATA_ERROR = -3
Z_MEM_ERROR = -4
Z_BUF_ERROR = -5
Z_VERSION_ERROR = -6

Z_NO_COMPRESSION = 0
Z_BEST_SPEED = 1
Z_BEST_COMPRESSION = 9
Z_DEFAULT_COMPRESSION = -1

Z_FILTERED = 1
Z_HUFFMAN_ONLY = 2
Z_RLE = 3
Z_FIXED = 4
Z_DEFAULT_STRATEGY = 0

Z_BINARY = 0
Z_TEXT = 1
Z_ASCII = Z_TEXT
Z_UNKNOWN = 2

Z_DEFLATED = 8

Z_NULL = None

_zlib_name = ctypes.util.find_library('z')
if _zlib_name is None:
    raise Exception('Could not find zlib')
if os.name == 'posix':
    # Allow LD_PRELOAD interposition
    ctypes.CDLL(_zlib_name, mode=ctypes.RTLD_GLOBAL)
    _zlib = ctypes.CDLL(None)
else:
    _zlib = ctypes.CDLL(_zlib_name)

_zlib.zlibVersion.restype = ctypes.c_char_p
_zlib.zlibVersion.argtypes = []


def zlibVersion():
    return _zlib.zlibVersion()


_zlib.deflateInit_.restype = ctypes.c_int
_zlib.deflateInit_.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # level
    ctypes.c_char_p,  # version
    ctypes.c_int,  # stream_size
]


def deflateInit(strm, level):
    return _zlib.deflateInit_(
        ctypes.addressof(strm), level,
        ctypes.c_char_p(ZLIB_VERSION), ctypes.sizeof(z_stream))


_zlib.deflate.restype = ctypes.c_int
_zlib.deflate.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # flush
]


def deflate(strm, flush):
    return _zlib.deflate(ctypes.addressof(strm), flush)


_zlib.deflateEnd.restype = ctypes.c_int
_zlib.deflateEnd.argtypes = [
    ctypes.c_void_p,  # strm
]


def deflateEnd(strm):
    return _zlib.deflateEnd(ctypes.addressof(strm))


_zlib.inflateInit_.restype = ctypes.c_int
_zlib.inflateInit_.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_char_p,  # version
    ctypes.c_int,  # stream_size
]


def inflateInit(strm):
    return _zlib.inflateInit_(
        ctypes.addressof(strm),
        ctypes.c_char_p(ZLIB_VERSION), ctypes.sizeof(z_stream))


_zlib.inflate.restype = ctypes.c_int
_zlib.inflate.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # flush
]


def inflate(strm, flush):
    return _zlib.inflate(ctypes.addressof(strm), flush)


_zlib.inflateEnd.restype = ctypes.c_int
_zlib.inflateEnd.argtypes = [
    ctypes.c_void_p,  # strm
]


def inflateEnd(strm):
    return _zlib.inflateEnd(ctypes.addressof(strm))


_zlib.deflateInit2_.restype = ctypes.c_int
_zlib.deflateInit2_.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # level
    ctypes.c_int,  # method
    ctypes.c_int,  # windowBits
    ctypes.c_int,  # memLevel
    ctypes.c_int,  # strategy
    ctypes.c_char_p,  # version
    ctypes.c_int,  # stream_size
]


def deflateInit2(strm, level, method, windowBits, memLevel, strategy):
    return _zlib.deflateInit2_(
        ctypes.addressof(strm), level, method, windowBits, memLevel, strategy,
        ctypes.c_char_p(ZLIB_VERSION), ctypes.sizeof(z_stream))


_zlib.deflateSetDictionary.restype = ctypes.c_int
_zlib.deflateSetDictionary.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_void_p,  # dictionary
    ctypes.c_uint,  # dictLength
]


def deflateSetDictionary(strm, dictionary, dictLength):
    return _zlib.deflateSetDictionary(
        ctypes.addressof(strm), dictionary, dictLength)


_zlib.deflateGetDictionary.restype = ctypes.c_int
_zlib.deflateGetDictionary.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_void_p,  # dictionary
    ctypes.c_uint,  # dictLength
]


def deflateGetDictionary(strm, dictionary, dictLength):
    return _zlib.deflateGetDictionary(
        ctypes.addressof(strm), dictionary, dictLength)


_zlib.deflateCopy.restype = ctypes.c_int
_zlib.deflateCopy.argtypes = [
    ctypes.c_void_p,  # dest
    ctypes.c_void_p,  # source
]


def deflateCopy(dest, source):
    return _zlib.deflateCopy(ctypes.addressof(dest), ctypes.addressof(source))


_zlib.deflateReset.restype = ctypes.c_int
_zlib.deflateReset.argtypes = [
    ctypes.c_void_p,  # strm
]


def deflateReset(strm):
    return _zlib.deflateReset(ctypes.addressof(strm))


_zlib.deflateParams.restype = ctypes.c_int
_zlib.deflateParams.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # level
    ctypes.c_int,  # strategy
]


def deflateParams(strm, level, strategy):
    return _zlib.deflateParams(ctypes.addressof(strm), level, strategy)


_zlib.deflateTune.restype = ctypes.c_int
_zlib.deflateTune.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # good_length
    ctypes.c_int,  # max_lazy
    ctypes.c_int,  # nice_length
    ctypes.c_int,  # max_chain
]


def deflateTune(strm, good_length, max_lazy, nice_length, max_chain):
    return _zlib.deflateTune(
        ctypes.addressof(strm), good_length, max_lazy, nice_length, max_chain)


_zlib.deflateBound.restype = ctypes.c_ulong
_zlib.deflateBound.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_ulong,  # sourceLen
]


def deflateBound(strm, sourceLen):
    return _zlib.deflateBound(ctypes.addressof(strm), sourceLen)


_zlib.deflatePending.restype = ctypes.c_int
_zlib.deflatePending.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_void_p,  # pending
    ctypes.c_void_p,  # bits
]


class _c_uint_wrapper(ctypes.Structure):
    _fields_ = [
        ('v', ctypes.c_uint),
    ]


class _c_int_wrapper(ctypes.Structure):
    _fields_ = [
        ('v', ctypes.c_int),
    ]


class _c_ulong_wrapper(ctypes.Structure):
    _fields_ = [
        ('v', ctypes.c_ulong),
    ]


def deflatePending(strm):
    pending = _c_uint_wrapper()
    bits = _c_int_wrapper()
    ret = _zlib.deflatePending(
        ctypes.addressof(strm),
        ctypes.addressof(pending),
        ctypes.addressof(bits))
    return ret, pending.v, bits.v


_zlib.deflatePrime.restype = ctypes.c_int
_zlib.deflatePrime.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # bits
    ctypes.c_int,  # value
]


def deflatePrime(strm, bits, value):
    return _zlib.deflatePrime(ctypes.addressof(strm), bits, value)


_zlib.inflateInit2_.restype = ctypes.c_int
_zlib.inflateInit2_.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # windowBits
    ctypes.c_char_p,  # version
    ctypes.c_int,  # stream_size
]


def inflateInit2(strm, windowBits):
    return _zlib.inflateInit2_(
        ctypes.addressof(strm), windowBits,
        ctypes.c_char_p(ZLIB_VERSION), ctypes.sizeof(z_stream))


_zlib.inflateSetDictionary.restype = ctypes.c_int
_zlib.inflateSetDictionary.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_void_p,  # dictionary
    ctypes.c_uint,  # dictLength
]


def inflateSetDictionary(strm, dictionary, dictLength):
    return _zlib.inflateSetDictionary(
        ctypes.addressof(strm), dictionary, dictLength)


_zlib.inflateSync.restype = ctypes.c_int
_zlib.inflateSync.argtypes = [
    ctypes.c_void_p,
]


def inflateSync(strm):
    return _zlib.inflateSync(ctypes.addressof(strm))


_zlib.inflateCopy.restype = ctypes.c_int
_zlib.inflateCopy.argtypes = [
    ctypes.c_void_p,  # dest
    ctypes.c_void_p,  # source
]


def inflateCopy(dest, source):
    return _zlib.inflateCopy(ctypes.addressof(dest), ctypes.addressof(source))


_zlib.inflateReset.restype = ctypes.c_int
_zlib.inflateReset.argtypes = [
    ctypes.c_void_p,  # strm
]


def inflateReset(strm):
    return _zlib.inflateReset(ctypes.addressof(strm))


_zlib.inflateReset2.restype = ctypes.c_int
_zlib.inflateReset2.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # windowBits
]


def inflateReset2(strm, windowBits):
    return _zlib.inflateReset2(ctypes.addressof(strm), windowBits)


_zlib.inflatePrime.restype = ctypes.c_int
_zlib.inflatePrime.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_int,  # bits
    ctypes.c_int,  # value
]


def inflatePrime(strm, bits, value):
    return _zlib.inflatePrime(ctypes.addressof(strm), bits, value)


_zlib.inflateMark.restype = ctypes.c_long
_zlib.inflateMark.argtypes = [
    ctypes.c_void_p,  # strm
]


def inflateMark(strm):
    return _zlib.inflateMark(ctypes.addressof(strm))


_zlib.zlibCompileFlags.restype = ctypes.c_ulong
_zlib.zlibCompileFlags.argtypes = []


def zlibCompileFlags():
    return _zlib.zlibCompileFlags()


_zlib.compress.restype = ctypes.c_int
_zlib.compress.argtypes = [
    ctypes.c_void_p,  # dest
    ctypes.c_void_p,  # destLen
    ctypes.c_void_p,  # source
    ctypes.c_ulong,  # sourceLen
]


def compress(dest, destLen, source, sourceLen):
    dest_len_buf = _c_ulong_wrapper()
    dest_len_buf.v = destLen
    ret = _zlib.compress(
        dest,
        ctypes.addressof(dest_len_buf),
        source,
        sourceLen)
    return ret, dest_len_buf.v


_zlib.compress2.restype = ctypes.c_int
_zlib.compress2.argtypes = [
    ctypes.c_void_p,  # dest
    ctypes.c_void_p,  # destLen
    ctypes.c_void_p,  # source
    ctypes.c_ulong,  # sourceLen
    ctypes.c_int,  # level
]


def compress2(dest, destLen, source, sourceLen, level):
    dest_len_buf = _c_ulong_wrapper()
    dest_len_buf.v = destLen
    ret = _zlib.compress2(
        dest,
        ctypes.addressof(dest_len_buf),
        source,
        sourceLen,
        level)
    return ret, dest_len_buf.v


_zlib.compressBound.restype = ctypes.c_ulong
_zlib.compressBound.argtypes = [
    ctypes.c_ulong,  # sourceLen
]


def compressBound(sourceLen):
    return _zlib.compressBound(sourceLen)


_zlib.uncompress.restype = ctypes.c_int
_zlib.uncompress.argtypes = [
    ctypes.c_void_p,  # dest
    ctypes.c_void_p,  # destLen
    ctypes.c_void_p,  # source
    ctypes.c_ulong,  # sourceLen
]


def uncompress(dest, destLen, source, sourceLen):
    dest_len_buf = _c_ulong_wrapper()
    dest_len_buf.v = destLen
    ret = _zlib.uncompress(
        dest,
        ctypes.addressof(dest_len_buf),
        source,
        sourceLen)
    return ret, dest_len_buf.v


_zlib.uncompress2.restype = ctypes.c_int
_zlib.uncompress2.argtypes = [
    ctypes.c_void_p,  # dest
    ctypes.c_void_p,  # destLen
    ctypes.c_void_p,  # source
    ctypes.c_void_p,  # sourceLen
]


def uncompress2(dest, destLen, source, sourceLen):
    dest_len_buf = _c_ulong_wrapper()
    dest_len_buf.v = destLen
    source_len_buf = _c_ulong_wrapper()
    source_len_buf.v = sourceLen
    ret = _zlib.uncompress2(
        dest,
        ctypes.addressof(dest_len_buf),
        source,
        ctypes.addressof(source_len_buf))
    return ret, dest_len_buf.v, source_len_buf.v


_zlib.inflateSyncPoint.restype = ctypes.c_int
_zlib.inflateSyncPoint.argtypes = [
    ctypes.c_void_p,  # strm
]


def inflateSyncPoint(strm):
    return _zlib.inflateSyncPoint(ctypes.addressof(strm))
