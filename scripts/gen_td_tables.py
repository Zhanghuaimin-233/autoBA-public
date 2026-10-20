"""Generate decryption T-tables (Td0-3) + mul tables, verify JS-compatible
AES-256 equivalent-inverse decrypt against pycryptodome. Output td_tables.json.
"""
import json

from Crypto.Cipher import AES
from gen_te_tables import mul, SBOX


def gen_td():
    ISBOX = [0] * 256
    for i, s in enumerate(SBOX):
        ISBOX[s] = i
    td = [[0] * 256 for _ in range(4)]
    for x in range(256):
        s = ISBOX[x]
        m9, mb, md, me = mul(s, 9), mul(s, 0x0B), mul(s, 0x0D), mul(s, 0x0E)
        # Td0[x] bytes (b3,b2,b1,b0) = me,9,md,b  (rijndael-alg-fst convention)
        td[0][x] = (me << 24) | (m9 << 16) | (md << 8) | mb
        td[1][x] = (mb << 24) | (me << 16) | (m9 << 8) | md
        td[2][x] = (md << 24) | (mb << 16) | (me << 8) | m9
        td[3][x] = (m9 << 24) | (md << 16) | (mb << 8) | me
    return td, ISBOX


TD, ISBOX = gen_td()
MUL9 = [mul(x, 9) for x in range(256)]
MULB = [mul(x, 0x0B) for x in range(256)]
MULD = [mul(x, 0x0D) for x in range(256)]
MULE = [mul(x, 0x0E) for x in range(256)]


def inv_mix_col(word_bytes):
    """word_bytes: 4 bytes [b0..b3] (big-endian word). Returns transformed 4-int list."""
    b = list(word_bytes)
    return [
        (MULE[b[0]] ^ MULB[b[1]] ^ MULD[b[2]] ^ MUL9[b[3]]),
        (MUL9[b[0]] ^ MULE[b[1]] ^ MULB[b[2]] ^ MULD[b[3]]),
        (MULD[b[0]] ^ MUL9[b[1]] ^ MULE[b[2]] ^ MULB[b[3]]),
        (MULB[b[0]] ^ MULD[b[1]] ^ MUL9[b[2]] ^ MULE[b[3]]),
    ]


def expand256_words(key):
    RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D]
    words = []
    for i in range(8):
        words.append(list(key[i * 4:i * 4 + 4]))
    for i in range(8, 60):
        t = list(words[i - 1])
        if i % 8 == 0:
            t = t[1:] + t[:1]
            t = [SBOX[b] for b in t]
            t[0] ^= RCON[i // 8 - 1]
        elif i % 8 == 4:
            t = [SBOX[b] for b in t]
        words.append([words[i - 8][j] ^ t[j] for j in range(4)])
    return words


def dec_block(ct16, key):
    """Equivalent-inverse-cipher AES-256 decrypt, byte-level reference impl."""
    words = expand256_words(key)
    # dk words: dk[i] for i=1..13 get InvMixColumns applied per word
    dk = []
    for i in range(15):
        w4 = words[i * 4:i * 4 + 4]
        if 1 <= i <= 13:
            w4 = [inv_mix_col(w) for w in w4]
        dk.append([int.from_bytes(bytes(w), "big") for w in w4])

    s = [int.from_bytes(bytes(ct16[j * 4:j * 4 + 4]), "big") ^ dk[14][j] for j in range(4)]
    for rnd in range(13, 0, -1):
        t = [0] * 4
        for j in range(4):
            # inverse shift rows: for decrypt T-table, byte picks:
            b0 = (s[j] >> 24) & 0xFF
            b1 = (s[(j + 3) % 4] >> 16) & 0xFF
            b2 = (s[(j + 2) % 4] >> 8) & 0xFF
            b3 = s[(j + 1) % 4] & 0xFF
            t[j] = TD[0][b0] ^ TD[1][b1] ^ TD[2][b2] ^ TD[3][b3] ^ dk[rnd][j]
        s = t
    out = bytearray(16)
    for j in range(4):
        b0 = (s[j] >> 24) & 0xFF
        b1 = (s[(j + 3) % 4] >> 16) & 0xFF
        b2 = (s[(j + 2) % 4] >> 8) & 0xFF
        b3 = s[(j + 1) % 4] & 0xFF
        v = (ISBOX[b0] << 24) | (ISBOX[b1] << 16) | (ISBOX[b2] << 8) | ISBOX[b3]
        v ^= dk[0][j]
        out[j * 4:j * 4 + 4] = v.to_bytes(4, "big")
    return bytes(out)


def main():
    key = bytes.fromhex("603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4")
    pt = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
    want = bytes.fromhex("f3eed1bdb5d2a03c064b5a7e3db181f8")
    got = dec_block(want, key)
    print("selftest:", "OK" if got == pt else f"FAIL got={got.hex()} want={pt.hex()}")
    ref = AES.new(key, AES.MODE_ECB).decrypt(bytes(range(16)))
    got2 = dec_block(bytes(range(16)), key)
    print("refcheck:", "OK" if got2 == ref else f"FAIL got={got2.hex()} ref={ref.hex()}")
    if got == pt and got2 == ref:
        json.dump({"td": TD, "isbox": ISBOX}, open("td_tables.json", "w"))
        print("[+] td_tables.json written")


if __name__ == "__main__":
    main()
