"""webui/server.py — autoBA WebUI 后端（FastAPI）。

功能：
  - 登录流：手机号 → 天御滑块（TCaptcha，AppID 从服务端配置拉）→ 验证码 → yostar Token
  - 会话：ba_session（rid 链 + N 计数），全局单例 + 锁串行化
  - 业务：学园日程（getinfo / attendschedule）

启动：uv run --with fastapi --with uvicorn --with requests --with pycryptodome python -m uvicorn webui.server:app --port 8800
访问：http://127.0.0.1:8800
"""
import json
import threading
import time
import datetime
import itertools

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from sign_offline import offline_sign
from ba_session import Session

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SDK_HOST = 'https://sdk-api.yostar.cn'
# 登录凭据（yostar UID/Token/设备指纹）从项目根本地凭据文件读取，不入库（见 .gitignore）
_CREDS_FILE = os.path.join(os.path.dirname(APP_DIR), 'yostar_credentials.json')
try:
    _CREDS = json.load(open(_CREDS_FILE, encoding='utf-8'))
except Exception:
    _CREDS = {}
HEAD_TEMPLATE = {
    'PID': 'CN-BA', 'Channel': 'official', 'Platform': 'android', 'Lang': 'zh',
    'DeviceID': _CREDS.get('DeviceID', 'deadbeefdeadbeef'), 'Version': '1.16.1', 'GVersionNo': '73',
    'GBuildNo': '', 'DeviceModel': '24031PN0DC',
    'RID': 'f0ec1a2b-3d4e-4f5a-6b7c-8d9e0a1b2c3d',
    'UID': _CREDS.get('UID', 1000000000),
    'Token': _CREDS.get('Token', 'dededededededededededededededededededede'),
}
STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'session_state.json')
NAME_MAPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables', 'name_maps.json')
FES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables', 'fes_students.json')
PEOPLE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables', 'character_people.json')
API_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api_map_v2.json')

app = FastAPI(title='autoBA WebUI')
_lock = threading.Lock()          # sdk 签名调用串行化
_sess_lock = threading.Lock()     # ba_session rid 链串行化
_session = None                   # 懒加载的 ba_session

_nm = json.load(open(NAME_MAPS, encoding='utf-8'))
char_names = _nm.get('character', {})
loc_names = _nm.get('academy_location', {})
item_names = _nm.get('item', {})
currency_names = _nm.get('currency', {})
api_map = json.load(open(API_MAP, encoding='utf-8'))
fes_ids = set(json.load(open(FES_FILE, encoding='utf-8'))['students'])
people = json.load(open(PEOPLE_FILE, encoding='utf-8'))   # uid → {family, personal}（同位体分组）


def _sdk_post(path: str, body_obj: dict) -> dict:
    """离线签名 + sdk-api POST。"""
    body = json.dumps(body_obj, separators=(',', ':'), ensure_ascii=False)
    head = dict(HEAD_TEMPLATE, Time=int(time.time()))
    head_json = json.dumps(head, separators=(',', ':'), ensure_ascii=False)
    with _lock:
        sig = offline_sign(head_json + body, 0)
    auth = json.dumps({'Head': head, 'Sign': sig}, separators=(',', ':'), ensure_ascii=False)
    r = requests.post(SDK_HOST + path, data=body.encode('utf-8'), headers={
        'Authorization': auth, 'Content-Type': 'application/json',
        'User-Agent': 'okhttp/4.9.3'}, timeout=30)
    return r.json()


def get_session() -> Session:
    global _session
    with _sess_lock:
        if _session is None:
            if os.path.exists(STATE):
                try:
                    _session = Session.load(STATE)
                    _session.call('/api/academy/getinfo', 24000)   # 活性探测
                    _session.save(STATE)
                    return _session
                except Exception:
                    _session = None
            _session = Session.login(state_path=STATE)
        return _session


def call_session(url: str, protocol: int, business: dict | None = None):
    """业务请求；rid 链断 / 会话超时自动重登一次。"""
    s = get_session()
    with _sess_lock:
        try:
            return s.call(url, protocol, business=business)
        except RuntimeError as e:
            msg = str(e)
            if '33004' in msg or '33005' in msg or '过期' in msg or 'time over' in msg:
                global _session
                s2 = Session.login(state_path=STATE)
                resp, pkt = s2.call(url, protocol, business=business)
                _session = s2
                return resp, pkt
            raise


@app.get('/')
def index():
    return FileResponse(os.path.join(APP_DIR, 'index.html'))


@app.get('/api/captcha-config')
def captcha_config():
    d = _sdk_post('/common/config', {})
    if d.get('Code') != 200:
        raise HTTPException(502, f'config 失败: {d}')
    cap = (d.get('Data') or {}).get('AppConfig', {}).get('Captcha', {})
    return {'appid': str(cap.get('AppID', '')), 'enable': bool(cap.get('Enable'))}


class SendSmsReq(BaseModel):
    phone: str
    ticket: str = ''
    randstr: str = ''


@app.post('/api/send-sms')
def send_sms(req: SendSmsReq):
    body = {'PhoneNumber': req.phone, 'Scene': 'login',
            'Captcha': {'Randstr': req.randstr, 'Ticket': req.ticket}}
    d = _sdk_post('/user/send-sms', body)
    if d.get('Code') != 200:
        raise HTTPException(400, f"{d.get('Code')}: {d.get('Msg')}")
    return {'ok': True}


class LoginReq(BaseModel):
    phone: str
    code: str


