"""v2 解密器：key 直接从 packet 自带（ct 尾部 32B ASCII），无需内存扫描。
packet = [4B 总长][gzip( AES_CBC(JSON+PKCS7) || key_ascii(32B) )]（无 gzip 时同构平铺）
响应侧：独立尝试各类内嵌 key 假设。
用法：./.venv/Scripts/python.exe decrypt_all_v2.py
"""
import base64
import glob
import gzip
import io
import json
import os
import re
import zlib

from Crypto.Cipher import AES

IV = b'JOSYdf8ys97uhFYS'
PRINTABLE = set(range(0x20, 0x7f)) | {9, 10, 13}
# 抓包目录：AUTOBA_CAPTURE_DIR 优先（本机见 env.local.bat），否则相对 cwd 的 capture/ba
CAP = os.environ.get('AUTOBA_CAPTURE_DIR') or r'capture/ba'
PAIRS_FILE = r'./protocol_hash_pairs.json'
PLAIN_LOG = r'./session_plain_all.jsonl'
PKT_RE = re.compile(
    r'name="packet"\r?\nContent-Type: text/plain; charset=utf-8\r?\n'
    r'Content-Length: \d+\r?\n\r?\n([A-Za-z0-9+/=]+)')


def unpack_packet(raw):
    """返回 (enc_ct, key32, declared)。key32 可能为 None。"""
    declared = int.from_bytes(raw[:4], 'little')
    body = raw[4:]
    if body[:2] == b'\x1f\x8b':
        do = zlib.decompressobj(16 + zlib.MAX_WBITS)
        full = do.decompress(body)
        if do.unused_data:
            return None, None, declared
    else:
        full = body
    if len(full) != declared:
        return None, None, declared
    key32 = full[-32:]
    try:
        dec = base64.b64decode(key32, validate=True)
        if len(dec) == 24 and all(chr(b) in '0123456789abcdef' for b in dec):
            return full[:-32], key32, declared
    except Exception:
        pass
    return full, None, declared


def pr_ratio(b):
    return sum(1 for x in b if x in PRINTABLE) / max(1, len(b))


def main():
    files = sorted(glob.glob(CAP + '/*gsqc-api*.json'), key=os.path.getmtime)
    print(f'[*] 全部样本 {len(files)} 个')
    if os.path.exists(PAIRS_FILE):
        pairs = json.load(open(PAIRS_FILE))
    else:
        pairs = []
        print(f'[!] {PAIRS_FILE} 不存在，将从空集合开始累积')
    seen = {(p['protocol'], p['hash']) for p in pairs}
    log = io.open(PLAIN_LOG, 'w', encoding='utf-8')
    n_ok = n_nofull = 0
    resp_key_hits = []
    for f in files:
        name = os.path.basename(f)
        try:
            d = json.load(io.open(f, encoding='utf-8'))
            m = PKT_RE.search(d.get('req_body', ''))
            if not m:
                continue
            raw = base64.b64decode(m.group(1))
            enc, key32, declared = unpack_packet(raw)
            if enc is None or len(enc) % 16 or len(enc) == 0:
                n_nofull += 1
                continue
            if key32 is None:
                n_nofull += 1
                continue
            pt = AES.new(key32, AES.MODE_CBC, IV).decrypt(enc)
            end = pt.rfind(b'}') + 1
            if end <= 0:
                n_nofull += 1
                continue
            j = json.loads(pt[:end])
            if 'Protocol' not in j or 'Hash' not in j:
                n_nofull += 1
                continue
            n_ok += 1
            url = d.get('url_path', '?')
            log.write(json.dumps({'file': name, 'url': url, 'key': key32.decode(),
                                  'json': j}, ensure_ascii=False) + '\n')
            if (j['Protocol'], j['Hash']) not in seen:
                seen.add((j['Protocol'], j['Hash']))
                pairs.append({'url': url, 'protocol': j['Protocol'],
                              'hash': j['Hash'], 'json_len': end, 'file': name})
                print(f'[+] {url}: Protocol={j["Protocol"]} Hash={j["Hash"]} '
                      f'(N={j["Hash"] & 0xffffffff})')

            # 响应侧：试内嵌 key 假设（resp 去掉 BASE64:/gzip/b64 后尾部 32B）
            rb = d.get('resp_body', '')
            resp = None
            try:
                if rb.startswith('BASE64:'):
                    r1 = base64.b64decode(rb[7:])
                    inner = gzip.decompress(r1) if r1[:2] == b'\x1f\x8b' else r1
                    t = inner.decode('ascii', 'ignore').strip()
                    resp = base64.b64decode(t + '=' * (-len(t) % 4))
                elif rb:
                    r1 = base64.b64decode(rb)
                    resp = gzip.decompress(r1) if r1[:2] == b'\x1f\x8b' else r1
            except Exception:
                resp = None
            if resp and len(resp) > 48 and len(resp) % 16 == 0:
                rk = resp[-32:]
                try:
                    rd = base64.b64decode(rk, validate=True)
                    is_keyish = len(rd) == 24 and all(chr(b) in '0123456789abcdef' for b in rd)
                except Exception:
                    is_keyish = False
                if is_keyish:
                    try:
                        rpt = AES.new(rk, AES.MODE_CBC, IV).decrypt(resp[:-32])
                        if pr_ratio(rpt[:256]) > 0.8:
                            resp_key_hits.append((name, url, rk.decode()))
                            print(f'[!!!] RESP 内嵌 key 命中: {url} key={rk.decode()} pt[:64]={rpt[:64]!r}')
                    except Exception:
                        pass
        except Exception as e:
            n_nofull += 1
    log.close()
    json.dump(pairs, open(PAIRS_FILE, 'w'), indent=1)
    print(f'\n[*] 请求解密成功 {n_ok} / 失败 {n_nofull}，pairs 累计 {len(pairs)} 对')
    print(f'[*] 响应内嵌 key 命中 {len(resp_key_hits)} 个')


if __name__ == '__main__':
    main()
