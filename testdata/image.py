# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import zlib
import struct

from .compat import *
from .utils import ByteString


def make_png(width, height, color=None):
    """Make a png image of arbitrary width, height, and color

    The mojority of this function comes from this great SO answer with public domain
    code:

        https://stackoverflow.com/a/25835368/5006

    it's been modified with help from:
        http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html
        https://en.wikipedia.org/wiki/Portable_Network_Graphics
        https://www.w3.org/TR/PNG/

    to support arbitrary dimensions and 0-255 rgb colors

    :param width: int, the width of the image you want to generate
    :param height: int, the height of the image you want to generate
    :param color: list|tuple, a list/tuple of an (r, g, b) value where r, g, and
        b are integers between 0 and 255
    :returns: bytes, the raw png that can be written to a file
    """
    def I1(value):
        return struct.pack("!B", value & (2**8-1))

    def I4(value):
        return struct.pack("!I", value & (2**32-1))

    def B1(value):
        return chr(value) if is_py2 else value

    # PNG file header
    png = b"\x89" + "PNG\r\n\x1A\n".encode('ascii')

    # IHDR block
    # colortype values:
    #   6 for color: Each pixel is an R,G,B triple, followed by an alpha sample
    #   0 for b&w: Each pixel is a grayscale sample
    colortype = 6 if color else 0
    bitdepth = 8 # with one byte per pixel (0..255)
    compression = 0 # zlib (no choice here)
    filtertype = 0 # adaptive (each scanline seperately)
    interlaced = 0 # no
    IHDR = I4(width) + I4(height) + I1(bitdepth)
    IHDR += I1(colortype) + I1(compression)
    IHDR += I1(filtertype) + I1(interlaced)
    block = "IHDR".encode('ascii') + IHDR
    png += I4(len(IHDR)) + block + I4(zlib.crc32(block))

    # IDAT block (the actual image)
    # if we don't have a color then we just use a black pixel bit, but if we do have
    # a color we use 4 bits (r, g, b, a) for each pixel
    raw = bytearray()

    if color:
        # NOTE -- you could make the images smaller by creating a
        # palette (colortype 2) with one color and then just using the
        # index like the b&w image does, but that's way more work because we
        # would need to add a PLTE block with the palette information
        c = []
        for co in color:
            c.append(B1(co))
        c.append(B1(255)) # alpha
    else:
        c = [B1(0)] # default black pixel

    # populate the actual image data
    for y in range(height):
        raw.append(B1(0)) # no filter for this scanline
        for x in range(width):
            raw.extend(c)

    compressor = zlib.compressobj()
    compressed = compressor.compress(bytes(raw) if is_py2 else raw)
    compressed += compressor.flush()
    block = "IDAT".encode('ascii') + compressed
    png += I4(len(compressed)) + block + I4(zlib.crc32(block))

    # IEND block
    block = "IEND".encode('ascii')
    png += I4(0) + block + I4(zlib.crc32(block))

    return png


def make_jpg(width, height, color=None):
    """Looks like this would be possible but I don't really need it right now so 
    I'm not bothering right now

    https://en.wikipedia.org/wiki/JPEG#The_JPEG_standard
    https://stackoverflow.com/a/16755049/5006

    you can probably pick apart how PIL does it:
        https://github.com/whatupdave/pil/blob/master/PIL/JpegImagePlugin.py

    search:
        create a jpeg of one color in pure python
    """
    pass

