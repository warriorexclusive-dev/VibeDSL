# -*- coding: utf-8 -*-
"""sample the theme from the screenshot, via uncompressed BMP

PNG needs zlib and un-filtering; BMP is raw pixels with a 14-byte header, so it
is read with struct and nothing else. Saving uncompressed is the whole trick.

A theme written from a glance is a theme invented from a glance - that is how
minimayz happened, and it applies to hex codes exactly as it applies to names.
So every colour here is a sampled value with its share of the region, and a
region that is not flat says so instead of pretending to be one.
"""
import collections
import os
import struct

BMP = r"C:\Users\SoftIce\AppData\Local\Temp\opencode\shot2.bmp"

REGIONS = [
    ("фон редактора",           0.28, 0.60, 0.45, 0.75),
    ("фон левой панели",        0.03, 0.40, 0.16, 0.60),
    ("фон полосы меню",         0.10, 0.004, 0.30, 0.020),
    ("фон вкладки активной",    0.22, 0.034, 0.33, 0.056),
    ("фон вкладки закрытой",    0.13, 0.034, 0.21, 0.056),
    ("фон правой панели",       0.78, 0.40, 0.95, 0.60),
    ("фон полосы toolwindow",   0.004, 0.30, 0.020, 0.60),
    ("номер строки",            0.212, 0.20, 0.228, 0.32),
    ("код: текст",              0.250, 0.113, 0.330, 0.124),
    ("код: комментарий",        0.270, 0.136, 0.420, 0.145),
    ("код: ключ",               0.270, 0.328, 0.320, 0.337),
    ("код: значение",           0.320, 0.328, 0.380, 0.337),
    ("код: тип",                0.330, 0.383, 0.390, 0.392),
    ("крестик вкладки",         0.322, 0.040, 0.336, 0.052),
    ("разделитель панелей",      0.2535, 0.30, 0.2565, 0.60),
    ("разделитель полосы",      0.02, 0.0305, 0.98, 0.0325),
]

if not os.path.exists(BMP):
    raise SystemExit("  нет файла: " + BMP)

with open(BMP, "rb") as fh:
    data = fh.read()
off = struct.unpack_from("<I", data, 10)[0]      # pixel data offset
# the DIB header starts at 14, not 18: size, width, height, planes, bpp, comp
W, H = struct.unpack_from("<ii", data, 18)
planes, bpp = struct.unpack_from("<HH", data, 26)
comp = struct.unpack_from("<I", data, 30)[0]
print("  BMP %dx%d  %d бит/пиксель, сжатие %d" % (W, H, bpp, comp))
if bpp != 32:
    raise SystemExit("  ожидалось 32 бит, получено %d" % bpp)
rowbytes = W * 4
bottom_up = H > 0


def px(x, y):
    row = H - 1 - y if bottom_up else y
    p = off + row * rowbytes + x * 4
    b, g, r = data[p], data[p + 1], data[p + 2]
    return (r, g, b)


def hexs(c):
    return "#%02x%02x%02x" % c


for name, a, b, c, d in REGIONS:
    cnt = collections.Counter()
    for y in range(int(b * H), int(d * H)):
        if y >= H:
            break
        for x in range(int(a * W), int(c * W)):
            if x >= W:
                break
            cnt[px(x, y)] += 1
    tot = sum(cnt.values()) or 1
    top = cnt.most_common(2)
    dom, n = top[0]
    share = 100.0 * n / tot
    flag = "" if share > 85 else "   <- область не однотонная"
    print("  %-24s %s  %5.1f%%%s" % (name, hexs(dom), share, flag))
    if share <= 85:
        print("  %-24s %s" % ("", ", ".join("%s %.0f%%" % (hexs(x), 100.0 * k / tot)
                                           for x, k in top[1:])))
