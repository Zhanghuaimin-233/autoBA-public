#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 libairisgcore.so 提取两把 RSA-1024 私钥（.rodata XOR 0xA5 + base64 + PKCS#1 DER）。

复跑：
  uv run --with pyelftools python reverse/extract_keys.py <libairisgcore.so>
输出：key_mode0.der / key_mode1.der 与参数摘要。
"""
import base64
import hashlib
import os
import sys
from pathlib import Path

from elftools.elf.elffile import ELFFile

SO = (sys.argv[1] if len(sys.argv) > 1
      else os.environ.get('AUTOBA_AIRI_SO') or os.path.join('capture', 'libairisgcore.so'))
OUT = Path(__file__).resolve().parent

# 0xf066c: mode==0 -> adr 0xB8FE0；mode!=0 -> adr 0xB930C；长度 0x32C；逐字节 XOR 0xA5。
TABLES = {0: 0xB8FE0, 1: 0xB930C}
LEN = 0x32C
XOR = 0xA5


def read_va(raw, elf, va, n):
    for s in elf.iter_sections():
        if s['sh_type'] != 'SHT_NOBITS' and s['sh_addr'] <= va < s['sh_addr'] + s['sh_size']:
            off = s['sh_offset'] + (va - s['sh_addr'])
            return raw[off:off + n]
    raise ValueError(f"vaddr 0x{va:x} 不在任何可读节内")


def read_tlv(buf, i):
    tag = buf[i]
    i += 1
    ln = buf[i]
    i += 1
    if ln & 0x80:
        n = ln & 0x7F
        ln = int.from_bytes(buf[i:i + n], "big")
        i += n
    return tag, buf[i:i + ln], i + ln


def parse_pkcs1(der):
    tag, body, end = read_tlv(der, 0)
    assert tag == 0x30 and end == len(der), (tag, end, len(der))
    vals, i = [], 0
    while i < len(body):
        t, v, i = read_tlv(body, i)
        assert t == 0x02
        vals.append(int.from_bytes(v, "big"))
    assert len(vals) == 9, len(vals)
    return vals  # version,n,e,d,p,q,dp,dq,qinv


def main():
    raw = open(SO, "rb").read()
    elf = ELFFile(open(SO, "rb"))
    for mode, va in TABLES.items():
        blob = read_va(raw, elf, va, LEN)
        b64 = bytes(b ^ XOR for b in blob)
        assert all(32 <= b < 127 for b in b64), "XOR 后应为纯 ASCII base64"
        der = base64.b64decode(b64, validate=True)
        (OUT / f"key_mode{mode}.der").write_bytes(der)
        version, n, e, d, p, q, dp, dq, qinv = parse_pkcs1(der)
        assert p * q == n
        assert (e * dp) % (p - 1) == 1 and (e * dq) % (q - 1) == 1
        assert (qinv * q) % p == 1
        print(f"mode {mode}: table=0x{va:x} b64_len={len(b64)} der_len={len(der)} "
              f"version={version} bits={n.bit_length()} e={e}")
        print(f"  n   = {n:0{256}x}")
        print(f"  d   = {d:0{256}x}")
        print(f"  p   = {p:0{128}x}")
        print(f"  q   = {q:0{128}x}")
        print(f"  dp  = {dp:0{128}x}")
        print(f"  dq  = {dq:0{128}x}")
        print(f"  qinv= {qinv:0{128}x}")
        print(f"  sha256(n) = {hashlib.sha256(n.to_bytes(128, 'big')).hexdigest()}")
        print(f"  sha256(der) = {hashlib.sha256(der).hexdigest()}")


if __name__ == "__main__":
    main()
