import ctypes
import ctypes.util

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

Z_NULL = 0

_zlib_name = ctypes.util.find_library('z')
if _zlib_name is None:
    raise Exception('Could not find zlib')
_zlib = ctypes.CDLL(_zlib_name)

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


_zlib.deflateBound.restype = ctypes.c_ulong
_zlib.deflateBound.argtypes = [
    ctypes.c_void_p,  # strm
    ctypes.c_ulong,  # sourceLen
]


def deflateBound(strm, sourceLen):
    return _zlib.deflateBound(ctypes.addressof(strm), sourceLen)
