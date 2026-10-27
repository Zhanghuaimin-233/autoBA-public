"""AiriSg 签名的纯 Python 实现（不依赖原生库或外部进程）。

算法（由 libairisgcore.so 的 sign 路径还原）：
- SHA-256 摘要
- RSA-1024 PKCS#1 v1.5 填充，私钥运算
- 128 字节大端输出，标准 base64（带 '=' 补齐）

mode 0 / 1 分别使用两把不同的 RSA-1024 私钥；两把私钥均从库的 .rodata
（0xB8FE0 / 0xB930C，0x32C 字节，逐字节 XOR 0xA5）解出 base64 后得到 PKCS#1 DER。
"""
import base64
import hashlib

# 两把密钥的 PKCS#1 RSAPrivateKey DER 的 base64（与 extract_keys.py 输出一致）。
_KEY_B64 = (
    # mode 0
    (
        "MIICXQIBAAKBgQDBdHUbBS5ZEnYbmLzUagVUD+WnG3h7vtPIb6lxLsIONtE35JEIPY3Q6+Klv+mMAR2f8yoxp/OAD2QGwOhp"
        "MVT7HK8HyDN6W4mjx6D61/5k3FhHRfokFk4pyJWxCiccqO6tzMgbyqNB8W2vH9qryGdKKmjoeKfyhCKjfI5mI5QSrQIDAQAB"
        "AoGBALUUrn0xV1X26ukgCjkGWKB8FOpb02Z5lEG9C60vKGQnuaUI5R0CiRmzgz7FKfZsIO/UrH04ibwoK+gKcEHu9GxL0+qj"
        "qoq1KgNRhy3nqSqk1EhPmLxfUaaCdGBBI5p4Bb8RAvtCwRABzkYobeZBQcOwSa/az0lpx4+IJu1wZAsdAkEA7RVtp6ia/QAO"
        "JWg2ikQpYDAWB7XtVb8Q/kpGodkLCDbJbxS9+6iXHpnjoGQicwR/AnIqWyp8liPC6agU4hoGowJBANDj4sQj+F8l24KjM04a"
        "Tf0V+NCXr0rhjvKNm1GEIhz56iNxlq5OdMcsv9B88puwvDMN7pvjm/4O3Pgt6tVlJm8CQHa9L7EzoYQq3ergOcigALT7AF2W"
        "QSqbyfAB1UREBuFzRwmKMuhydFVQL4/p9tLyIoZgFVSZf9JWUM1jcCoZbM8CQBc+A/FG/0+26qGyfvblvl+2niS3e+2dA0bB"
        "stJzHUiUFhUzgkyKtjujIwSTonroQ0h6+F2oCadPCA8lLMfppUkCQQCAUYlW1Ys3DgUi+3gDZbhWqQajojfYU5PbhxhlZwc5"
        "2TnwB+07yrrBu1yzzb0LbDWSrJUlNL2UZ438GGqrWJ0l"
    ),
    # mode 1
    (
        "MIICWwIBAAKBgQC42/lKqBKC5fApmSS/GYyQeozjfbxXEri1tNpQkd0fBuhHRd/trCs6ldummRu73dwEPbRXb3E/pv7TiNIs"
        "0QeddUTk9gPwATv3yDaNwU4IYA1iU7h0ZAYr12zX7hwu34BtPsMgF2OY+f8Aw9X/MMMU87Qb3ukifnzOxI//xm8NtwIDAQAB"
        "AoGAaQ5yjZAY/RUqOKnU7VnavZ04Bm1FpQJ5wKJoU9Oho+lsBl1alpr68k+KRhLLZSf/ytU6cVpfNPp15cfjEh81QLq8B0kg"
        "jS16ufH6u5So15sdv/xe8xb9pcCZ9bArdVgTOIKNLZasHFInFRYaxmxpwic93+Lnxuxydh76BZGLsZECQQDeNXmBL+YZgh8U"
        "frFMgQsp+Vr6LNAMbgD38+OkGFbBTw6mAtM1lG7sHMj/V4ktYlcp3ovNil+NbTgMh2TjR9pZAkEA1Ph9bCCuk/ljYcMN2Imu"
        "0gGBEfIWP6f4oGr3ApXoTRfUrvDP1dE0qjrx6zE1B91vTtBWjX4QbIu9OkGU8d4GjwJAZxWBp5fT9DN0ParEj4wx5KgEN5kA"
        "bzO9CUpAacjMvmLxlbwrxWh1yN1VtXcjcUV00DyouJKf31kyrkVFXVbhCQJAUPHlUcyWLf3SrRyizZN/E6iosvZtSGKCWA5v"
        "tdbeRTbyik9S3zS1rKHcwwSf4E5kePMsgnjQq0Dteg/lGYzGtwJAaJy1gSZhAd16VXoxBqrSV3LVAI/IanM9z4eF+FLdpkFg"
        "8aCD0rORh430hmql2QjkRWAiNr27K7b7J4egs1os/Q=="
    ),
)

_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _read_tlv(buf, i):
    tag = buf[i]
    i += 1
    ln = buf[i]
    i += 1
    if ln & 0x80:
        n = ln & 0x7F
        ln = int.from_bytes(buf[i:i + n], "big")
        i += n
    return tag, buf[i:i + ln], i + ln


def _parse_pkcs1(der):
    tag, body, end = _read_tlv(der, 0)
    if tag != 0x30 or end != len(der):
        raise ValueError("不是 PKCS#1 RSAPrivateKey DER")
    vals, i = [], 0
    while i < len(body):
        t, v, i = _read_tlv(body, i)
        if t != 0x02:
            raise ValueError("RSAPrivateKey 字段不是 INTEGER")
        vals.append(int.from_bytes(v, "big"))
    if len(vals) != 9 or vals[0] != 0:
        raise ValueError("RSAPrivateKey 字段数/版本不符")
    return vals  # version, n, e, d, p, q, dp, dq, qinv


def _load_keys():
    out = []
    for b64 in _KEY_B64:
        vals = _parse_pkcs1(base64.b64decode(b64))
        n, d = vals[1], vals[3]
        if n.bit_length() != 1024:
            raise ValueError("密钥不是 1024 位")
        out.append((n, d))
    return tuple(out)


_KEYS = _load_keys()


def offline_sign(text, mode=0):
    """返回 AiriSgClient.sign 的等价 base64 签名。

    text: str（按 UTF-8 编码）或 bytes；mode: 0/1（非 0 等价于原生实现的 mode 1）。
    """
    data = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    n, d = _KEYS[1 if mode else 0]
    k = (n.bit_length() + 7) // 8
    t = _SHA256_DIGEST_INFO + hashlib.sha256(data).digest()
    if k < len(t) + 11:
        raise ValueError("密钥长度不足以容纳 PKCS#1 v1.5 填充")
    em = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    sig = pow(int.from_bytes(em, "big"), d, n).to_bytes(k, "big")
    return base64.b64encode(sig).decode("ascii")


if __name__ == "__main__":
    import sys

    msg = sys.argv[1] if len(sys.argv) > 1 else "test"
    m = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    print(offline_sign(msg, m))
