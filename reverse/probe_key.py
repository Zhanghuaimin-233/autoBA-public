#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证提取的 RSA 私钥能否复现 oracle（PKCS#1 v1.5 + SHA-256）。"""
import base64
import hashlib
import json
import sys
from pathlib import Path


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


def parse_rsa_priv(der):
    tag, body, _ = read_tlv(der, 0)
    assert tag == 0x30
    items = []
    i = 0
    while i < len(body):
        tag, val, i = read_tlv(body, i)
        items.append((tag, val))
    ints = [int.from_bytes(v, "big") for t, v in items]
    return ints  # version,n,e,d,p,q,dp,dq,qinv


def i2osp(x, k):
    return x.to_bytes(k, "big")


def pkcs1_v15_sha256(msg, n, d, k):
    t = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(msg).digest()
    ps = b"\xff" * (k - 3 - len(t))
    em = b"\x00\x01" + ps + b"\x00" + t
    return i2osp(pow(int.from_bytes(em, "big"), d, n), k)


HERE = Path(__file__).resolve().parent

for name in ("mode0", "mode1"):
    der = open(HERE / f"key_{name}.der", "rb").read()
    v, n, e, d, p, q, dp, dq, qinv = parse_rsa_priv(der)
    print(name, "version", v, "n_bits", n.bit_length(), "e", e, "d_bits", d.bit_length(),
          "p*q==n", p * q == n)
    assert p * q == n
    assert (e * d) % ((p - 1) * (q - 1) // __import__("math").gcd(p - 1, q - 1)) == 1
    for v in json.load(open(HERE / "vectors.json", encoding="utf-8")):
        if v["mode"] != int(name[-1]):
            continue
        msg = bytes.fromhex(v["input_hex"])
        sig = pkcs1_v15_sha256(msg, n, d, 128)
        ok = sig.hex() == v["sig_hex"]
        print(f"  {v['name']:10s} mode={v['mode']} match={ok}")
        if not ok:
            print("   want", v["sig_hex"][:64])
            print("   got ", sig.hex()[:64])
