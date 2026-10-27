#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用公钥还原签名块（s^e mod n），对照 SHA-256/SHA-1/PSS 三种假设。"""
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sign_pure import _KEYS  # 复用已解析的两把私钥

VEC = json.loads(Path(__file__).with_name("vectors.json").read_text(encoding="utf-8"))


def em_of(sig_b64, n):
    k = (n.bit_length() + 7) // 8
    s = int.from_bytes(base64.b64decode(sig_b64), "big")
    return pow(s, 65537, n).to_bytes(k, "big")


def tlv(tag, body):
    return bytes([tag, len(body)]) + body if len(body) < 128 else bytes([tag, 0x81, len(body)]) + body


def em_sha256(msg, k):
    t = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(msg).digest()
    return b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t


def em_sha1(msg, k):
    t = bytes.fromhex("3021300906052b0e03021a05000414") + hashlib.sha1(msg).digest()
    return b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t


for v in VEC:
    if v["name"] != "test":
        continue
    n = _KEYS[v["mode"]][0]
    em = em_of(v["sig_b64"], n)
    msg = bytes.fromhex(v["input_hex"])
    print(f"mode {v['mode']} sig^e mod n (前 40B) = {em[:40].hex()}")
    print(f"mode {v['mode']} sig^e mod n (后 51B)  = {em[-51:].hex()}")
    print(f"  == PKCS#1v1.5+SHA256 ? {em == em_sha256(msg, 128)}")
    print(f"  == PKCS#1v1.5+SHA1   ? {em == em_sha1(msg, 128)}")
    print(f"  PSS 末字节 0xbc ?     {em[-1] == 0xbc}")
    print(f"  EM 头 00 01 ff ?      {em[:3].hex() == '0001ff'}")
