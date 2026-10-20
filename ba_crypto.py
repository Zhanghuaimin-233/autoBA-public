"""autoBA 协议加密模块 —— 2026-10-13 完整破解版

国服（CN）请求协议模型（867/867 抓包样本全量验证）：
  packet(b64 解开后) = [4B LE: 载荷总长] + payload
  payload            = gzip( ct || key_ascii )   （不可压缩时 gzip 会用 stored 块，
                        服务器按 gzip magic 嗅探；ct+key 合在一起压）
  ct                 = AES-256-CBC(key_ascii, IV, JSON+PKCS7)
  key_ascii          = 32B ASCII：b64( hex(12B 随机) )，**每个请求随机生成**，
                       以明文形式附在 ct 尾部 —— 服务器从包尾读 key。
                       （没有会话级 key，不存在"key 轮换"——之前是误判）
  IV                 = b"JOSYdf8ys97uhFYS"（编译期常量，跨会话不变）
  JSON 字段序        = Protocol, <业务字段...>, Resendable, Hash, IsTest,
                       SessionKey{AccountServerId, MxToken}, AccountId, OSType
  Hash               = (Protocol << 32) | N ；N = 会话级全局请求计数，
                       首个请求 N=1，每请求 +1（go-plana 参考实现同构；
                       重发复用同一 N）
                       实弹（2026-10-13）：服务器**严格校验 N**——新包
                       N≠服务器计数器+1 → 500；字节级完全相同的重放包
                       走去重缓存 → 200。borrow 会话发请求会把游戏自己的
                       计数器挤后移，游戏下次请求吃 500 后自动重 auth。
  响应侧             = 'BASE64:'+b64(gzip(b64(AES))) 或 纯 b64(AES)，
                       key 与请求 key 无关（链式/内嵌/派生候选均排除），
                       待静态逆向响应解密函数。

参考：go-plana/plana/request_packet.go（Hash 公式）、plana.go:303（RequestCount++）
"""
import base64
import gzip
import os
import re
import uuid
import zlib

from Crypto.Cipher import AES

IV_CONSTANT = b'JOSYdf8ys97uhFYS'
PKT_RE = re.compile(
    r'name="packet"\r?\nContent-Type: text/plain; charset=utf-8\r?\n'
    r'Content-Length: \d+\r?\n\r?\n([A-Za-z0-9+/=]+)')


# ---------- key ----------

def gen_key_ascii(rng=os.urandom) -> bytes:
    """生成 32B ASCII key：b64(hex(12B 随机))，形态与真实抓包一致。"""
    raw12 = rng(12)
    return base64.b64encode(raw12.hex().encode())


def key_from_ascii(key_ascii: bytes) -> bytes:
    assert len(key_ascii) == 32, f'key 长度 {len(key_ascii)} != 32'
    return key_ascii  # AES-256 直接用 32B ASCII


# ---------- packet ----------

def encrypt_payload(json_bytes: bytes, key_ascii: bytes) -> bytes:
    """JSON+PKCS7 → AES-256-CBC → ct，返回 ct || key_ascii。"""
    key = key_from_ascii(key_ascii)
    pad = 16 - len(json_bytes) % 16
    pt = json_bytes + bytes([pad]) * pad
    ct = AES.new(key, AES.MODE_CBC, IV_CONSTANT).encrypt(pt)
    return ct + key_ascii


def decrypt_payload(full: bytes) -> tuple[bytes, bytes]:
    """ct || key_ascii → (JSON 明文(含 PKCS7), key_ascii)。"""
    key_ascii = full[-32:]
    ct = full[:-32]
    pt = AES.new(key_from_ascii(key_ascii), AES.MODE_CBC, IV_CONSTANT).decrypt(ct)
    return pt, key_ascii


def build_packet(json_bytes: bytes, key_ascii: bytes | None = None) -> bytes:
    """构造 packet 二进制：[4B LE 总长] + gzip(ct||key)。

    注意：客户端**永远 gzip**（不可压缩时 stored 块）——实弹验证服务器
    拒绝无 gzip 载荷（bisect C 500）。gzip 容器字节（XFL/mtime）服务器不校验。
    """
    if key_ascii is None:
        key_ascii = gen_key_ascii()
    full = encrypt_payload(json_bytes, key_ascii)
    return len(full).to_bytes(4, 'little') + gzip.compress(full)