@app.post('/api/login')
def login(req: LoginReq):
    body = {'Type': 'mobile', 'OpenID': req.phone, 'Token': req.code,
            'UserName': '', 'Secret': ''}
    d = _sdk_post('/user/login', body)
    if d.get('Code') != 200:
        raise HTTPException(400, f"{d.get('Code')}: {d.get('Msg')}")
    user = (d.get('Data') or {}).get('User', {})
    token = user.get('Token')
    uid = user.get('ID')
    json.dump({'uid': uid, 'token': token}, open('yostar_token.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    # token 更新后重置 BA 会话（下次业务请求重新 auth）
    global _session
    with _sess_lock:
        _session = None
        if os.path.exists(STATE):
            os.remove(STATE)
    return {'ok': True, 'uid': uid, 'token': token}


@app.get('/api/session/status')
def session_status():
    try:
        s = get_session()
        resp, pkt = call_session('/api/academy/getinfo', 24000)
        return {'ok': True, 'rid': s.rid[:13], 'n': s.n,
                'uid': s.srv, 'zones': len(pkt['AcademyDB']['ZoneVisitCharacterDBs'])}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:200]}


# ---------- 学生名册 / 日程清票 ----------

CAP = {1: 10, 2: 10, 3: 20, 4: 30, 5: 100}   # 好感上限按星级
DAILY_TICKETS = 7        # 实测每日 4:00 刷新；CurrencyExcel 写 10（与国服实际不符）
ROSTER_TTL = 120

_roster = {'ts': 0.0, 'data': {}}
_ztab = None
_favor_table = None


def _favor_exp() -> dict:
    """FavorLevelExcel: Level → 升到下一级所需经验。"""
    global _favor_table
    if _favor_table is None:
        rows = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           'tables', 'full', 'ExcelDB', 'FavorLevelExcel.json'),
                              encoding='utf-8'))
        _favor_table = {r['Level']: (r.get('ExpType') or [0])[0] for r in rows}
    return _favor_table


def _remain_exp(rank: int, cap: int, exp: int) -> int:
    """距离好感上限还剩多少经验（单次日程基准 25，Bonus 翻倍 50）。"""
    if cap <= 0:
        return 10 ** 6
    t = _favor_exp()
    need = sum(t.get(lv, 0) for lv in range(rank, cap))
    return max(0, need - exp)


def _expected_gain(remain: int) -> float:
    """25% 概率翻倍下的期望好感。"""
    return 0.75 * min(25, remain) + 0.25 * min(50, remain)


def _zone_table() -> dict:
    global _ztab
    if _ztab is None:
        rows = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           'tables', 'full', 'ExcelDB', 'AcademyZoneExcel.json'),
                              encoding='utf-8'))
        _ztab = {r['Id']: r for r in rows}
    return _ztab


_sync = {'ts': 0.0, 'pkt': None}
SYNC_TTL = 60


def login_sync(force: bool = False) -> dict:
    """loginsync(1017) 原始响应（名册 + 双厅状态都在里面）。"""
    if not force and _sync['pkt'] and time.time() - _sync['ts'] < SYNC_TTL:
        return _sync['pkt']
    _, pkt = call_session('/api/account/loginsync', 1017,
                          business={'SyncProtocols': [20000, 1003, 2000], 'SkillCutInOption': 'Never'})
    _sync.update(ts=time.time(), pkt=pkt)
    return pkt


def fetch_roster(force: bool = False) -> dict:
    """已解锁学生名册：loginsync(1017) → CharacterListResponse。含好感/星级/收藏。"""
    if not force and _roster['data'] and time.time() - _roster['ts'] < ROSTER_TTL:
        return _roster['data']
    pkt = login_sync(force=force)
    dbs = (pkt.get('CharacterListResponse') or {}).get('CharacterDBs') or []
    data = {}
    for c in dbs:
        uid = str(c['UniqueId'])
        star = c.get('StarGrade') or 1
        cap = CAP.get(star, 0)
        rank = c.get('FavorRank') or 0
        data[uid] = {
            'uid': int(uid), 'serverId': c.get('ServerId'),
            'name': char_names.get(uid, f'#{uid}'),
            'star': star, 'level': c.get('Level'),
            'rank': rank, 'exp': c.get('FavorExp') or 0,
            'cap': cap, 'favorite': bool(c.get('IsFavorite')),
            'fes': uid in fes_ids,
            'capped': cap > 0 and rank >= cap,
        }
    _roster.update(ts=time.time(), data=data)
    return data


def fetch_academy():
    """今日访客（ZoneId → 学生）与今日已执行的 Zone 集合。"""
    _, pkt = call_session('/api/academy/getinfo', 24000)
    ac = pkt.get('AcademyDB') or {}
    visitors = ac.get('ZoneVisitCharacterDBs') or {}
    used = {int(z) for z in (ac.get('ZoneScheduleGroupRecords') or {})}
    return visitors, used


def _zone_members(visitors: dict, roster: dict) -> dict:
    ztab = _zone_table()
    out = {}
    for zs, lst in visitors.items():
        zid = int(zs)
        members = []
        for st in lst:
            uid = str(st['UniqueId'])
            r = roster.get(uid)
            owned = st.get('ServerId', 0) > 0 and r is not None
            rank = (r or {}).get('rank') or 0
            cap = (r or {}).get('cap') or 0
            remain = _remain_exp(rank, cap, (r or {}).get('exp') or 0) if owned else 0
            members.append({
                'uid': int(uid),
                'name': (r or {}).get('name') or char_names.get(uid, f'#{uid}'),
                'owned': owned,
                'rank': (r or {}).get('rank'),
                'cap': (r or {}).get('cap'),
                'remain': remain,
                'ev': _expected_gain(remain) if owned and not (r or {}).get('capped') else 0.0,
                'favorite': bool((r or {}).get('favorite')),
                'capped': bool((r or {}).get('capped')) if owned else True,
            })
        row = ztab.get(zid)
        out[zid] = {
            'zone': zid,
            'locationName': loc_names.get(str(row['LocationId']), f'Loc{row["LocationId"]}') if row else '',
            'members': members,
        }
    return out


