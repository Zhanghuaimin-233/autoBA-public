"""ba_session.py — 自主会话客户端（2026-10-15 登录关破解的沉淀）。

核心机制（全部实弹验证）：
  1. 自主冷登录：auth 请求体由内置骨架 + `yostar_token.json` 里的 uid/token 构造，
     不依赖抓包（本地有抓包明文时优先用它，字段序更保真）。每次都换新随机 key 重加密
     ——字节级相同会命中服务器去重缓存，返回缓存响应而不建会话。
     实测（2026-10-27）：auth 的 11 个字段里只有 DevId（=yostar UID）、Token、
     Protocol 被服务端校验，其余（设备信息 / ResUrl / Hash）任意值均可。
  2. 资源版本头：RESOURCE-VER/TABLE-VER 过旧时服务器报 90007 并告知最低版本，
     动态升级重试即可。
  3. REQUEST-ID 链（关键！）：auth 响应的 requestid 是下一个请求的头值；
     每个响应颁发下一个请求的 rid。复用旧 rid = 视为重发（Resendable 幂等缓存，
     返回上次响应）；用没见过的 uuid = 33004 request_id does not match。
  4. N 计数：Hash = (Protocol << 32) | N。auth 的 N 是会话起点，此后逐请求 +1。
     N 错也报 33004。
  5. 会话状态（MxToken/rid/N）可落盘续用，避免每次冷登录。

用法：
    from ba_session import Session
    s = Session.login()                    # 冷登录（auth 构造）
    s = Session.load('session_state.json') # 或恢复已存会话
    resp, pkt = s.call('/api/academy/getinfo', 24000)
    resp, pkt = s.call('/api/academy/attendschedule', 24001, business={'ZoneId': 61})
    s.save('session_state.json')
"""
import ast
import base64
import json
import os
import uuid
import warnings

import requests

import ba_crypto as bc

HOST = 'https://gsqc-api.bluearchive-cn.com'
API_MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_map_v2.json')

# 与 decrypt_all_v2 的明文日志同源。存在时优先用它（字段序与真实请求完全一致），
# 缺失则回退到内置骨架——2026-10-27 实测确认 auth 只有 3 个字段被服务端校验。
PLAIN_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_plain_all.jsonl')
YOSTAR_TOKEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yostar_token.json')


def _auth_skeleton():
    """内置 auth 请求骨架。

    2026-10-27 实测（结论见 docs/协议/自主登录.md §3）：11 个字段里服务端只校验
    `DevId`（= yostar UID，与 Token 成对）、`Token`、`Protocol`；其余字段任意值均可，
    空字符串也能建会话。所以设备类字段填中性值，不再依赖抓包。
    """
    protocol = json.load(open(API_MAP, encoding='utf-8'))['/api/account/auth']['protocol']
    return {
        'Protocol': protocol,
        'DevId': '',                       # 运行时填 yostar UID
        'OSVersion': 'Android OS 12 / API-32',
        'DeviceUniqueId': '0' * 32,
        'DeviceModel': 'unknown',
        'DeviceSystemMemorySize': 4096,
        'Token': '',                       # 运行时填 yostar Token
        'SdkPid': 'CN-BA',
        'SubChannel': '',
        'ResUrl': '',
        'Hash': (protocol << 32) | 1,      # 服务端不校验，填标准值即可
    }


def _yostar_credentials():
    """读 yostar_token.json 的 (uid, token)——自主登录的产物。缺失返回 (None, None)。"""
    try:
        d = json.load(open(YOSTAR_TOKEN, encoding='utf-8'))
        uid, tok = d.get('uid'), d.get('token')
        if uid and tok:
            return str(uid), str(tok)
    except Exception:
        pass
    return None, None


