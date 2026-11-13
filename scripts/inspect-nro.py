#!/usr/bin/env python3
"""Check a packaged NRO's sections and application metadata without running it."""
import argparse
from pathlib import Path
import struct

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('path', type=Path)
args = ap.parse_args()
data = args.path.read_bytes()
assert len(data) >= 0x80 and data[0x10:0x14] == b'NRO0', 'Missing NRO header'
size = struct.unpack_from('<I', data, 0x18)[0]
assert 0x80 <= size <= len(data), 'Invalid NRO image size'
for offset in (0x20, 0x28, 0x30):
    start, length = struct.unpack_from('<II', data, offset)
    assert start + length <= size, 'Section outside the NRO image'
assert data[size:size + 4] == b'ASET', 'Missing asset section'
offset, length = struct.unpack_from('<QQ', data, size + 0x18)
assert length == 0x4000 and size + offset + length <= len(data), 'Invalid NACP'
nacp = data[size + offset:size + offset + length]
title = nacp[:0x200].split(b'\0')[0].decode('utf-8')
assert title, 'Empty application title'
print(f'{args.path}: {len(data)} bytes; NRO sections and NACP verified; title={title!r}')