def build_plan(selected_ids):
    """三轮筛选：指定学生 → 收藏学生 → 好感最高的 Zone（按可涨人数）。"""
    roster = fetch_roster()
    visitors, used = fetch_academy()
    zmap = _zone_members(visitors, roster)
    sel = {int(x) for x in selected_ids}

    def open_owned(m):
        return m['owned'] and not m['capped']

    def qualify(zid, pred):
        hits = [m for m in zmap[zid]['members'] if open_owned(m) and pred(m)]
        return hits

    picked, plan = set(), []

    def add_round(no, label, pred, primary='hits'):
        cands = []
        for zid in zmap:
            if zid in used or zid in picked:
                continue
            hits = qualify(zid, pred)
            if not hits:
                continue
            open_members = [m for m in zmap[zid]['members'] if open_owned(m)]
            favor = round(sum(m['ev'] for m in open_members))
            cands.append((zid, hits, len(open_members), favor))
        # 第一/二轮：命中人数优先；第三轮：好感收益优先
        if primary == 'hits':
            cands.sort(key=lambda t: (-len(t[1]), -t[3], t[0]))
        else:
            cands.sort(key=lambda t: (-t[3], -t[2], t[0]))
        for zid, hits, gains, favor in cands:
            picked.add(zid)
            plan.append({
                'round': no, 'roundLabel': label, 'zone': zid,
                'locationName': zmap[zid]['locationName'],
                'targets': [{'uid': m['uid'], 'name': m['name'], 'rank': m['rank'],
                             'cap': m['cap'], 'favorite': m['favorite']} for m in hits],
                'gain': gains, 'favor': favor,
                'members': zmap[zid]['members'],
            })

    add_round(1, '指定学生', lambda m: m['uid'] in sel)
    add_round(2, '收藏学生', lambda m: m['favorite'])
    add_round(3, '好感优先', lambda m: True, primary='favor')

    est = max(0, DAILY_TICKETS - len(used))
    limit = est + 3 if est else 3          # 余票估算可能偏保守，多备 3 条；实际以服务端为准
    plan = plan[:limit]
    return {
        'tickets': {'daily': DAILY_TICKETS, 'used': len(used), 'estimated': est},
        'plan': plan,
        'selected': sorted(sel),
        'roster': roster,
    }


@app.get('/api/characters')
def characters(refresh: int = 0):
    r = fetch_roster(force=bool(refresh))
    out = sorted(r.values(), key=lambda x: (not x['favorite'], -x['rank'], x['name']))
    return {'count': len(out), 'characters': out}


@app.get('/api/academy/zones')
def academy_zones():
    """今日 Zone 访客一览（只读）。"""
    roster = fetch_roster()
    visitors, used = fetch_academy()
    zmap = _zone_members(visitors, roster)
    out = []
    for zid, z in zmap.items():
        members = [{'uid': m['uid'], 'name': m['name'], 'owned': m['owned'],
                    'rank': m['rank'], 'cap': m['cap'], 'capped': m['capped'],
                    'favorite': m['favorite']} for m in z['members']]
        out.append({'zone': zid, 'locationName': z['locationName'],
                    'used': zid in used,
                    'openCount': sum(1 for m in members if m['owned'] and not m['capped']),
                    'members': members})
    out.sort(key=lambda x: (x['used'], -x['openCount'], x['zone']))
    return {'zones': out, 'used': len(used), 'total': len(out)}


class PlanReq(BaseModel):
    students: list[int] = []


@app.post('/api/schedule/plan')
def schedule_plan(req: PlanReq):
    j = build_plan(req.students)
    r = j.pop('roster')
    j['counts'] = {'roster': len(r), 'selected': len(req.students)}
    return j


@app.post('/api/schedule/clear')
def schedule_clear(req: PlanReq):
    """按方案顺序执行，券尽即停。"""
    built = build_plan(req.students)
    steps, tickets, stopped = [], None, None
    for item in built['plan']:
        zid = item['zone']
        try:
            resp, pkt = call_session('/api/academy/attendschedule', 24001,
                                     business={'ZoneId': zid})
        except Exception as e:
            stopped = f'Zone {zid} 中断：{e}'
            break
        pr = pkt.get('ParcelResultDB') or {}
        tickets = ((pr.get('AccountCurrencyDB') or {}).get('CurrencyDict') or {}).get('6')
        chars = [{'name': char_names.get(str(c['UniqueId']), f'#{c["UniqueId"]}'),
                  'rank': c.get('FavorRank'), 'exp': c.get('FavorExp'),
                  'star': c.get('StarGrade')} for c in pr.get('CharacterDBs') or []]
        steps.append({'zone': zid, 'round': item['round'], 'roundLabel': item['roundLabel'],
                      'locationName': item['locationName'],
                      'targets': [t['name'] for t in item['targets']],
                      'characters': chars, 'tickets': tickets})
        if tickets == 0:
            stopped = '日程券已用尽'
            break
    _roster['ts'] = 0.0          # 好感变了，下次重新拉名册
    return {'steps': steps, 'tickets': tickets, 'stopped': stopped,
            'ticketsBefore': built['tickets'], 'planned': len(built['plan'])}



class AttendReq(BaseModel):
    zoneId: int