def _load_auth_template():
    """构造 account/auth 请求体。

    有本地抓包明文就用它（保真），没有就用内置骨架；两种情况都用
    yostar_token.json 的 uid / token 覆盖 DevId / Token——这两个是服务端
    唯一校验内容，必须与当前登录态一致。
    """
    pkt = None
    if os.path.exists(PLAIN_LOG):
        latest = None
        with open(PLAIN_LOG, encoding='utf-8') as f:
            for line in f:
                d = json.loads(line)
                if d['url'] == '/api/account/auth':
                    latest = d
        if latest is not None:
            pkt = latest['json']
            if isinstance(pkt, str):
                pkt = ast.literal_eval(pkt)

    pkt = dict(pkt) if pkt else _auth_skeleton()

    uid, tok = _yostar_credentials()
    if uid and tok:
        pkt['DevId'] = uid
        pkt['Token'] = tok
    elif pkt.get('DevId') and pkt.get('Token'):
        warnings.warn(
            f'未找到 {os.path.basename(YOSTAR_TOKEN)}，回退使用 auth 模板自带的 DevId/Token'
            f'（可能是历史凭据）；建议先跑 login_oracle.py 完成自主登录')
    else:
        raise RuntimeError(
            f'缺少登录凭据：{YOSTAR_TOKEN} 里没有 uid/token，也没有可用的抓包模板。'
            f'先跑 login_oracle.py 完成手机号+验证码登录。')
    return pkt


