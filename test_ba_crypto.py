"""ba_crypto v2 自测：与真实抓包逐层比对。
跑法：uv run --with pycryptodome python test_ba_crypto.py
"""
import base64
import json
import glob
import io
import os

import ba_crypto as bc

CAP = r'capture/ba'
TARGET = os.path.join(CAP, '1791883383917_gsqc-api_bluearchive-cn_com_api_cafe_interact.json')

ok = 0
fail = 0


def check(name, cond, detail=''):
    global ok, fail
    if cond:
        ok += 1
        print(f'[PASS] {name}')
    else:
        fail += 1
        print(f'[FAIL] {name} {detail}')


d = json.load(io.open(TARGET, encoding='utf-8'))
mp = bc.parse_multipart(d['req_body'])
print('multipart fields:', {k: (v[:40] + '...' if len(v) > 40 else v) for k, v in mp.items()})

# 1) 解析真实 packet
pt, key = bc.parse_packet_b64(mp['packet'])
j = bc.json_to_dict(pt)
check('parse_packet → JSON', j is not None and j['Protocol'] == 20006,
      f'Protocol={j and j.get("Protocol")}')
check('parse_packet → key 32B ASCII', len(key) == 32 and key.isascii())

# 2) JSON 字节级重建（同字段序）
rebuild = bc.build_request_json(
    protocol=j['Protocol'], n_count=j['Hash'] & 0xffffffff,
    mx_token=j['SessionKey']['MxToken'],
    account_server_id=j['SessionKey']['AccountServerId'],
    account_id=j['AccountId'], business={k: j[k] for k in j if k not in (
        'Protocol', 'Resendable', 'Hash', 'IsTest', 'SessionKey',
        'AccountId', 'OSType')}, ostype=j['OSType'])
end = pt.rfind(b'}') + 1
check('JSON 字节级重建一致', rebuild == pt[:end],
      f'\n  ours={rebuild[:120]!r}\n  real={pt[:end][:120]!r}')

# 3) AES 确定性：同 key 同明文 → 同 ct
full2 = bc.encrypt_payload(rebuild, key)
real_full = __import__('zlib').decompressobj(16 + __import__('zlib').MAX_WBITS).decompress(
    base64.b64decode(mp['packet'])[4:])
check('ct 逐字节还原', full2 == real_full)

# 4) Hash 公式核验（全部 pairs）
pairs = json.load(open('protocol_hash_pairs.json'))
bad = [p for p in pairs if p['hash'] >> 32 != p['protocol']]
check(f'Hash=(Protocol<<32)|N 于 {len(pairs)} 对全部成立', not bad, f'异常 {len(bad)} 条')

# 5) N 会话内连续性（N 回落 = 会话边界，分段检查）
ns = []
for line in io.open('session_plain_all.jsonl', encoding='utf-8'):
    r = json.loads(line)
    ns.append(r['json']['Hash'] & 0xffffffff)
segs, cur = [], [ns[0]]
for a, b in zip(ns, ns[1:]):
    if b < a:  # 会话重置
        segs.append(cur); cur = [b]
    else:
        cur.append(b)
segs.append(cur)
gaps = [(a, b) for s in segs for a, b in zip(s, s[1:]) if b - a not in (0, 1)]
check(f'N 会话内单调（{len(segs)} 个会话段）', not gaps, f'{len(gaps)} 处异常: {gaps[:5]}')
print(f'  各会话段 N: {[ (s[0], s[-1]) for s in segs ]}')

# 6) 全量往返：parse → 原样重加密（ptt 已含 PKCS7，直接 AES 不再填充）
from Crypto.Cipher import AES as _AES
n_rt = 0
for f in glob.glob(CAP + '/*gsqc-api*.json'):
    try:
        dd = json.load(io.open(f, encoding='utf-8'))
        mpp = bc.parse_multipart(dd.get('req_body', ''))
        if 'packet' not in mpp:
            continue
        ptt, kk = bc.parse_packet_b64(mpp['packet'])
        full_rt = _AES.new(kk, _AES.MODE_CBC, bc.IV_CONSTANT).encrypt(ptt) + kk
        body = base64.b64decode(mpp['packet'])[4:]
        full_now = (__import__('zlib').decompressobj(16 + __import__('zlib').MAX_WBITS)
                    .decompress(body) if body[:2] == b'\x1f\x8b' else body)
        if full_rt != full_now:
            print('  [RT-FAIL]', os.path.basename(f))
        else:
            n_rt += 1
    except Exception:
        pass
check(f'往返重加密全部样本一致（{n_rt}）', n_rt >= 860)

print(f'\n===== {ok} pass / {fail} fail =====')