@app.post('/api/academy/attend')
def academy_attend(req: AttendReq):
    resp, pkt = call_session('/api/academy/attendschedule', 24001,
                             business={'ZoneId': req.zoneId})
    pr = pkt.get('ParcelResultDB') or {}
    cur = (pr.get('AccountCurrencyDB') or {}).get('CurrencyDict', {})
    chars = []
    for c in pr.get('CharacterDBs') or []:
        uid = c.get('UniqueId')
        chars.append({'name': char_names.get(str(uid), f'#{uid}'),
                      'star': c.get('StarGrade'), 'rank': c.get('FavorRank'),
                      'exp': c.get('FavorExp')})
    _roster['ts'] = 0.0          # 好感变了，下次重新拉名册
    return {'protocol': resp['protocol'], 'tickets': cur.get('6'),
            'characters': chars, 'extra': pkt.get('ExtraRewards')}


# ---------- 咖啡厅 ----------

CAFE_INVITE_CD = 20 * 3600      # 每厅独立 20h
PET_CD = 3 * 3600               # 摸头 3h（按厅 × 访客实例）


def _dt(s):
    if not s or str(s).startswith('0001'):
        return None
    try:
        return datetime.datetime.fromisoformat(str(s))
    except ValueError:
        return None


def _cooldown(last, cd):
    """返回 (是否可用, 剩余秒)。"""
    t = _dt(last)
    if t is None:
        return True, 0
    left = cd - (datetime.datetime.now() - t).total_seconds()
    return left <= 0, max(0, int(left))


def _dbid(cid: int) -> int:
    return get_session().srv * 10 + cid


def _fetch_cafe(cid: int) -> dict:
    """咖啡厅状态从 loginsync 的 CafeGetInfoResponse 取（ack 是状态确认接口，不是读取）。"""
    cgi = login_sync().get('CafeGetInfoResponse') or {}
    dbs = cgi.get('CafeDBs') or ([cgi['CafeDB']] if cgi.get('CafeDB') else [])
    for c in dbs:
        if c.get('CafeId') == cid:
            return c
    return {}


def build_cafe_state():
    roster = fetch_roster()
    cafes = []
    for cid in (1, 2):
        db = _fetch_cafe(cid)
        visitors = []
        for uid_s, v in (db.get('CafeVisitCharacterDBs') or {}).items():
            uid = int(uid_s)
            r = roster.get(uid_s)
            owned = (v.get('ServerId') or 0) > 0 and r is not None
            ready, left = _cooldown(v.get('LastInteractTime'), PET_CD)
            visitors.append({
                'uid': uid, 'serverId': v.get('ServerId'),
                'name': (r or {}).get('name') or char_names.get(uid_s, f'#{uid}'),
                'owned': owned,
                'rank': (r or {}).get('rank'), 'cap': (r or {}).get('cap'),
                'capped': bool((r or {}).get('capped')),
                'favorite': bool((r or {}).get('favorite')),
                'fes': bool((r or {}).get('fes')),
                'lastInteract': v.get('LastInteractTime'),
                'petReady': owned and not (r or {}).get('capped') and ready,
                'petCooldown': 0 if ready else left,
            })
        ready, left = _cooldown(db.get('LastSummonDate'), CAFE_INVITE_CD)
        cafes.append({
            'cafeId': cid, 'rank': db.get('CafeRank'),
            'lastSummon': db.get('LastSummonDate'),
            'summonReady': ready, 'summonCooldown': 0 if ready else left,
            'visitors': visitors,
        })
    return {'cafes': cafes, 'roster': roster}


def _person_of(uid):
    p = people.get(str(uid))
    return (p['family'], p['personal']) if p else None


def _evicts_target(uid, present, sel_set):
    """邀请 uid 会顶掉同人的其他形态；若那个形态也是未满目标，则跳过。"""
    key = _person_of(uid)
    if not key:
        return False
    for other in present:
        if other == uid or other not in sel_set:
            continue
        if _person_of(other) == key:
            return True
    return False


def build_cafe_plan(ordered):
    st = build_cafe_state()
    roster = st['roster']
    present = {v['uid']: c['cafeId'] for c in st['cafes'] for v in c['visitors'] if v['owned']}

    sel, notes = [], []
    for uid in ordered:
        r = roster.get(str(uid))
        if not r:
            notes.append({'uid': uid, 'reason': '未拥有'})
        elif r['capped']:
            notes.append({'uid': uid, 'reason': '好感已满'})
        else:
            sel.append(uid)
    sel_set = set(sel)

    present0 = present
    slots = [c['cafeId'] for c in st['cafes'] if c['summonReady']]

    def simulate(order):
        present = dict(present0)
        remaining = list(order)
        plan, sim_notes = [], []
        # 1) 未在厅的目标，按顺序补券位
        for uid in sel:
            if not remaining:
                break
            if uid in present:
                continue
            if _evicts_target(uid, present, sel_set):
                sim_notes.append({'uid': uid, 'reason': '会顶掉同人的另一个目标形态'})
                continue
            cafe = remaining.pop(0)
            plan.append({'order': len(plan) + 1, 'uid': uid, 'name': roster[str(uid)]['name'],
                         'cafeId': cafe, 'action': 'invite', 'reason': '未在厅，直接邀请'})
            present[uid] = cafe
        # 2) 剩余券位：先给每个在场目标各挪一次，券还有剩再回头挪高顺位
        moved = set()
        while remaining:
            pick = next((u for u in sel if u in present and u not in moved), None)
            if pick is None:
                break
            target = next((c for c in remaining if c != present[pick]), None)
            if target is None:
                moved.add(pick)
                continue
            remaining.remove(target)
            plan.append({'order': len(plan) + 1, 'uid': pick, 'name': roster[str(pick)]['name'],
                         'cafeId': target, 'action': 'move', 'reason': '挪厅重置摸头 CD'})
            present[pick] = target
            moved.add(pick)
        while remaining:
            pick = next((u for u in sel if u in present), None)
            if pick is None:
                break
            target = next((c for c in remaining if c != present[pick]), None)
            if target is None:
                break
            remaining.remove(target)
            plan.append({'order': len(plan) + 1, 'uid': pick, 'name': roster[str(pick)]['name'],
                         'cafeId': target, 'action': 'move', 'reason': '二次挪厅，再吃一次摸头'})
            present[pick] = target
        return plan, sim_notes

    # 券位只有两个，枚举分配顺序：先比总步数，再比高顺位学生拿到的次数
    best_plan, best_notes, best_score = [], [], None
    for order in itertools.permutations(slots):
        p, n = simulate(list(order))
        cnt = {u: (1 if u in present0 else 0) for u in sel}
        for step in p:
            cnt[step['uid']] += 1
        sc = (len(p), tuple(cnt[u] for u in sel))
        if best_score is None or sc > best_score:
            best_plan, best_notes, best_score = p, n, sc
    for i, p in enumerate(best_plan, 1):
        p['order'] = i
    return {'plan': best_plan, 'notes': notes + best_notes,
            'slots': slots, 'state': st}