def probe_table_version(timeout=20):
    """用极低版本头发一次 auth，问出服务器当前最低数据版本（不建立会话）。

    返回如 '202610131404'；异常或非 90007 返回 None。
    """
    auth_json = _load_auth_template()
    json_str = json.dumps(auth_json, ensure_ascii=False, separators=(',', ':'))
    packet = bc.build_packet(json_str.encode('utf-8'), bc.gen_key_ascii())
    obf = json.load(open(API_MAP, encoding='utf-8'))['/api/account/auth']['obf']
    body, boundary = bc.build_multipart(obf, base64.b64encode(packet).decode())
    h = Session._base_headers()
    h['RESOURCE-VER'] = '202001010000'
    h['TABLE-VER'] = '202001010000'
    h['REQUEST-ID'] = str(uuid.uuid4())
    h['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    r = requests.post(HOST + '/api/account/auth', data=body, headers=h, timeout=timeout)
    resp = bc.decrypt_response(r.text)
    pkt = resp['packet']
    if isinstance(pkt, str):
        pkt = json.loads(pkt)
    reason = str(pkt.get('Reason') or '')
    if pkt.get('ErrorCode') == 90007 and 'lowest=' in reason:
        return reason.split('lowest=')[1].strip()
    return None


class Session:
    def __init__(self, mx, srv, rid, n, acct=None):
        self.mx = mx
        self.srv = srv
        self.acct = acct or srv
        self.rid = rid          # 下一个请求要用的 REQUEST-ID（由上一个响应颁发）
        self.n = n              # 下一个请求的 N
        self._map = json.load(open(API_MAP, encoding='utf-8'))
        self.sess = requests.Session()

    # ---------- 构造 ----------

    @classmethod
    def login(cls, state_path=None):
        """冷登录：重放 auth（新 key 重加密）→ 会话。"""
        auth_json = _load_auth_template()
        json_str = json.dumps(auth_json, ensure_ascii=False, separators=(',', ':'))
        auth_n = auth_json['Hash'] & 0xffffffff
        packet = bc.build_packet(json_str.encode('utf-8'), bc.gen_key_ascii())
        body, boundary = bc.build_multipart(
            json.load(open(API_MAP, encoding='utf-8'))['/api/account/auth']['obf'],
            base64.b64encode(packet).decode())
        r = requests.post(HOST + '/api/account/auth', data=body, headers={
            **cls._base_headers(),
            'REQUEST-ID': str(uuid.uuid4()),
            'Content-Type': f'multipart/form-data; boundary={boundary}',
        }, timeout=30)
        resp = bc.decrypt_response(r.text)
        pkt = resp['packet']
        if isinstance(pkt, str):
            pkt = json.loads(pkt)
        if pkt.get('Protocol') == -1:
            reason = pkt.get('Reason', '')
            # 资源版本过旧 → 服务器告知最低版本，升级头重试一次
            if 'resource version is too low' in reason and 'lowest=' in reason:
                ver = reason.split('lowest=')[1].strip()
                cls._ver_override = ver
                return cls.login()
            raise RuntimeError(f'auth 失败: {reason}')
        sk = pkt['SessionKey']
        s = cls(mx=sk['MxToken'], srv=sk['AccountServerId'],
                rid=resp['requestid'], n=auth_n + 1)
        if state_path:
            s.save(state_path)
        return s

    @classmethod
    def load(cls, path):
        st = json.load(open(path, encoding='utf-8'))
        return cls(mx=st['mx'], srv=st['srv'], rid=st['rid'], n=st['n'], acct=st.get('acct'))

    def save(self, path):
        json.dump({'mx': self.mx, 'srv': self.srv, 'rid': self.rid, 'n': self.n,
                   'acct': self.acct}, open(path, 'w', encoding='utf-8'), ensure_ascii=False)

    # ---------- 请求 ----------

    @staticmethod
    def _base_headers():
        h = {
            'APP-VER': '3.0.2', 'PLATFORM-ID': '1', 'CHANNEL-ID': '1',
            'RESOURCE-VER': getattr(cls_ver, 'value', None) or '202610131404',
            'TABLE-VER': getattr(cls_ver, 'value', None) or '202610131404',
            'User-Agent': 'BestHTTP/2 v2.4.0', 'Accept-Encoding': 'gzip',
        }
        return h

    def call(self, url, protocol, business=None, timeout=30):
        """发一个请求：自动 rid 链 + N 递增。返回 (resp, pkt)。"""
        jb = bc.build_request_json(protocol=protocol, n_count=self.n, mx_token=self.mx,
                                   account_server_id=self.srv, account_id=self.acct,
                                   business=business)
        packet = bc.build_packet(jb, bc.gen_key_ascii())
        obf = self._map[url]['obf']
        body, boundary = bc.build_multipart(obf, base64.b64encode(packet).decode())
        h = self._base_headers()
        h['REQUEST-ID'] = self.rid
        h['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        r = self.sess.post(HOST + url, data=body, headers=h, timeout=timeout)
        resp = bc.decrypt_response(r.text)
        pkt = resp['packet']
        if isinstance(pkt, str):
            pkt = json.loads(pkt)
        if pkt.get('Protocol') == -1 and pkt.get('ErrorCode') == 33004:
            raise RuntimeError(f'33004 rid 链断裂/N 不匹配（rid={self.rid[:13]} N={self.n}）'
                               '——会话状态过期，请重新 login()')
        if pkt.get('Protocol') == -1:
            # 错误响应同样颁发下一个 rid，必须推进，否则后续请求会一直拿到同一个错误
            # （实测：mission/multiplereward 报 8000 之后，整个会话的所有接口都卡死）
            nxt = resp.get('requestid')
            if nxt:
                self.rid = nxt
                self.n += 1
            raise RuntimeError(f"协议错误 {pkt.get('ErrorCode')}: {pkt.get('Reason')}")
        # rid 链推进：响应颁发下一个请求的 rid；N 推进
        self.rid = resp.get('requestid') or self.rid
        self.n += 1
        return resp, pkt


class cls_ver:
    """资源版本头覆盖（auth 90007 时自动升级）。"""
    value = None


if __name__ == '__main__':
    import sys
    state = 'session_state.json'
    if os.path.exists(state) and '--fresh' not in sys.argv:
        s = Session.load(state)
        print(f'[load] rid={s.rid[:13]} N={s.n}')
        resp, pkt = s.call('/api/academy/getinfo', 24000)
        print(f'[getinfo] {resp["protocol"]} zones={len(pkt["AcademyDB"]["ZoneVisitCharacterDBs"])}')
    else:
        s = Session.login()
        print(f'[login] rid={s.rid[:13]} N={s.n}')
        resp, pkt = s.call('/api/academy/getinfo', 24000)
        print(f'[getinfo] {resp["protocol"]} zones={len(pkt["AcademyDB"]["ZoneVisitCharacterDBs"])}')
    s.save(state)
    print(f'[save] {state} rid={s.rid[:13]} N={s.n}')
