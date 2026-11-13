#!/usr/bin/env python3
"""Verify a module's original cartridge revision without modifying it."""
import argparse
from pathlib import Path
import zlib

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--rom', required=True, type=Path)
ap.add_argument('--crc', required=True)
ap.add_argument('--mapper', required=True, type=int)
ap.add_argument('--title', required=True)
args = ap.parse_args()
data = args.rom.read_bytes()
if len(data) < 16 or data[:4] != b'NES\x1a':
    ap.error('Expected an original iNES/NES 2.0 cartridge image')
nes2 = data[7] & 12 == 8
mapper = (data[6] >> 4) | (data[7] & 240) | (((data[8] & 15) << 8) if nes2 else 0)
def size(low, high, unit):
    return ((1 << (low >> 2)) * (2 * (low & 3) + 1)) if high == 15 else (low | high << 8) * unit
expected = size(data[4], data[9] & 15 if nes2 else 0, 16384)
expected += size(data[5], data[9] >> 4 if nes2 else 0, 8192)
payload = data[16 + (512 if data[6] & 4 else 0):]
crc = zlib.crc32(payload)
if len(payload) != expected or mapper != args.mapper or crc != int(args.crc, 16):
    ap.error(f'{args.title}: requires payload CRC {args.crc}, mapper {args.mapper}; '
             f'received CRC {crc:08X}, mapper {mapper}. Use the matching original ROM.')
print(f'{args.title}: cartridge revision verified ({crc:08X}, mapper {mapper})')