def _pet(cid: int, uid: int) -> dict:
    _, pkt = call_session('/api/cafe/interact', 20006,
                          business={'CafeDBId': _dbid(cid), 'CharacterId': uid})
    return pkt.get('CharacterDB') or {}


def _invite(cid: int, server_id: int):
    return call_session('/api/cafe/summoncharacter', 20015,
                        business={'CafeDBId': _dbid(cid), 'CharacterServerId': server_id})


@app.get('/api/cafe/state')
def cafe_state():
    st = build_cafe_state()
    st.pop('roster', None)
    return st


class CafePlanReq(BaseModel):
    students: list[int] = []


class CafePetReq(BaseModel):
    cafeId: int
    uid: int


@app.post('/api/cafe/plan')
def cafe_plan(req: CafePlanReq):
    j = build_cafe_plan(req.students)
    st = j.pop('state')
    pet_ready = sum(1 for c in st['cafes'] for v in c['visitors'] if v['petReady'])
    return {'plan': j['plan'], 'notes': j['notes'], 'slots': j['slots'],
            'petReady': pet_ready, 'cafes': st['cafes']}


@app.post('/api/cafe/pet')
def cafe_pet(req: CafePetReq):
    ch = _pet(req.cafeId, req.uid)
    _roster['ts'] = 0.0
    _sync['ts'] = 0.0
    return {'uid': ch.get('UniqueId'), 'rank': ch.get('FavorRank'),
            'exp': ch.get('FavorExp'), 'star': ch.get('StarGrade')}


@app.post('/api/cafe/run')
def cafe_run(req: CafePlanReq):
    """先摸遍所有可摸访客，再按方案邀请/挪厅并各摸一次。"""
    st = build_cafe_state()
    steps = []
    for c in st['cafes']:
        for v in c['visitors']:
            if not v['petReady']:
                continue
            try:
                ch = _pet(c['cafeId'], v['uid'])
                steps.append({'type': 'pet', 'cafeId': c['cafeId'], 'uid': v['uid'],
                              'name': v['name'], 'ok': True,
                              'rank': ch.get('FavorRank'), 'exp': ch.get('FavorExp')})
            except Exception as e:
                steps.append({'type': 'pet', 'cafeId': c['cafeId'], 'uid': v['uid'],
                              'name': v['name'], 'ok': False, 'error': str(e)[:120]})

    built = build_cafe_plan(req.students)
    roster = built['state']['roster']
    stopped = None
    for p in built['plan']:
        server_id = (roster.get(str(p['uid'])) or {}).get('serverId')
        if not server_id:
            stopped = f"邀请 {p['name']} 失败：名册缺少 ServerId"
            steps.append({'type': p['action'], 'cafeId': p['cafeId'], 'uid': p['uid'],
                          'name': p['name'], 'ok': False, 'error': stopped})
            break
        try:
            _invite(p['cafeId'], server_id)
        except Exception as e:
            stopped = f"邀请 {p['name']} 到 {p['cafeId']} 号厅失败：{str(e)[:120]}"
            steps.append({'type': p['action'], 'cafeId': p['cafeId'], 'uid': p['uid'],
                          'name': p['name'], 'ok': False, 'error': str(e)[:120]})
            break
        steps.append({'type': p['action'], 'cafeId': p['cafeId'], 'uid': p['uid'],
                      'name': p['name'], 'ok': True})
        try:
            ch = _pet(p['cafeId'], p['uid'])
            steps.append({'type': 'pet', 'cafeId': p['cafeId'], 'uid': p['uid'],
                          'name': p['name'], 'ok': True,
                          'rank': ch.get('FavorRank'), 'exp': ch.get('FavorExp')})
        except Exception as e:
            steps.append({'type': 'pet', 'cafeId': p['cafeId'], 'uid': p['uid'],
                          'name': p['name'], 'ok': False, 'error': str(e)[:120]})
    _roster['ts'] = 0.0
    _sync['ts'] = 0.0
    return {'steps': steps, 'stopped': stopped, 'planned': len(built['plan'])}


# ---------- 社交小组（社团）签到 ----------
CLAN_STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'clan_state.json')
_clan = {'ts': 0.0, 'data': None}
CLAN_TTL = 60