def parse_packet(raw: bytes) -> tuple[bytes, bytes]:
    """解析 packet 二进制 → (JSON 明文(含 PKCS7), key_ascii)。"""
    declared = int.from_bytes(raw[:4], 'little')
    body = raw[4:]
    if body[:2] == b'\x1f\x8b':
        do = zlib.decompressobj(16 + zlib.MAX_WBITS)
        full = do.decompress(body)
        assert not do.unused_data and len(full) == declared, 'packet 载荷长度不符'
    else:
        full = body[:declared]
    return decrypt_payload(full)


def parse_packet_b64(packet_b64: str) -> tuple[bytes, bytes]:
    return parse_packet(base64.b64decode(packet_b64))


def json_to_dict(pt: bytes) -> dict:
    end = pt.rfind(b'}') + 1
    return json.loads(pt[:end]) if end else None


import json  # noqa: E402  (json_to_dict 用)


# ---------- 请求 JSON ----------

def build_request_json(protocol: int, n_count: int, mx_token: str,
                       account_server_id: int, account_id: int,
                       business: dict | None = None, ostype: int = 2) -> bytes:
    """构造请求 JSON（字段序与真实抓包一致：Protocol, 业务..., 标准尾）。"""
    obj: dict = {'Protocol': protocol}
    if business:
        obj.update(business)
    obj['Resendable'] = True
    obj['Hash'] = (protocol << 32) | n_count
    obj['IsTest'] = False
    obj['SessionKey'] = {'AccountServerId': account_server_id,
                         'MxToken': mx_token}
    obj['AccountId'] = account_id
    obj['OSType'] = ostype
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False).encode()


# ---------- multipart ----------

def build_multipart(protocol_obf: str, packet_b64: str,
                    boundary: str | None = None) -> tuple[bytes, str]:
    """构造 multipart/form-data 三字段体。返回 (body, boundary)。"""
    if boundary is None:
        boundary = 'BestHTTP_HTTPMultiPartForm_' + os.urandom(4).hex().upper()
    parts = []
    for name, value, extra_len in (('protocol', protocol_obf, len(protocol_obf)),
                                   ('encode', 'True', 4),
                                   ('packet', packet_b64, len(packet_b64))):
        parts.append((
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"\r\n'
            f'Content-Type: text/plain; charset=utf-8\r\n'
            f'Content-Length: {extra_len}\r\n\r\n'
            f'{value}\r\n').encode())
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts), boundary


def parse_multipart(req_body: str) -> dict:
    """从抓包 req_body 提取三字段（字段头行 + 空行 + 单行值）。"""
    out = {}
    for m in re.finditer(r'name="(\w+)"\r?\n(?:[^\r\n]*\r?\n)*?\r?\n([^\r\n]+)',
                         req_body):
        out[m.group(1)] = m.group(2)
    return out


# ---------- 响应 ----------

def decode_response(resp_body: str) -> tuple[bytes, bytes]:
    """响应两种形态 → (JSON 明文 bytes, resp_key)。

    响应模型（2026-10-13 定案，867/867 验证）：
      blob = 'BASE64:'+b64 → gzip → b64 → [ct || resp_key(32B 原始二进制)]
          或 纯 b64 → [ct || resp_key]
      ct = AES-256-CBC(resp_key, IV, JSON+PKCS7)
      响应明文 = {"protocol":"<接口名>","packet":"<转义载荷JSON>","requestid":"..."}
      resp_key 每响应随机（原始二进制形态；请求侧是 b64-hex ASCII 形态），
      与请求 key 无关——**都明文附在密文尾部**，无需内存提取。
    """
    if resp_body.startswith('BASE64:'):
        raw = base64.b64decode(resp_body[7:])
        inner = gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw
        t = inner.decode('ascii').strip()
        blob = base64.b64decode(t + '=' * (-len(t) % 4))
    else:
        raw = base64.b64decode(resp_body)
        blob = gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw
    key = blob[-32:]
    try:
        dec = base64.b64decode(key, validate=True)
        if len(dec) == 24 and all(chr(b) in '0123456789abcdef' for b in dec):
            return blob[:-32], key   # ASCII 形态（兼容）
    except Exception:
        pass
    return blob[:-32], key            # 原始二进制形态


def decrypt_response(resp_body: str) -> dict:
    """一键解响应 → {'protocol','packet'(dict),'requestid'}。"""
    ct, key = decode_response(resp_body)
    pt = AES.new(key_from_ascii(key), AES.MODE_CBC, IV_CONSTANT).decrypt(ct)
    end = pt.rfind(b'}') + 1
    outer = json.loads(pt[:end])
    if isinstance(outer.get('packet'), str):
        outer['packet'] = json.loads(outer['packet'])
    return outer


def new_request_id() -> str:
    return str(uuid.uuid4())
