"""Generate AES T-tables (Te0-3) + verify a JS-compatible AES-256 encrypt
implementation against pycryptodome. Output tables.json for the node scanner.
"""
import json

from Crypto.Cipher import AES


def mul(a, b):
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p


def gen_sbox():
    sbox = [0] * 256
    for x in range(256):
        inv = 0 if x == 0 else next(y for y in range(256) if mul(x, y) == 1)
        res = inv
        for sh in (1, 2, 3, 4):
            res ^= ((inv << sh) | (inv >> (8 - sh))) & 0xFF
        sbox[x] = res ^ 0x63
    return sbox


SBOX = gen_sbox()
assert SBOX[0] == 0x63 and SBOX[1] == 0x7c and SBOX[0x53] == 0xED, "sbox selftest failed"


def gen_te():
    te = [[0] * 256 for _ in range(4)]
    for x in range(256):
        s = SBOX[x]
        m2, m3 = mul(s, 2), mul(s, 3)
        te[0][x] = (m2 << 24) | (s << 16) | (s << 8) | m3
        te[1][x] = (m3 << 24) | (m2 << 16) | (s << 8) | s
        te[2][x] = (s << 24) | (m3 << 16) | (m2 << 8) | s
        te[3][x] = (s << 24) | (s << 16) | (m3 << 8) | m2
    return te


TE = gen_te()
RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D]


def expand256(key):
    rk = [[key[i * 4 + j] for j in range(4)] for i in range(8)]  # 8 words of 4 bytes
    words = [list(w) for w in rk]
    for i in range(8, 60):
        t = list(words[i - 1])
        if i % 8 == 0:
            t = t[1:] + t[:1]
            t = [SBOX[b] for b in t]
            t[0] ^= RCON[i // 8 - 1]
        elif i % 8 == 4:
            t = [SBOX[b] for b in t]
        words.append([words[i - 8][j] ^ t[j] for j in range(4)])
    # pack into 15 round keys of 4 words
    return [words[i * 4:i * 4 + 4] for i in range(15)]


def xtime(a):
    return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else (a << 1)


def enc_block(pt, rk):
    """T-table AES-256 encrypt, word-based (state as 4 words, big-endian bytes)."""
    s = [int.from_bytes(bytes(pt[i * 4:i * 4 + 4]), "big") for i in range(4)]
    # initial AddRoundKey
    for j in range(4):
        s[j] ^= int.from_bytes(bytes(rk[0][j]), "big")
    for rnd in range(1, 14):
        t = [0] * 4
        for j in range(4):
            b0 = (s[j] >> 24) & 0xFF
            b1 = (s[(j + 1) % 4] >> 16) & 0xFF
            b2 = (s[(j + 2) % 4] >> 8) & 0xFF
            b3 = s[(j + 3) % 4] & 0xFF
            t[j] = TE[0][b0] ^ TE[1][b1] ^ TE[2][b2] ^ TE[3][b3] ^ int.from_bytes(bytes(rk[rnd][j]), "big")
        s = t
    # final round (no MixColumns): SubBytes+ShiftRows+AddRoundKey
    out = bytearray(16)
    rk14 = rk[14]
    for j in range(4):
        b0 = (s[j] >> 24) & 0xFF
        b1 = (s[(j + 1) % 4] >> 16) & 0xFF
        b2 = (s[(j + 2) % 4] >> 8) & 0xFF
        b3 = s[(j + 3) % 4] & 0xFF
        v = (SBOX[b0] << 24) | (SBOX[b1] << 16) | (SBOX[b2] << 8) | SBOX[b3]
        v ^= int.from_bytes(bytes(rk14[j]), "big")
        out[j * 4:j * 4 + 4] = v.to_bytes(4, "big")
    return bytes(out)


def main():
    # FIPS-197 C.3 AES-256 vector
    key = bytes.fromhex("603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4")
    pt = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
    want = bytes.fromhex("f3eed1bdb5d2a03c064b5a7e3db181f8")
    rk = expand256(key)
    got = enc_block(pt, rk)
    print("selftest:", "OK" if got == want else f"FAIL got={got.hex()} want={want.hex()}")

    # also cross-check with pycryptodome on random-ish input
    pt2 = bytes(range(16))
    ref = AES.new(key, AES.MODE_ECB).encrypt(pt2)
    got2 = enc_block(pt2, rk)
    print("refcheck:", "OK" if got2 == ref else f"FAIL got={got2.hex()} ref={ref.hex()}")

    if got == want and got2 == ref:
        json.dump({"te": TE}, open("te_tables.json", "w"))
        print("[+] te_tables.json written")


if __name__ == "__main__":
    main()