def _game_day(dt=None):
    dt = dt or datetime.datetime.now()
    if dt.hour < 4:
        dt -= datetime.timedelta(days=1)
    return dt.strftime('%Y-%m-%d')


def build_clan_state():
    """进入社团大厅即签到；带 60s 缓存，避免重复请求。"""
    if _clan['data'] and time.time() - _clan['ts'] < CLAN_TTL:
        return _clan['data']
    _, pkt = call_session('/api/clan/lobby', 28000)
    clan = pkt.get('AccountClanDB') or {}
    me = pkt.get('AccountClanMemberDB') or {}
    missions = pkt.get('MissionProgressDBs') or []
    m1603 = next((m for m in missions if m.get('MissionUniqueId') == 1603), None)
    att = int(me.get('AttendanceCount') or 0)

    prev = {}
    if os.path.exists(CLAN_STATE):
        try:
            prev = json.load(open(CLAN_STATE, encoding='utf-8'))
        except Exception:
            prev = {}
    prev_att = int(prev.get('attendance') or 0)
    gained = att - prev_att if prev_att and att > prev_att else 0

    json.dump({'attendance': att, 'day': _game_day(),
               'checked_at': datetime.datetime.now().isoformat(timespec='seconds')},
              open(CLAN_STATE, 'w', encoding='utf-8'), ensure_ascii=False)

    data = {
        'clan': {'id': clan.get('ClanDBId'), 'name': clan.get('ClanName'),
                 'memberCount': clan.get('ClanMemberCount'),
                 'president': clan.get('ClanPresidentNickName'),
                 'notice': clan.get('ClanNotice') or ''},
        'me': {'nick': me.get('AccountNickName'), 'level': me.get('AccountLevel'),
               'attendance': att, 'socialGrade': me.get('ClanSocialGrade'),
               'joinDate': me.get('JoinDate'), 'lastLogin': me.get('LastLoginDate')},
        'gained': gained,
        'checkedToday': bool(_dt(me.get('LastLoginDate'))
                             and _game_day(_dt(me.get('LastLoginDate'))) == _game_day()),
        'mission': ({'id': 1603, 'complete': bool(m1603.get('Complete'))} if m1603 else None),
    }
    _clan.update(ts=time.time(), data=data)
    return data


@app.get('/api/clan/state')
def clan_state():
    return build_clan_state()


@app.post('/api/clan/checkin')
def clan_checkin():
    _clan['ts'] = 0.0
    return build_clan_state()


# ---------- 数据版本校验（新关卡/新内容预警） ----------
TABLE_VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  'tables', 'table_version.json')
RESOURCE_STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'resource_state.json')
_resource = {'ts': 0.0, 'data': None}
RESOURCE_TTL = 3600


def local_table_version():
    try:
        return json.load(open(TABLE_VERSION_FILE, encoding='utf-8')).get('version') or ''
    except Exception:
        return ''


def _read_resource_state():
    if os.path.exists(RESOURCE_STATE):
        try:
            return json.load(open(RESOURCE_STATE, encoding='utf-8'))
        except Exception:
            pass
    return {}


def build_resource_status(force=False):
    """问服务器当前最低数据版本，和本地表版本比对。"""
    if not force and _resource['data'] and time.time() - _resource['ts'] < RESOURCE_TTL:
        return _resource['data']
    local = local_table_version()
    server, err = None, None
    try:
        from ba_session import probe_table_version
        server = probe_table_version()
    except Exception as e:
        err = str(e)[:150]
    state = _read_resource_state()
    ack = state.get('ack')
    outdated = bool(server and local and server > local and server != ack)
    data = {'local': local, 'server': server, 'outdated': outdated, 'ack': ack,
            'checkedAt': datetime.datetime.now().isoformat(timespec='seconds'),
            'error': err}
    if server:
        state.update({'server': server, 'checked_at': data['checkedAt']})
        json.dump(state, open(RESOURCE_STATE, 'w', encoding='utf-8'), ensure_ascii=False)
    _resource.update(ts=time.time(), data=data)
    return data


@app.get('/api/resource/status')
def resource_status(force: int = 0):
    return build_resource_status(bool(force))


class ResourceAckReq(BaseModel):
    version: str = ''


@app.post('/api/resource/ack')
def resource_ack(req: ResourceAckReq):
    state = _read_resource_state()
    state['ack'] = req.version or (state.get('server') or '')
    json.dump(state, open(RESOURCE_STATE, 'w', encoding='utf-8'), ensure_ascii=False)
    _resource['ts'] = 0.0
    return {'ok': True, 'ack': state['ack']}


# ---------- 悬赏通缉 ----------
BOUNTY_MAPS = [
    {'key': 'ChaserA', 'name': '悬赏通缉：高架公路', 'short': '高架公路'},
    {'key': 'ChaserB', 'name': '悬赏通缉：沙漠铁路', 'short': '沙漠铁路'},
    {'key': 'ChaserC', 'name': '悬赏通缉：讲堂', 'short': '讲堂'},
]


def _stage_label(n: int) -> str:
    """国服关卡难度用字母：1 → A，10 → J。"""
    return chr(ord('A') + n - 1) if 1 <= n <= 26 else str(n)
BOUNTY_DAILY = 6
_wd_table = None
_bounty = {'ts': 0.0, 'data': None}
BOUNTY_TTL = 30


def _weekdungeon_table():
    global _wd_table
    if _wd_table is None:
        rows = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           'tables', 'full', 'ExcelDB', 'WeekDungeonExcel.json'),
                              encoding='utf-8'))
        tab = {}
        for r in rows:
            tab.setdefault(r['WeekDungeonType'], []).append(r)
        for k in tab:
            tab[k].sort(key=lambda x: x['StageId'])
        _wd_table = tab
    return _wd_table


def build_bounty_state(force=False):
    if not force and _bounty['data'] and time.time() - _bounty['ts'] < BOUNTY_TTL:
        return _bounty['data']
    tab = _weekdungeon_table()
    _, pkt = call_session('/api/weekdungeon/list', 23000)
    hist = {int(h['StageUniqueId']): h
            for h in (pkt.get('WeekDungeonStageHistoryDBList') or [])}
    known = {r['StageId'] for rows in tab.values() for r in rows}
    by_id = {r['StageId']: r for rows in tab.values() for r in rows}

    maps = []
    for m in BOUNTY_MAPS:
        ids = [r['StageId'] for r in tab.get(m['key']) or []]
        cleared = [sid for sid in ids if _is_3star(hist.get(sid))]
        released = max(ids) if ids else None
        sweepable = max(cleared) if cleared else None
        maps.append({
            'key': m['key'], 'name': m['name'], 'short': m['short'],
            'stageCount': len(ids),
            'released': released,
            'releasedLabel': _stage_label(by_id[released]['Difficulty']) if released in by_id else None,
            'sweepable': sweepable,
            'sweepableLabel': _stage_label(by_id[sweepable]['Difficulty']) if sweepable in by_id else None,
            'newNotCleared': bool(released and sweepable and released > sweepable),
            'noSweepable': sweepable is None,
        })

    unknown = sorted(sid for sid in hist if sid not in known)
    res = build_resource_status()
    data = {
        'maps': maps,
        'dailyTickets': BOUNTY_DAILY,
        'unknownStages': unknown,
        'resource': {'outdated': res.get('outdated'), 'local': res.get('local'),
                     'server': res.get('server')},
    }
    _bounty.update(ts=time.time(), data=data)
    return data


class BountySweepReq(BaseModel):
    counts: dict[str, int] = {}
    force: bool = False


def _sum_parcels(groups):
    agg = {}
    for grp in groups or []:
        for p in grp or []:
            key = p.get('Key') or {}
            t, i = key.get('Type'), key.get('Id')
            agg[(t, i)] = agg.get((t, i), 0) + (p.get('Amount') or 0)
    out = []
    for (t, i), amt in agg.items():
        if t == 4:
            name = item_names.get(str(i), f'Item {i}')
        elif t == 2:
            name = currency_names.get(str(i), f'Currency {i}')
        else:
            name = f'Type{t}:{i}'
        out.append({'name': name, 'amount': amt})
    out.sort(key=lambda x: -x['amount'])
    return out


@app.get('/api/bounty/state')
def bounty_state(force: int = 0):
    return build_bounty_state(bool(force))


@app.post('/api/bounty/sweep')
def bounty_sweep(req: BountySweepReq):
    counts = {k: int(v or 0) for k, v in (req.counts or {}).items() if int(v or 0) > 0}
    total = sum(counts.values())
    if total <= 0:
        raise HTTPException(400, '票数合计为 0')
    if total > BOUNTY_DAILY:
        raise HTTPException(400, f'票数合计 {total} 超过每日 {BOUNTY_DAILY} 张')

    st = build_bounty_state(force=True)
    if st['resource']['outdated'] and not req.force:
        raise HTTPException(409, '游戏数据已更新，可能新增关卡；请先更新 tables，或勾选强制执')
    if st['unknownStages'] and not req.force:
        raise HTTPException(409, f"通关历史里出现表外关卡 {st['unknownStages']}，说明本地表过期；请更新 tables 或勾选强制执")

    steps, tickets, stopped = [], None, None
    for m in st['maps']:
        n = counts.get(m['key'], 0)
        if n <= 0:
            continue
        if not m['sweepable']:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': None,
                          'error': '没有三星通关的关卡，无法扫荡'})
            continue
        if m['newNotCleared'] and not req.force:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': m['sweepable'],
                          'error': f"最高关 {m['released']} 未三星，已停止（勾选强制执可继续刷 {m['sweepable']}）"})
            stopped = f"{m['name']} 最高关 {m['released']} 未三星"
            break
        try:
            _, pkt = call_session('/api/contentsweep/request', 27000, business={
                'Content': 3, 'StageId': m['sweepable'], 'Count': n, 'EventContentId': 0})
        except Exception as e:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': m['sweepable'],
                          'error': str(e)[:150]})
            stopped = f"{m['name']} 扫荡失败"
            break
        pr = pkt.get('ParcelResult') or {}
        cur = ((pr.get('AccountCurrencyDB') or {}).get('CurrencyDict') or {})
        tickets = cur.get('22')
        steps.append({'map': m['name'], 'ok': True, 'count': n, 'stage': m['sweepable'],
                      'stageLabel': m.get('sweepableLabel'),
                      'tickets': tickets, 'rewards': _sum_parcels(pkt.get('ClearParcels'))})
        if tickets == 0:
            stopped = '挑战券已用尽'
            break

    _bounty['ts'] = 0.0
    _sync['ts'] = 0.0
    return {'steps': steps, 'tickets': tickets, 'stopped': stopped}


# ---------- 学院交流会 ----------
SCRIM_MAPS = [
    {'key': 'SchoolA', 'name': '学院交流会 - 崔尼蒂', 'short': '崔尼蒂'},
    {'key': 'SchoolB', 'name': '学院交流会 - 歌赫娜', 'short': '歌赫娜'},
    {'key': 'SchoolC', 'name': '学院交流会 - 千禧年', 'short': '千禧年'},
]
SCRIM_DAILY = 6
_sd_table = None
_scrim = {'ts': 0.0, 'data': None}
SCRIM_TTL = 30


def _schooldungeon_table():
    global _sd_table
    if _sd_table is None:
        rows = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           'tables', 'full', 'ExcelDB', 'SchoolDungeonStageExcel.json'),
                              encoding='utf-8'))
        tab = {}
        for r in rows:
            tab.setdefault(r['DungeonType'], []).append(r)
        for k in tab:
            tab[k].sort(key=lambda x: x['StageId'])
        _sd_table = tab
    return _sd_table


def _is_3star(rec):
    if not rec:
        return False
    if 'StarFlags' in rec:
        return all(bool(x) for x in (rec.get('StarFlags') or []))
    goal = rec.get('StarGoalRecord') or {}
    return all(int(goal.get(k, 0)) for k in ('Clear', 'AllAlive', 'ClearTimeInSec'))


def _stage_ap(row):
    """从 StageEnterCost 里取行动点（Currency 5）消耗。"""
    ids = row.get('StageEnterCostId') or []
    amounts = row.get('StageEnterCostAmount') or []
    for i, cid in enumerate(ids):
        if cid == 5 and i < len(amounts):
            return amounts[i]
    return None


def build_scrim_state(force=False):
    if not force and _scrim['data'] and time.time() - _scrim['ts'] < SCRIM_TTL:
        return _scrim['data']
    tab = _schooldungeon_table()
    _, pkt = call_session('/api/schooldungeon/list', 38000)
    hist = {int(h['StageUniqueId']): h
            for h in (pkt.get('SchoolDungeonStageHistoryDBList') or [])}
    known = {r['StageId'] for rows in tab.values() for r in rows}
    by_id = {r['StageId']: r for rows in tab.values() for r in rows}

    maps = []
    for m in SCRIM_MAPS:
        ids = [r['StageId'] for r in tab.get(m['key']) or []]
        cleared = [sid for sid in ids if _is_3star(hist.get(sid))]
        released = max(ids) if ids else None
        sweepable = max(cleared) if cleared else None
        maps.append({
            'key': m['key'], 'name': m['name'], 'short': m['short'],
            'stageCount': len(ids),
            'released': released,
            'releasedLabel': _stage_label(by_id[released]['Difficulty']) if released in by_id else None,
            'sweepable': sweepable,
            'sweepableLabel': _stage_label(by_id[sweepable]['Difficulty']) if sweepable in by_id else None,
            'ap': _stage_ap(by_id[sweepable]) if sweepable in by_id else None,
            'newNotCleared': bool(released and sweepable and released > sweepable),
            'noSweepable': sweepable is None,
        })

    res = build_resource_status()
    data = {
        'maps': maps,
        'dailyTickets': SCRIM_DAILY,
        'unknownStages': sorted(sid for sid in hist if sid not in known),
        'resource': {'outdated': res.get('outdated'), 'local': res.get('local'),
                     'server': res.get('server')},
        'note': '每关额外消耗行动点：A 10、B–D 15；本工具不校验体力',
    }
    _scrim.update(ts=time.time(), data=data)
    return data


@app.get('/api/scrimmage/state')
def scrimmage_state(force: int = 0):
    return build_scrim_state(bool(force))


@app.post('/api/scrimmage/sweep')
def scrimmage_sweep(req: BountySweepReq):
    counts = {k: int(v or 0) for k, v in (req.counts or {}).items() if int(v or 0) > 0}
    total = sum(counts.values())
    if total <= 0:
        raise HTTPException(400, '票数合计为 0')
    if total > SCRIM_DAILY:
        raise HTTPException(400, f'票数合计 {total} 超过每日 {SCRIM_DAILY} 张')

    st = build_scrim_state(force=True)
    if st['resource']['outdated'] and not req.force:
        raise HTTPException(409, '游戏数据已更新，可能新增关卡；请先更新 tables，或勾选强制执')
    if st['unknownStages'] and not req.force:
        raise HTTPException(409, f"通关历史里出现表外关卡 {st['unknownStages']}，说明本地表过期；请更新 tables 或勾选强制执")

    steps, tickets, stopped = [], None, None
    for m in st['maps']:
        n = counts.get(m['key'], 0)
        if n <= 0:
            continue
        if not m['sweepable']:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': None,
                          'error': '没有三星通关的关卡，无法扫荡'})
            continue
        if m['newNotCleared'] and not req.force:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': m['sweepable'],
                          'error': f"最高关 {m['released']} 未三星，已停止（勾选强制执可继续刷 {m['sweepable']}）"})
            stopped = f"{m['name']} 最高关 {m['released']} 未三星"
            break
        try:
            _, pkt = call_session('/api/contentsweep/request', 27000, business={
                'Content': 8, 'StageId': m['sweepable'], 'Count': n, 'EventContentId': 0})
        except Exception as e:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': m['sweepable'],
                          'error': str(e)[:150]})
            stopped = f"{m['name']} 扫荡失败"
            break
        pr = pkt.get('ParcelResult') or {}
        cur = ((pr.get('AccountCurrencyDB') or {}).get('CurrencyDict') or {})
        tickets = cur.get('23')
        steps.append({'map': m['name'], 'ok': True, 'count': n, 'stage': m['sweepable'],
                      'stageLabel': m.get('sweepableLabel'), 'ap': m.get('ap'),
                      'tickets': tickets, 'rewards': _sum_parcels(pkt.get('ClearParcels'))})
        if tickets == 0:
            stopped = '挑战券已用尽'
            break

    _scrim['ts'] = 0.0
    _sync['ts'] = 0.0
    return {'steps': steps, 'tickets': tickets, 'stopped': stopped}
