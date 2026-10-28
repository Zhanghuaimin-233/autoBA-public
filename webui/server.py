"""webui/server.py — autoBA WebUI 后端（FastAPI）。

功能：
  - 登录流：手机号 → 天御滑块（TCaptcha，AppID 从服务端配置拉）→ 验证码 → yostar Token
  - 会话：ba_session（rid 链 + N 计数），全局单例 + 锁串行化
  - 业务：学园日程（getinfo / attendschedule）

启动：start_webui.bat（直接用项目 .venv 里的解释器，不走 uv run 的临时 overlay 环境）
手动：./.venv/Scripts/python.exe -m uvicorn webui.server:app --port 8800
端口：默认 8800，可用环境变量 AUTOBA_PORT 覆盖
访问：http://127.0.0.1:8800
"""
import json
import logging
import threading
import time
import datetime
import itertools
import asyncio
from logging.handlers import TimedRotatingFileHandler

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from sign_offline import offline_sign
from ba_session import Session
from webui import daily        # 一键清日常的执行器（业务函数由本模块注入，见文件末尾）

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- 日志：webui/logs/server.log，按天轮转；保留 7 天（按日期，不按份数） ----------
LOG_DIR = os.path.join(APP_DIR, 'logs')
LOG_RETAIN_DAYS = 7
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('autoba')
if not logger.handlers:                     # uvicorn --reload 会在同进程重复 import
    logger.setLevel(logging.INFO)
    _fh = TimedRotatingFileHandler(os.path.join(LOG_DIR, 'server.log'),
                                   when='midnight', backupCount=LOG_RETAIN_DAYS, encoding='utf-8')
    _fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(funcName)s] %(message)s',
                                       '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(_fh)
    _ch = logging.StreamHandler()
    _ch.setFormatter(logging.Formatter('%(levelname)s [%(funcName)s] %(message)s'))
    logger.addHandler(_ch)

SDK_HOST = 'https://sdk-api.yostar.cn'
# 登录凭据（yostar UID/Token/设备指纹）从项目根本地凭据文件读取，不入库（见 .gitignore）
_CREDS_FILE = os.path.join(os.path.dirname(APP_DIR), 'yostar_credentials.json')
try:
    _CREDS = json.load(open(_CREDS_FILE, encoding='utf-8'))
except Exception as e:
    _CREDS = {}
    logger.warning('凭据文件未加载（%s），登录相关功能会失败：%s', _CREDS_FILE, e)

# 客户端版本头：游戏更新后改 data/client_version.json 即可，不用动代码
_CLIENT_FILE = os.path.join(os.path.dirname(APP_DIR), 'data', 'client_version.json')
try:
    _CLIENT = json.load(open(_CLIENT_FILE, encoding='utf-8'))
except Exception as e:
    _CLIENT = {}
    logger.warning('client_version.json 未加载（%s），用内置默认版本：%s', _CLIENT_FILE, e)

HEAD_TEMPLATE = {
    'PID': 'CN-BA', 'Channel': 'official', 'Platform': 'android', 'Lang': 'zh',
    'DeviceID': _CREDS.get('DeviceID', 'deadbeefdeadbeef'),
    'Version': _CLIENT.get('Version', '1.16.1'),
    'GVersionNo': _CLIENT.get('GVersionNo', '73'),
    'GBuildNo': _CLIENT.get('GBuildNo', ''),
    'DeviceModel': _CLIENT.get('DeviceModel', '24031PN0DC'),
    'UID': _CREDS.get('UID', 1000000000),
    'Token': _CREDS.get('Token', 'dededededededededededededededededededede'),
}
STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'session_state.json')
NAME_MAPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables', 'name_maps.json')
FES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables', 'fes_students.json')
PEOPLE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tables', 'character_people.json')
API_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api_map_v2.json')

app = FastAPI(title='autoBA WebUI')


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    """兜住所有未捕获异常：完整堆栈进日志，前端拿 detail（与 HTTPException 同格式）。"""
    logger.exception('未处理异常 %s %s', request.method, request.url.path)
    return JSONResponse({'detail': f'{type(exc).__name__}: {exc}'[:200]}, status_code=500)


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(os.path.join(STATIC_DIR, 'icons'), exist_ok=True)
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
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
GOODS_INFO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'tables', 'goods_info.json')
try:
    goods_info = json.load(open(GOODS_INFO, encoding='utf-8'))   # goodsId → {icon,name,desc,rarity}
except Exception as e:
    goods_info = {}
    logger.warning('goods_info.json 加载失败，商店商品名/图标会缺：%s', e)
# 学生名 → 碎片图标（item_names 里「XX的神名文字」的 icon 字段就是它）
_SHARD_SUFFIX = '的神名文字'
try:
    _item_meta = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                             'tables', 'item_names.json'), encoding='utf-8'))
    shard_icons = {v['name_cn'][:-len(_SHARD_SUFFIX)]: v['icon']
                   for v in _item_meta.values()
                   if (v.get('name_cn') or '').endswith(_SHARD_SUFFIX) and v.get('icon')}
except Exception as e:
    shard_icons = {}
    logger.warning('item_names.json 加载失败，学生碎片图标会缺：%s', e)
# 商店表每行的 LocalizeEtcId → 中文名/描述（比 goods_info 更权威，覆盖全部商品）
try:
    _loc_etc = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           'tables', 'full', 'ExcelDB', 'LocalizeEtcExcel.json'),
                              encoding='utf-8'))
    localize_etc = {r['Key']: r for r in _loc_etc}
except Exception as e:
    localize_etc = {}
    logger.warning('LocalizeEtcExcel.json 加载失败，商店商品名会退回 goods_info：%s', e)


def _sdk_post(path: str, body_obj: dict) -> dict:
    """离线签名 + sdk-api POST。"""
    body = json.dumps(body_obj, separators=(',', ':'), ensure_ascii=False)
    # RID 是请求标识，每次请求生成新的（原来是固定常量）
    head = dict(HEAD_TEMPLATE, Time=int(time.time()), RID=str(uuid.uuid4()))
    head_json = json.dumps(head, separators=(',', ':'), ensure_ascii=False)
    # 签名是纯函数（reverse/sign_pure.py），无共享状态，不需要串行化
    sig = offline_sign(head_json + body, 0)
    auth = json.dumps({'Head': head, 'Sign': sig}, separators=(',', ':'), ensure_ascii=False)
    try:
        r = requests.post(SDK_HOST + path, data=body.encode('utf-8'), headers={
            'Authorization': auth, 'Content-Type': 'application/json',
            'User-Agent': 'okhttp/4.9.3'}, timeout=30)
        return r.json()
    except Exception:
        logger.exception('sdk-api 请求失败：%s', path)
        raise


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
                except Exception as e:
                    _session = None
                    logger.warning('会话活性探测失败，重新登录：%s', e)
            _session = Session.login(state_path=STATE)
            logger.info('已建立新会话')
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
                logger.warning('会话过期（%s），重新登录后重试 %s', msg[:80], url)
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
    # 照抄客户端的 SyncProtocols：少请求段会拿到空数据（货币/咖啡厅都踩过）
    _, pkt = call_session('/api/account/loginsync', 1017,
                          business={'SyncProtocols': [20000, 1003, 2000, 3000, 5000, 12000, 6000, 22001, 17018,
                                                      21000, 28001, 33000, 19000, 10006, 39006, 44000, 29002,
                                                      30041, 45000, 46000, 46001, 47000, 49000, 27002, 49004],
                                    'SkillCutInOption': 'Never'})
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
    steps, tickets, stopped, stop_kind = [], None, None, None
    for item in built['plan']:
        zid = item['zone']
        try:
            resp, pkt = call_session('/api/academy/attendschedule', 24001,
                                     business={'ZoneId': zid})
        except Exception as e:
            stopped, stop_kind = f'Zone {zid} 中断：{e}', 'error'
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
            stopped, stop_kind = '日程券已用尽', 'done'
            break
    _roster['ts'] = 0.0          # 好感变了，下次重新拉名册
    return {'steps': steps, 'tickets': tickets, 'stopped': stopped, 'stopKind': stop_kind,
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
_ap_cap_cache = None


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
                # 好感满也摸：+0 好感，但算每日/周常「咖啡厅互动」任务计数（10-20 抓包实证）
                'petReady': owned and ready,
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
            notes.append({'uid': uid, 'reason': '好感已满，不占邀请券'})
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


def _ap_cap() -> int:
    """行动点上限：CurrencyExcel(5).OverChargeLimit。"""
    global _ap_cap_cache
    if _ap_cap_cache is None:
        rows = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           'tables', 'full', 'ExcelDB', 'CurrencyExcel.json'),
                              encoding='utf-8'))
        _ap_cap_cache = next((int(r.get('OverChargeLimit') or 0) for r in rows if r.get('ID') == 5), 999)
    return _ap_cap_cache


def _currency(cid: int) -> int:
    cur = ((login_sync().get('AccountCurrencySyncResponse') or {})
           .get('AccountCurrencyDB') or {}).get('CurrencyDict') or {}
    return int(cur.get(str(cid)) or 0)


def _income_gains(pkt: dict) -> list:
    """领取入账明细取自 ParcelResultDB.DisplaySequence，两厅各一条同类货币要合并。"""
    sums = {}
    for d in ((pkt.get('ParcelResultDB') or {}).get('DisplaySequence') or []):
        amt = int(d.get('Amount') or 0)
        pid = (d.get('Key') or {}).get('Id')
        if amt > 0:
            sums[pid] = sums.get(pid, 0) + amt
    return [{'id': pid, 'amount': amt,
             'name': currency_names.get(str(pid), f'货币{pid}')} for pid, amt in sums.items()]


def _receive_income(force: bool = False) -> dict:
    """领取两厅累积产出（信用点 + 行动点）：CafeDBId=0 一次领完。

    行动点已到上限时默认不领——产出留在厅里不会浪费，硬领只会把 AP 溢出掉；
    等 AP 消耗后下一轮巡检自然会领。
    """
    ap, cap = _currency(5), _ap_cap()
    if not force and ap >= cap:
        return {'ok': False, 'skipped': f'行动点 {ap}/{cap} 已满，先消耗再领', 'gains': []}
    _, pkt = call_session('/api/cafe/receivecurrency', 20013,
                          business={'AccountServerId': get_session().srv, 'CafeDBId': 0})
    gains = _income_gains(pkt)
    return {'ok': True, 'gains': gains,
            'text': '、'.join(f"{g['name']} ×{g['amount']}" for g in gains) or '暂无可领取产出'}


@app.get('/api/debug/currency')
def debug_currency():
    cur = ((login_sync().get('AccountCurrencySyncResponse') or {})
           .get('AccountCurrencyDB') or {}).get('CurrencyDict') or {}
    pkt = login_sync()
    top = [k for k in pkt if isinstance(pkt[k], dict)]
    sec = {}
    for k in top:
        if 'urrenc' in k or 'ccount' in k:
            v = pkt[k]
            sec[k] = list(v.keys())[:12]
    return {'count': len(cur),
            'items': {k: v for k, v in sorted(cur.items(), key=lambda x: int(x[0])) if int(k) in (1, 5, 6, 22, 23)},
            'top_sections': top,
            'currency_sections': sec}


@app.get('/api/debug/cafe')
def debug_cafe():
    """咖啡厅产出原始状态（累积金额/舒适度/应用时间），排查领取用。"""
    cgi = login_sync().get('CafeGetInfoResponse') or {}
    out = []
    for c in (cgi.get('CafeDBs') or []):
        p = c.get('ProductionDB') or {}
        out.append({'cafeId': c.get('CafeId'), 'rank': c.get('CafeRank'),
                    'lastUpdate': c.get('LastUpdate'),
                    'applied': c.get('ProductionAppliedTime'),
                    'comfort': p.get('ComfortValue'), 'appliedDate': p.get('AppliedDate'),
                    'infos': p.get('ProductionParcelInfos')})
    return {'ap': _currency(5), 'apCap': _ap_cap(), 'credit': _currency(1), 'cafes': out}


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


@app.post('/api/cafe/claim')
def cafe_claim(force: bool = False):
    """手动领取咖啡厅产出；force=True 时行动点满了也硬领。"""
    try:
        j = _receive_income(force=force)
    except Exception as e:
        raise HTTPException(502, f'领取失败：{str(e)[:120]}')
    _sync['ts'] = 0.0
    return j


@app.post('/api/cafe/run')
def cafe_run(req: CafePlanReq, invite: bool = True, max_invites: int = 99):
    """先领产出，再摸遍所有可摸访客，最后按方案邀请/挪厅并各摸一次。

    invite=False      只领+只摸不邀请（定时巡检的“只摸”轮次）
    max_invites=N     单次最多消耗 N 张邀请券（定时任务每窗口只用 1 张）
    """
    steps = []
    try:
        steps.append({'type': 'claim', **_receive_income()})
    except Exception as e:
        steps.append({'type': 'claim', 'ok': False, 'error': str(e)[:120]})

    st = build_cafe_state()
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

    if not invite:
        _roster['ts'] = 0.0
        _sync['ts'] = 0.0
        return {'steps': steps, 'stopped': None, 'planned': 0}

    built = build_cafe_plan(req.students)
    roster = built['state']['roster']
    stopped, stop_kind = None, None
    for p in built['plan'][:max(0, max_invites)]:
        server_id = (roster.get(str(p['uid'])) or {}).get('serverId')
        if not server_id:
            stopped, stop_kind = f"邀请 {p['name']} 失败：名册缺少 ServerId", 'error'
            steps.append({'type': p['action'], 'cafeId': p['cafeId'], 'uid': p['uid'],
                          'name': p['name'], 'ok': False, 'error': stopped})
            break
        try:
            _invite(p['cafeId'], server_id)
        except Exception as e:
            stopped, stop_kind = f"邀请 {p['name']} 到 {p['cafeId']} 号厅失败：{str(e)[:120]}", 'error'
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
    return {'steps': steps, 'stopped': stopped, 'stopKind': stop_kind, 'planned': len(built['plan'])}


# ---------- 咖啡厅自动摸头 ----------
# 机制：摸头 3h CD（按「厅 × 访客实例」）；访客 4:00 / 16:00 两批刷新。
# 两厅邀请券独立、各 20h CD，所以能错开：4:00 用 1 号厅券摸 4 次 → 16:00 刷新走 →
# 16:00 用 2 号厅券再拉回来摸 4 次 = 一天 8 次。
# 巡检只是"摸到可摸的 + 券好了就按名单邀请"，不预设时段，靠 CD 自然逼近上限。
CAFE_AUTO_INTERVAL = 600
_cafe_auto = {'enabled': False, 'task': None, 'lastTick': 0, 'nextTick': 0,
              'lastResult': None, 'lastError': None, 'lastClaimError': None}


def _load_ui_state() -> dict:
    try:
        with open(UI_STATE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write_ui_state(data: dict):
    tmp = UI_STATE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, UI_STATE)


_LOG_DATE_PAT = re.compile(r'^(?:(\d{4}-\d{2}-\d{2})\.jsonl|server\.log\.(\d{4}-\d{2}-\d{2}))$')
_prune_ts = 0.0


def _prune_old_logs() -> int:
    """删掉超过保留期的日志：按文件名里的日期判断，不看文件个数。

    覆盖两类：操作日志 `YYYY-MM-DD.jsonl`、服务日志轮转产物 `server.log.YYYY-MM-DD`。
    只动匹配命名的文件，目录里别的东西不碰。
    """
    keep_from = datetime.date.today() - datetime.timedelta(days=LOG_RETAIN_DAYS - 1)
    removed = 0
    try:
        names = os.listdir(LOG_DIR)
    except OSError:
        return 0
    for name in names:
        m = _LOG_DATE_PAT.match(name)
        if not m:
            continue
        try:
            d = datetime.date.fromisoformat(m.group(1) or m.group(2))
        except ValueError:
            continue
        if d < keep_from:
            try:
                os.remove(os.path.join(LOG_DIR, name))
                removed += 1
            except OSError:
                pass
    if removed:
        logger.info('清理过期日志 %d 个（保留 %d 天，%s 起）',
                    removed, LOG_RETAIN_DAYS, keep_from.isoformat())
    return removed


def _maybe_prune_logs():
    """每小时最多清一次（跟日志写入顺带触发，不额外起线程）。"""
    global _prune_ts
    now = time.time()
    if now - _prune_ts < 3600:
        return
    _prune_ts = now
    _prune_old_logs()


_maybe_prune_logs()          # 启动时清一次，避免长期不重启时旧日志滞留


def _log_line(text: str, cls: str = ''):
    """后端直接写操作日志（定时任务没有前端可调）。时间戳与前端一致：本地时间 + 偏移。"""
    now = datetime.datetime.now().astimezone()
    os.makedirs(LOG_DIR, exist_ok=True)
    _maybe_prune_logs()
    entry = {'ts': now.isoformat(timespec='seconds'), 'text': text, 'cls': cls}
    with open(os.path.join(LOG_DIR, f"{now.strftime('%Y-%m-%d')}.jsonl"), 'a',
              encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _cafe_window_key(now=None) -> str:
    """当前刷新窗口：4:00-16:00 记作当天 T04，16:00-次日 4:00 记作 T16。"""
    d = now or datetime.datetime.now()
    if d.hour < 4:
        return f"{(d - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}T16"
    if d.hour < 16:
        return f"{d.strftime('%Y-%m-%d')}T04"
    return f"{d.strftime('%Y-%m-%d')}T16"


def _cafe_auto_once():
    """一次巡检：摸遍可摸的；每个刷新窗口只用一张券做邀请/挪厅。

    窗口内首轮：学生在某厅 → 先白摸一次，再用对面厅的券挪过去重置 CD（档位二）
                不在厅   → 直接用券邀请（档位一）
    窗口内后续轮次：invite=False，只摸不动券，把另一张券留给下个窗口
    """
    state = _load_ui_state()
    students = state.get('cafeStudents') or []
    window = _cafe_window_key()
    do_invite = state.get('cafeInviteWindow') != window
    res = cafe_run(CafePlanReq(students=students), invite=do_invite, max_invites=1)
    if do_invite and not res.get('stopped'):
        state['cafeInviteWindow'] = window
        _write_ui_state(state)
    return res


async def _cafe_auto_loop():
    while True:
        try:
            if _cafe_auto['enabled']:
                res = await asyncio.to_thread(_cafe_auto_once)
                steps = res.get('steps') or []
                pets = sum(1 for s in steps if s.get('type') == 'pet' and s.get('ok'))
                inv = sum(1 for s in steps if s.get('type') in ('invite', 'move') and s.get('ok'))
                claim = next((s for s in steps if s.get('type') == 'claim'), {})
                claimed = claim.get('text') if claim.get('ok') and claim.get('gains') else ''
                _cafe_auto['lastResult'] = {
                    'ts': datetime.datetime.now().isoformat(),
                    'pets': pets,
                    'invites': inv,
                    'claimed': claimed or claim.get('skipped') or '',
                    'stopped': res.get('stopped'),
                }
                _cafe_auto['lastError'] = None
                claim_err = '' if (claim.get('ok') or claim.get('skipped')) else (claim.get('error') or '')
                if claim_err and claim_err != _cafe_auto['lastClaimError']:
                    _log_line(f'[自动摸头] 领取收益失败：{claim_err}', 'err')
                _cafe_auto['lastClaimError'] = claim_err
                if pets or inv:
                    _log_line(f'[自动摸头] 摸头 {pets} 次，邀请/挪厅 {inv} 次'
                              + (f'，领取 {claimed}' if claimed else ''), 'ok')
                    _roster['ts'] = 0.0
        except Exception as e:
            _cafe_auto['lastError'] = str(e)[:200]
            _log_line(f'[自动摸头] 失败：{str(e)[:150]}', 'err')
        _cafe_auto['lastTick'] = time.time()
        _cafe_auto['nextTick'] = time.time() + CAFE_AUTO_INTERVAL
        await asyncio.sleep(CAFE_AUTO_INTERVAL)


@app.on_event('startup')
async def _start_cafe_auto():
    st = _load_ui_state()
    _cafe_auto['enabled'] = bool(st.get('cafeAuto'))
    _cafe_auto['task'] = asyncio.create_task(_cafe_auto_loop())


class CafeAutoReq(BaseModel):
    enabled: bool


@app.get('/api/cafe/auto')
def cafe_auto_state():
    return {
        'enabled': _cafe_auto['enabled'],
        'interval': CAFE_AUTO_INTERVAL,
        'lastTick': _cafe_auto['lastTick'],
        'nextTick': _cafe_auto['nextTick'],
        'lastResult': _cafe_auto['lastResult'],
        'lastError': _cafe_auto['lastError'],
    }


@app.post('/api/cafe/auto')
def cafe_auto_toggle(req: CafeAutoReq):
    _cafe_auto['enabled'] = bool(req.enabled)
    if not req.enabled:
        _cafe_auto['nextTick'] = 0
    st = _load_ui_state()
    st['cafeAuto'] = bool(req.enabled)
    _write_ui_state(st)
    return {'ok': True, 'enabled': _cafe_auto['enabled']}


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


# ---------- 界面设置持久化 ----------
# 对齐 autopcr 的做法（配置存后端文件，前端只做即时缓存），我们是单用户，
# 一个文件足够，不像 autopcr 那样按 qid 分目录。
UI_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui_state.json')


@app.get('/api/ui-state')
def get_ui_state():
    try:
        with open(UI_STATE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


@app.put('/api/ui-state')
async def put_ui_state(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(400, '请求体不是合法 JSON')
    if not isinstance(data, dict):
        raise HTTPException(400, '请求体必须是对象')
    data['ts'] = time.time()
    tmp = UI_STATE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, UI_STATE)      # 原子替换，避免写一半断电留下坏文件
    return {'ok': True, 'ts': data['ts']}


# ---------- 操作日志（按天落盘，前端可回看） ----------
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


@app.post('/api/log')
async def post_log(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(400, '请求体不是合法 JSON')
    entries = data.get('entries') if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise HTTPException(400, 'entries 必须是数组')
    os.makedirs(LOG_DIR, exist_ok=True)
    buckets = {}
    for e in entries[:200]:          # 单次上限，防误传大包
        if not isinstance(e, dict):
            continue
        day = str(e.get('day') or '')
        text = str(e.get('text') or '')[:1000]
        if len(day) != 10 or not text:
            continue
        buckets.setdefault(day, []).append(
            {'ts': str(e.get('ts') or ''), 'text': text, 'cls': str(e.get('cls') or '')})
    for day, rows in buckets.items():
        with open(os.path.join(LOG_DIR, f'{day}.jsonl'), 'a', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return {'ok': True, 'written': sum(len(v) for v in buckets.values())}


@app.get('/api/log/dates')
def log_dates():
    try:
        names = [n[:-6] for n in os.listdir(LOG_DIR) if n.endswith('.jsonl')]
    except Exception:
        return []
    return sorted(names, reverse=True)


@app.get('/api/log')
def get_log(date: str = '', limit: int = 800):
    if len(date) != 10 or not date.replace('-', '').isdigit():
        raise HTTPException(400, 'date 需为 YYYY-MM-DD')
    path = os.path.join(LOG_DIR, f'{date}.jsonl')
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows[-limit:]


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


TICKET_STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'ticket_state.json')


# 票类每日补充规则：源自 tables/full/ExcelDB/CurrencyExcel.json
#   DailyRefillAmount / DailyRefillTime=[400]（凌晨 4:00）/ ChargeLimit / OverChargeLimit
# 服务端 CurrencyDict 只保留“最后一次变更后的值”，跨天补票不落库——实测 2026-10-20
# 服务端日程券给 0（UpdateTime 停在昨夜），客户端界面却显示 7。客户端按下面这套规则
# 本地推算，这里照抄同一套逻辑，否则会把 0 当成“没票”。
TICKET_RULES = {
    6:  {'refill': 10, 'cap': None},   # 日程券：上限随学园地点等级总和变化
    22: {'refill': 6,  'cap': 30},     # 悬赏通缉整合票
    23: {'refill': 6,  'cap': 30},     # 学院交流会整合票
    24: {'refill': 1,  'cap': 7},      # 大决战 A
    25: {'refill': 1,  'cap': 7},      # 大决战 B
    26: {'refill': 1,  'cap': 7},      # 大决战 C
    27: {'refill': 1,  'cap': 7},      # 大决战 D
}
# AcademyTicketExcel.json：LocationRankSum → ScheduleTicktetMax
_ACADEMY_TICKET_CAP = ((80, 7), (50, 6), (25, 5), (10, 4), (1, 3))
_rank = {'ts': 0.0, 'sum': None}
RANK_TTL = 600


def _iso_ts(s):
    """ISO 时间串 → 时间戳；空值/占位值返回 None。"""
    if not s or str(s).startswith('0001'):
        return None
    try:
        return datetime.datetime.fromisoformat(str(s)).timestamp()
    except ValueError:
        return None


def _academy_rank_sum() -> int:
    """学园各地点 Rank 之和（日程券上限依据），10 分钟缓存。"""
    if _rank['sum'] is not None and time.time() - _rank['ts'] < RANK_TTL:
        return _rank['sum']
    try:
        _, pkt = call_session('/api/academy/getinfo', 24000)
        s = sum(int(l.get('Rank') or 0) for l in (pkt.get('AcademyLocationDBs') or [])) or 1
    except Exception:
        s = _rank['sum'] or 1
    _rank.update(ts=time.time(), sum=s)
    return s


def _academy_ticket_cap(rank_sum: int) -> int:
    for need, cap in _ACADEMY_TICKET_CAP:
        if rank_sum >= need:
            return cap
    return 3


def _reset_ts() -> float:
    """最近一次 4:00 补票时刻的本地时间戳。"""
    now = datetime.datetime.now()
    t = now.replace(hour=4, minute=0, second=0, microsecond=0)
    if now < t:
        t -= datetime.timedelta(days=1)
    return t.timestamp()


def _ticket_cache(cid: int):
    """本地记录的操作后余额 → (值, 时间戳)。跨天不再直接作废，而是当推算基数。"""
    try:
        with open(TICKET_STATE, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        return None, None
    v = d.get(str(cid))
    if v is None:
        return None, None
    return int(v), _iso_ts(d.get(f'{cid}_ts'))


def _ticket_cache_set(cid: int, value: int):
    """操作响应带回的余额最权威，直接落盘并记时间。"""
    d = {}
    try:
        with open(TICKET_STATE, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        pass
    d[str(cid)] = int(value)
    d[f'{cid}_ts'] = datetime.datetime.now().isoformat()
    d['day'] = _game_day()
    with open(TICKET_STATE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)


def _ticket_balance(cid: int):
    """返回 (余额, 来源)。来源 measured=实测；estimated=按补票规则推算；unknown=未知。

    取“操作响应本地记录”与“loginsync 货币快照”中时间较新者作基准：
    今天变更过 → 服务端值就是当前余额；跨天没动 → 上次值 + 每日补充 × 天数（截上限）。
    """
    rule = TICKET_RULES.get(cid)
    if not rule:
        return None, 'unknown'
    cap = rule['cap']
    if cap is None:
        cap = _academy_ticket_cap(_academy_rank_sum())

    best_v, best_t = _ticket_cache(cid)
    try:
        db = ((login_sync().get('AccountCurrencySyncResponse') or {})
              .get('AccountCurrencyDB') or {})
        cur = db.get('CurrencyDict') or {}
        if str(cid) in cur:
            t = _iso_ts((db.get('UpdateTimeDict') or {}).get(str(cid)))
            if best_t is None or (t is not None and t > best_t):
                best_t, best_v = t, int(cur.get(str(cid)) or 0)
    except Exception:
        pass

    if best_v is None:
        return None, 'unknown'
    reset = _reset_ts()
    if best_t is not None and best_t >= reset:
        return best_v, 'measured'
    days = 1
    if best_t is not None:
        days = max(1, int((reset - best_t) // 86400) + 1)
    return min(best_v + rule['refill'] * days, cap), 'estimated'
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
    _tk, _src = _ticket_balance(22)
    data = {
        'maps': maps,
        'dailyTickets': BOUNTY_DAILY,
        'tickets': _tk,
        'ticketsSrc': _src,
        'unknownStages': sorted(sid for sid in hist if sid not in known),
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
    st = build_bounty_state(force=True)
    balance, _ = _ticket_balance(22)
    if balance is not None and total > balance:
        raise HTTPException(409, f'本地记录的悬赏挑战券为 {balance} 张，不足以扫荡 {total} 张')
    if st['resource']['outdated'] and not req.force:
        raise HTTPException(409, '游戏数据已更新，可能新增关卡；请先更新 tables，或勾选强制执')
    if st['unknownStages'] and not req.force:
        raise HTTPException(409, f"通关历史里出现表外关卡 {st['unknownStages']}，说明本地表过期；请更新 tables 或勾选强制执")

    steps, tickets, stopped, stop_kind = [], None, None, None
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
            stopped, stop_kind = f"{m['name']} 最高关 {m['released']} 未三星", 'done'
            break
        try:
            _, pkt = call_session('/api/contentsweep/request', 27000, business={
                'Content': 3, 'StageId': m['sweepable'], 'Count': n, 'EventContentId': 0})
        except Exception as e:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': m['sweepable'],
                          'error': str(e)[:150]})
            stopped, stop_kind = f"{m['name']} 扫荡失败", 'error'
            break
        pr = pkt.get('ParcelResult') or {}
        cur = ((pr.get('AccountCurrencyDB') or {}).get('CurrencyDict') or {})
        tickets = cur.get('22')
        if tickets is not None:
            _ticket_cache_set(22, int(tickets))
        steps.append({'map': m['name'], 'ok': True, 'count': n, 'stage': m['sweepable'],
                      'stageLabel': m.get('sweepableLabel'),
                      'tickets': tickets, 'rewards': _sum_parcels(pkt.get('ClearParcels'))})
        if tickets == 0:
            stopped, stop_kind = '挑战券已用尽', 'done'
            break

    _bounty['ts'] = 0.0
    _sync['ts'] = 0.0
    return {'steps': steps, 'tickets': tickets, 'stopped': stopped, 'stopKind': stop_kind}


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
    _tk, _src = _ticket_balance(23)
    data = {
        'maps': maps,
        'dailyTickets': SCRIM_DAILY,
        'tickets': _tk,
        'ticketsSrc': _src,
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
    st = build_scrim_state(force=True)
    balance, _ = _ticket_balance(23)
    if balance is not None and total > balance:
        raise HTTPException(409, f'本地记录的学院交流会券为 {balance} 张，不足以扫荡 {total} 张')
    if st['resource']['outdated'] and not req.force:
        raise HTTPException(409, '游戏数据已更新，可能新增关卡；请先更新 tables，或勾选强制执')
    if st['unknownStages'] and not req.force:
        raise HTTPException(409, f"通关历史里出现表外关卡 {st['unknownStages']}，说明本地表过期；请更新 tables 或勾选强制执")

    steps, tickets, stopped, stop_kind = [], None, None, None
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
            stopped, stop_kind = f"{m['name']} 最高关 {m['released']} 未三星", 'done'
            break
        try:
            _, pkt = call_session('/api/contentsweep/request', 27000, business={
                'Content': 8, 'StageId': m['sweepable'], 'Count': n, 'EventContentId': 0})
        except Exception as e:
            steps.append({'map': m['name'], 'ok': False, 'count': n, 'stage': m['sweepable'],
                          'error': str(e)[:150]})
            stopped, stop_kind = f"{m['name']} 扫荡失败", 'error'
            break
        pr = pkt.get('ParcelResult') or {}
        cur = ((pr.get('AccountCurrencyDB') or {}).get('CurrencyDict') or {})
        tickets = cur.get('23')
        if tickets is not None:
            _ticket_cache_set(23, int(tickets))
        steps.append({'map': m['name'], 'ok': True, 'count': n, 'stage': m['sweepable'],
                      'stageLabel': m.get('sweepableLabel'), 'ap': m.get('ap'),
                      'tickets': tickets, 'rewards': _sum_parcels(pkt.get('ClearParcels'))})
        if tickets == 0:
            stopped, stop_kind = '挑战券已用尽', 'done'
            break

    _scrim['ts'] = 0.0
    _sync['ts'] = 0.0
    return {'steps': steps, 'tickets': tickets, 'stopped': stopped, 'stopKind': stop_kind}


# ---------- 战术对抗赛 ----------
# 机制（2026-10-21 实测）：服务端演算整场（IsServerRunBattle），战果随 enterbattle(22004) 响应返回，
# 没有独立结算请求；每场之后 30s 待机，时间戳在 ArenaPlayerInfoDB.BattleEnterActiveTime。
_arena = {'ts': 0.0, 'data': None}
ARENA_TTL = 30


def _arena_tickets() -> int:
    """战术对抗赛挑战券（Currency 7）。"""
    return _currency(7)


def build_arena_state(force=False):
    if not force and _arena['data'] and time.time() - _arena['ts'] < ARENA_TTL:
        return _arena['data']
    _, pkt = call_session('/api/arena/enterlobby', 22000)
    info = pkt.get('ArenaPlayerInfoDB') or {}
    opps = []
    for i, o in enumerate(pkt.get('OpponentUserDBs') or [], 1):
        ts_db = o.get('TeamSettingDB') or {}
        main_ids = [c.get('UniqueId') for c in (ts_db.get('MainCharacters') or []) if c.get('UniqueId')]
        sup_ids = [c.get('UniqueId') for c in (ts_db.get('SupportCharacters') or []) if c.get('UniqueId')]
        leader = ts_db.get('LeaderCharacterId') or (main_ids[0] if main_ids else None)
        opps.append({
            'index': i,
            'accountId': o.get('AccountServerId'),
            'rank': o.get('Rank'),
            'level': o.get('Level'),
            'nick': o.get('NickName'),
            'leader': char_names.get(str(leader)) or (f'#{leader}' if leader else '—'),
            'team': [char_names.get(str(x)) or f'#{x}' for x in (main_ids + sup_ids)[:6]],
            'teamSize': len(main_ids) + len(sup_ids),
        })
    now = time.time()
    daily_next = _iso_ts(info.get('DailyRewardActiveTime'))
    data = {
        'season': info.get('CurrentSeasonId'),
        'group': info.get('PlayerGroupId'),
        'rank': info.get('CurrentRank'),
        'seasonRecord': info.get('SeasonRecord'),
        'allTimeRecord': info.get('AllTimeRecord'),
        'cumulativeReward': info.get('CumulativeTimeReward'),
        'tickets': _arena_tickets(),
        'opponents': opps,
        'serverRunBattle': bool(pkt.get('IsServerRunBattle')),
        'dailyReady': daily_next is None or daily_next <= now,
        'dailyNext': info.get('DailyRewardActiveTime'),
        'timeNext': info.get('TimeRewardLastUpdateTime'),
        'battleNext': info.get('BattleEnterActiveTime'),
        'battleSupported': True,
    }
    _arena.update(ts=time.time(), data=data)
    return data


@app.get('/api/arena/state')
def arena_state(force: int = 0):
    try:
        return build_arena_state(bool(force))
    except Exception as e:
        raise HTTPException(500, f'读取战术对抗赛失败：{e}')


def _claim_arena_rewards(daily=True, cumulative=True) -> dict:
    """领取每日排名奖励与累计时数奖励；两者互相独立，一个失败不影响另一个。"""
    out = {'daily': None, 'cumulative': None}
    if daily:
        try:
            _, pkt = call_session('/api/arena/dailyreward', 22009)
            pr = pkt.get('ParcelResult') or {}
            out['daily'] = {
                'ok': True,
                'nextTime': pkt.get('DailyRewardActiveTime'),
                'rewards': _sum_parcels([pr.get('DisplaySequence')]),
            }
        except Exception as e:
            out['daily'] = {'ok': False, 'error': str(e)[:150]}
    if cumulative:
        try:
            _, pkt = call_session('/api/arena/cumulativetimereward', 22008)
            pr = pkt.get('ParcelResult') or {}
            out['cumulative'] = {
                'ok': True,
                'amount': pkt.get('TimeRewardAmount'),
                'nextTime': pkt.get('TimeRewardLastUpdateTime'),
                'rewards': _sum_parcels([pr.get('DisplaySequence')]),
            }
        except Exception as e:
            out['cumulative'] = {'ok': False, 'error': str(e)[:150]}
    _arena['ts'] = 0.0
    _sync['ts'] = 0.0          # 领奖动了货币，让下次 loginsync 重新拉
    return out


class ArenaRewardReq(BaseModel):
    daily: bool = True
    cumulative: bool = True


@app.post('/api/arena/rewards')
def arena_rewards(req: ArenaRewardReq):
    return _claim_arena_rewards(req.daily, req.cumulative)


# ---------- 战术对抗赛自动清票（后台线程，30s 待机期间可跑别的模块） ----------
_arena_clear = {'running': False, 'battles': [], 'startedAt': None, 'finishedAt': None,
                'error': None, 'stopReason': None, 'claimed': None}


def _arena_wait_cd(next_time) -> int:
    """等到 BattleEnterActiveTime 之后（服务端给的 30s 待机），返回等待秒数。"""
    t = _iso_ts(next_time)
    if t is None:
        return 0
    left = t - time.time()
    if left <= 0:
        return 0
    left = min(left, 90)       # 防守上限，避免脏数据把线程挂死
    time.sleep(left)
    return int(left)


def _arena_pick(st: dict):
    """BAAS 思路：等级低优先（满级服恒同），再打名次最高的那个。"""
    opps = [o for o in (st.get('opponents') or []) if o.get('rank') and o.get('accountId')]
    if not opps:
        return None
    opps.sort(key=lambda o: ((o.get('level') or 0), (o.get('rank') or 10 ** 9)))
    return opps[0]


def _arena_battle(opp: dict) -> dict:
    """打一场：服务端演算，战果直接来自响应。

    客户端进竞技场的动作序列是 enterlobby → syncechelonsettingtime → enterbattle，
    少了中间那步服务端会回 21017（实测）。
    """
    call_session('/api/arena/syncechelonsettingtime', 22016)
    _, pkt = call_session('/api/arena/enterbattle', 22004, business={
        'OpponentAccountServerId': opp['accountId'],
        'OpponentIndex': opp['index'] - 1,      # 请求里是 0 基下标
        'OpponentRank': opp['rank'],
    })
    sm = ((pkt.get('ArenaBattleDB') or {}).get('BattleSummary') or {})
    info = pkt.get('ArenaPlayerInfoDB') or {}
    cur = ((pkt.get('AccountCurrencyDB') or {}).get('CurrencyDict') or {})
    tickets = cur.get('7')
    return {
        'win': sm.get('Winner') == 'Group01',     # Group01 = 攻方（实测对齐过）
        'winner': sm.get('Winner'),
        'endFrame': sm.get('EndFrame'),
        'rank': info.get('CurrentRank'),
        'nextBattle': info.get('BattleEnterActiveTime'),
        'tickets': int(tickets) if tickets is not None else None,
    }


def _arena_clear_worker(max_battles: int, stop_rank1: bool, claim_rewards: bool):
    try:
        while len(_arena_clear['battles']) < max_battles:
            st = build_arena_state(force=True)
            if _arena_tickets() <= 0:
                _arena_clear['stopReason'] = '挑战券已用尽'
                break
            if stop_rank1 and (st.get('rank') or 0) == 1:
                _arena_clear['stopReason'] = '已到第 1 名'
                break
            _arena_wait_cd(st.get('battleNext'))
            st = build_arena_state(force=True)      # 等完 CD 重新拿对手（列表会自动刷新）
            opp = _arena_pick(st)
            if not opp:
                _arena_clear['stopReason'] = '没有可攻击的对手'
                break
            r = _arena_battle(opp)
            _sync['ts'] = 0.0                        # 券数变了，下次 loginsync 重新拉
            _arena_clear['battles'].append({
                'targetRank': opp['rank'], 'targetLevel': opp.get('level'),
                'win': r['win'], 'rank': r['rank'], 'endFrame': r['endFrame'],
            })
            _log_line(f"[竞技场] 打 R{opp['rank']}（Lv{opp.get('level')}）"
                      f"{'胜' if r['win'] else '负'} → 现 R{r['rank']}", 'ok' if r['win'] else 'sub')
            time.sleep(1)                            # 两场之间留一点余量
    except Exception as e:
        logger.exception('[竞技场] 清票线程异常')
        _arena_clear['error'] = str(e)[:200]
        _log_line(f'[竞技场] 清票中断：{_arena_clear["error"]}', 'err')
    finally:
        if claim_rewards:
            try:
                _arena_clear['claimed'] = _claim_arena_rewards(True, True)
            except Exception as e:
                logger.warning('[竞技场] 领奖失败：%s', e)
                _arena_clear['claimed'] = {'error': str(e)[:150]}
        _arena_clear['running'] = False
        _arena_clear['finishedAt'] = datetime.datetime.now().isoformat(timespec='seconds')
        why = _arena_clear.get('stopReason') or ('中断' if _arena_clear.get('error') else '达到上限')
        _log_line(f"[竞技场] 清票结束：{len(_arena_clear['battles'])} 场（{why}）", 'sub')


class ArenaClearReq(BaseModel):
    maxBattles: int = 5
    stopAtRank1: bool = True
    claimRewards: bool = True


@app.post('/api/arena/clear')
def arena_clear(req: ArenaClearReq):
    """启动后台清票：每场之间只等 30s CD，等待期间其他模块可以照常发请求。"""
    if _arena_clear['running']:
        return {'ok': False, 'error': '清票已在执行中', 'running': True}
    tickets = _arena_tickets()
    _arena_clear.update(running=True, battles=[], error=None, stopReason=None,
                        startedAt=datetime.datetime.now().isoformat(timespec='seconds'),
                        finishedAt=None, claimed=None)
    threading.Thread(target=_arena_clear_worker,
                     args=(max(1, req.maxBattles), req.stopAtRank1, req.claimRewards),
                     daemon=True).start()
    return {'ok': True, 'started': True, 'tickets': tickets}


@app.get('/api/arena/clear/status')
def arena_clear_status():
    return dict(_arena_clear, tickets=_arena_tickets())


# ---------- 邮箱 ----------
@app.get('/api/mail/state')
def mail_state():
    _, chk = call_session('/api/mail/check', 7001)
    n = int(chk.get('Count') or 0)
    if n <= 0:
        return {'unread': 0, 'mails': []}
    _, pkt = call_session('/api/mail/list', 7000, business={
        'IsDescending': True, 'IsReadMail': False, 'PivotIndex': 0,
        'PivotTime': '9999-12-31T23:59:59', 'mailSortingRule': 0})
    mails = []
    for m in (pkt.get('MailDBs') or []):
        mails.append({
            'id': m.get('ServerId') or m.get('MailServerId'),
            'title': m.get('Title') or m.get('LocalizedTitle') or '',
            'expire': m.get('ExpireDate') or m.get('ExpireTime'),
        })
    return {'unread': len(mails), 'mails': mails}


@app.post('/api/mail/claim')
def mail_claim():
    st = mail_state()
    ids = [m['id'] for m in st['mails'] if m.get('id')]
    if not ids:
        return {'ok': True, 'count': 0, 'rewards': []}
    _, pkt = call_session('/api/mail/receive', 7002, business={'MailServerIds': ids})
    pr = pkt.get('ParcelResultDB') or {}
    _sync['ts'] = 0.0
    return {'ok': True, 'count': len(ids), 'rewards': _sum_parcels([pr.get('DisplaySequence')])}


# ---------- 任务奖励 ----------
@app.get('/api/mission/state')
def mission_state():
    _, pkt = call_session('/api/mission/list', 8000, business={'EventContentId': None})
    prog = pkt.get('ProgressDBs') or []
    claimed = set(pkt.get('MissionHistoryUniqueIds') or [])
    cats = {}
    for p in prog:
        if p.get('Complete') and p.get('MissionUniqueId') not in claimed:
            c = p.get('Category')
            cats[c] = cats.get(c, 0) + 1
    return {'claimable': cats, 'total': sum(cats.values())}


class MissionClaimReq(BaseModel):
    categories: list[int] = [1, 2, 3]


@app.post('/api/mission/claim')
def mission_claim(req: MissionClaimReq):
    st = mission_state()
    steps = []
    for c in req.categories:
        if not st['claimable'].get(c):
            continue
        try:
            _, pkt = call_session('/api/mission/multiplereward', 8002, business={
                'MissionCategory': c, 'EventContentId': None, 'GuideMissionSeasonId': None})
            pr = pkt.get('ParcelResultDB') or {}
            steps.append({'category': c, 'ok': True,
                          'rewards': _sum_parcels([pr.get('DisplaySequence')])})
        except Exception as e:
            msg = str(e)
            # 8000 = 该类别没有已完成任务（不是错误，只是没得领）
            if '8000' in msg or 'no completed' in msg:
                steps.append({'category': c, 'ok': True, 'skipped': '无可领取'})
            else:
                steps.append({'category': c, 'ok': False, 'error': msg[:120]})
    _sync['ts'] = 0.0
    return {'steps': steps, 'claimable': st['claimable']}


# ---------- 商店（多分类） ----------
# 客户端一次拉全部商店：CategoryList 固定这 11 个分类（抓包实证）
SHOP_CATEGORIES = [0, 36, 37, 1, 21, 2, 33, 10, 25, 26, 20]
# 名称按 ShopExcel.CategoryType 反查（2026-10-21 核对）；活动商店不在此接口，
# 走 eventcontent/shoplist(30014)，所以这里没有「活动」这一类
SHOP_CAT_NAMES = {
    0: '常规道具', 1: '神名精髓I', 2: '总力战',
    10: '战术对抗赛', 20: '熟练证书', 21: '神名精髓II',
    25: '综合战术测试', 26: '悬赏通缉', 33: '大决战',
    36: '青辉石·每日商品', 37: '青辉石·每周商品',
}
_shop_excel = None
_shop_refresh = None


def _shop_row(item_id: int, is_refresh: bool = False):
    """商品 Id → 商店表整行（含 LocalizeEtcId），按是否刷新选表并互相兜底。"""
    global _shop_excel, _shop_refresh
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'tables', 'full', 'ExcelDB')
    if _shop_excel is None:
        _shop_excel = {r['Id']: r for r in json.load(open(os.path.join(base, 'ShopExcel.json'),
                                                          encoding='utf-8'))}
    if _shop_refresh is None:
        _shop_refresh = {r['Id']: r for r in json.load(open(os.path.join(base, 'ShopRefreshExcel.json'),
                                                            encoding='utf-8'))}
    tables = (_shop_refresh, _shop_excel) if is_refresh else (_shop_excel, _shop_refresh)
    for t in tables:
        row = t.get(item_id)
        if row:
            return row
    return {}


def _shop_goods_id(item_id: int, is_refresh: bool = False):
    """商品 Id → GoodsId（购买请求要带这个）。

    ShopExcel 和 ShopRefreshExcel 的 Id 有重叠（如 20000 段），必须按商店是否随机刷新来选表：
    刷新类商店（常规道具/竞技场/青辉石每日·每周）的商品在 ShopRefreshExcel，IsRefreshGoods=true；
    其余（总力战/大决战/演习/悬赏/熟练证书等）在 ShopExcel。
    """
    global _shop_excel, _shop_refresh
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'tables', 'full', 'ExcelDB')
    if _shop_excel is None:
        _shop_excel = {r['Id']: r for r in json.load(open(os.path.join(base, 'ShopExcel.json'),
                                                          encoding='utf-8'))}
    if _shop_refresh is None:
        _shop_refresh = {r['Id']: r for r in json.load(open(os.path.join(base, 'ShopRefreshExcel.json'),
                                                            encoding='utf-8'))}
    tables = (_shop_refresh, _shop_excel) if is_refresh else (_shop_excel, _shop_refresh)
    for t in tables:
        row = t.get(item_id) or {}
        gids = row.get('GoodsId')
        if isinstance(gids, list) and gids:
            return gids[0]
        if isinstance(gids, int) and gids:
            return gids
    return None


def _shop_period(next_date):
    """按 NextAutoRefreshDate 距现在多久推断刷新周期（实测：0/10/36 每日、37 每周、其余每月 1 日）。"""
    t = _iso_ts(next_date)
    if t is None:
        return '不自动刷新'
    days = (t - time.time()) / 86400
    if days <= 1.5:
        return '每日 04:00'
    if days <= 8:
        return '每周'
    if days <= 32:
        return '每月 1 日'
    return f'{int(days)} 天'


@app.get('/api/shop/state')
def shop_state(cats: str = ''):
    want = [int(x) for x in cats.split(',') if x.strip().isdigit()] if cats else SHOP_CATEGORIES
    _, pkt = call_session('/api/shop/list', 10002, business={'CategoryList': want})
    shops = []
    for s in pkt.get('ShopInfos') or []:
        prods = []
        is_refresh = bool(s.get('IsRefresh'))
        for p in s.get('ShopProductList') or []:
            row = _shop_row(p.get('ShopExcelId'), is_refresh)
            gid = _shop_goods_id(p.get('ShopExcelId'), is_refresh)
            meta = goods_info.get(str(gid)) or {}
            loc = localize_etc.get(row.get('LocalizeEtcId')) or {}
            icon = meta.get('icon') or ''
            prods.append({
                'shopExcelId': p.get('ShopExcelId'), 'goodsId': gid, 'isRefresh': is_refresh,
                'limit': p.get('PurchaseCountLimit'), 'bought': p.get('PurchaseCount'),
                'soldOut': bool(p.get('SoldOut')),
                'name': loc.get('NameKr') or meta.get('name') or item_names.get(str(gid)) or f'#{gid}',
                'desc': loc.get('DescriptionKr') or meta.get('desc') or '',
                'rarity': meta.get('rarity') or '',
                'icon': icon,
                'iconUrl': (f'/static/icons/{icon.rsplit("/", 1)[-1]}.png' if icon else ''),
            })
        nxt = s.get('NextAutoRefreshDate')
        shops.append({
            'category': s.get('Category'),
            'name': SHOP_CAT_NAMES.get(s.get('Category'), f'商店{s.get("Category")}'),
            'group': s.get('ShopGroupType'), 'refresh': bool(s.get('IsRefresh')),
            'nextRefresh': nxt,
            'period': _shop_period(nxt),
            'manualRefreshCount': s.get('ManualRefreshCount'),
            'products': prods,
        })
    return {'shops': shops}


class ShopBuyReq(BaseModel):
    shopExcelId: int
    goodsId: int
    count: int = 1
    isRefresh: bool = False


@app.post('/api/shop/buy')
def _shop_buy_one(shop_excel_id: int, goods_id: int, count: int, is_refresh: bool) -> dict:
    _, pkt = call_session('/api/shop/buymerchandise', 10000, business={
        'ShopUniqueId': shop_excel_id, 'GoodsId': goods_id,
        'PurchaseCount': max(1, count), 'IsRefreshGoods': bool(is_refresh)})
    pr = pkt.get('ParcelResultDB') or {}
    _sync['ts'] = 0.0
    return {'ok': True, 'rewards': _sum_parcels([pr.get('DisplaySequence')])}


def shop_buy(req: ShopBuyReq):
    return _shop_buy_one(req.shopExcelId, req.goodsId, req.count, req.isRefresh)


def _refresh_shop(category: int, products=None):
    """刷新一个商店。两种协议按类型分流（实测抓包）：

    - 战术对抗赛（10）走 shop/refresh(10003) {"ShopCategoryType": 10}，消耗竞技场币；
    - 常规道具等“随机商品”商店走 shop/buyrefreshmerchandise(10007)
      {"ShopUniqueIds": [当前商品 id...]}，消耗青辉石（40/60/80）。
    """
    # 实测：buyrefreshmerchandise(10007) 并不会真正刷新商店（只回一份商品列表），
    # 真正生效的是 shop/refresh(10003) + ShopCategoryType。
    return call_session('/api/shop/refresh', 10003, business={'ShopCategoryType': category})


# ---------- 商店自动购买 ----------
# 「轮」= 每天一次的执行周期（不需要刷新商店）：每天推进一轮，直到各商品轮数跑完。
# 例：30体×3轮 + 60体×2轮 → 第 1/2 天各买 30+60，第 3 天只买 30。
# 保护：神名精髓I/II（1、21）与青辉石每日/每周（36、37）不参与自动购买。
SHOP_PROTECTED = {1, 21, 36, 37}
# 只有这两个商店能手动刷新（其余靠每日自动刷新）；手动刷新每日上限 3 次，
# 所以最多 4 轮 = 首轮 + 3 次刷新。
SHOP_MANUAL_REFRESH = {0, 10}
SHOP_MAX_ROUNDS = 4


def _autobuy_cfg() -> dict:
    cfg = (_load_ui_state().get('shopAutobuy') or {})
    return {
        'enabled': bool(cfg.get('enabled')),
        'items': cfg.get('items') or [],
        'lastRun': cfg.get('lastRun'),
        'manualRefresh': sorted(SHOP_MANUAL_REFRESH),
        'maxRounds': SHOP_MAX_ROUNDS,
    }


@app.get('/api/shop/autobuy')
def shop_autobuy_get():
    cfg = _autobuy_cfg()
    cfg['protected'] = sorted(SHOP_PROTECTED)
    return cfg


@app.post('/api/shop/autobuy')
async def shop_autobuy_set(request: Request):
    body = await request.json()
    st = _load_ui_state()
    cfg = st.get('shopAutobuy') or {}
    cfg['enabled'] = bool(body.get('enabled'))
    items = []
    for it in body.get('items') or []:
        try:
            cat = int(it.get('category'))
            sid = int(it.get('shopExcelId'))
        except (TypeError, ValueError):
            continue
        if cat in SHOP_PROTECTED:
            continue
        items.append({
            'shopExcelId': sid, 'category': cat,
            'perRound': max(1, int(it.get('perRound') or 1)),
            'rounds': max(1, int(it.get('rounds') or 1)),
        })
    cfg['items'] = items
    cfg.pop('progress', None)
    cfg.setdefault('lastRun', None)
    st['shopAutobuy'] = cfg
    _write_ui_state(st)
    return {'ok': True, 'count': len(items)}


@app.post('/api/shop/autobuy/run')
async def shop_autobuy_run(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _autobuy_run(bool((body or {}).get('force')))


def _autobuy_run(force: bool = False) -> dict:
    """按「刷新轮」执行自动购买（不跨天保存进度）。

    每轮：把本轮该买的买掉 → 需要下一轮时刷新商店（消耗货币）→ 再买。
    例：30体×3轮 + 60体×2轮 = 第1轮 30+60 → 刷新 → 第2轮 30+60 → 刷新 → 第3轮 只买30。
    只有常规道具(0)与战术对抗赛(10)能手动刷新，其余分类强制 1 轮；
    手动刷新每日上限 3 次 → 轮数上限 4（首轮 + 3 次刷新）。
    """
    cfg = _autobuy_cfg()
    if not force and not cfg['enabled']:
        return {'ok': False, 'skipped': True, 'error': '自动购买未启用'}
    if not cfg['items']:
        return {'ok': True, 'skipped': '没有配置商品'}
    today = datetime.date.today().isoformat()
    if not force and cfg['lastRun'] == today:
        return {'ok': True, 'skipped': f'{today} 已执行过（force 可强制再跑）'}

    # 轮数夹紧：不可手动刷新的分类只能 1 轮
    plan = []
    for it in cfg['items']:
        rounds = it['rounds'] if it['category'] in SHOP_MANUAL_REFRESH else 1
        rounds = max(1, min(SHOP_MAX_ROUNDS, rounds))
        plan.append(dict(it, rounds=rounds))

    steps = []
    bought = 0
    refreshed = 0
    rounds_total = max(p['rounds'] for p in plan)

    for r in range(1, rounds_total + 1):
        active = [it for it in plan if it['rounds'] >= r]
        if not active:
            break

        if r > 1:
            if refreshed >= 3:
                steps.append({'ok': False, 'skipped': '手动刷新已达上限 3 次'})
                break
            st_now = shop_state()
            prods_by_cat = {sh.get('category'): (sh.get('products') or [])
                            for sh in (st_now.get('shops') or [])}
            failed = set()
            for cat in sorted({it['category'] for it in active}):
                try:
                    _refresh_shop(cat, prods_by_cat.get(cat))
                    refreshed += 1
                    _log_line(f'[商店] 刷新第 {r} 轮（分类 {cat}）', 'sub')
                except Exception as e:
                    failed.add(cat)
                    steps.append({'ok': False, 'category': cat,
                                  'skipped': f'刷新失败：{str(e)[:100]}'})
                    _log_line(f'[商店] 刷新分类 {cat} 失败：{str(e)[:80]}', 'err')
            active = [it for it in active if it['category'] not in failed]
            if not active:
                break

        st = shop_state()
        idx = {}
        for sh in st.get('shops') or []:
            for p in sh.get('products') or []:
                idx[p['shopExcelId']] = p

        for it in active:
            sid = it['shopExcelId']
            p = idx.get(sid)
            if not p:
                steps.append({'shopExcelId': sid, 'ok': False, 'round': r,
                              'skipped': '本轮商店没有这件商品'})
                continue
            left = (p.get('limit') or 0) - (p.get('bought') or 0)
            if p.get('soldOut') or left <= 0:
                steps.append({'shopExcelId': sid, 'ok': False, 'name': p.get('name'),
                              'round': r, 'skipped': '已售罄'})
                continue
            cnt = min(it['perRound'], left)
            try:
                res = _shop_buy_one(sid, p.get('goodsId'), cnt, p.get('isRefresh'))
                bought += 1
                steps.append({'shopExcelId': sid, 'ok': True, 'round': r, 'name': p.get('name'),
                              'count': cnt, 'rewards': res.get('rewards')})
                _log_line(f"[商店] 第 {r} 轮：{p.get('name')} ×{cnt}", 'ok')
            except Exception as e:
                steps.append({'shopExcelId': sid, 'ok': False, 'round': r, 'name': p.get('name'),
                              'error': str(e)[:120]})
                _log_line(f"[商店] 第 {r} 轮 {p.get('name')} 失败：{str(e)[:80]}", 'err')

    st2 = _load_ui_state()
    cfg2 = st2.get('shopAutobuy') or {}
    cfg2['lastRun'] = today
    st2['shopAutobuy'] = cfg2
    _write_ui_state(st2)
    _log_line(f'[商店] 自动购买完成：{bought} 件 / 刷新 {refreshed} 次（{today}）', 'sub')
    return {'ok': True, 'steps': steps, 'bought': bought, 'refreshed': refreshed, 'date': today}


# ---------- 神名精髓 Ⅰ（Eligma 商店·学生碎片） ----------
# 机制（社区公认 + 数据自洽）：每买 20 片涨 1 精髓，1 起、5 封顶。
# 商品目录不由服务端下发（shop/list 只给 ShopEligmaHistoryDBs 已购次数），
# 所以这里按「名册 + 已购次数」自建只读视图；购买走 shop/buyeligma(10004)。
ELIGMA_STEP = 20
ELIGMA_CAP = 5


def _eligma_price(bought: int) -> int:
    return min(ELIGMA_CAP, 1 + bought // ELIGMA_STEP)


@app.get('/api/shop/eligma')
def shop_eligma():
    _, pkt = call_session('/api/shop/list', 10002, business={'CategoryList': [1]})
    hist = {}
    for h in pkt.get('ShopEligmaHistoryDBs') or []:
        uid = h.get('CharacterUniqueId')
        if uid:
            hist[int(uid)] = int(h.get('PurchaseCount') or 0)
    roster = fetch_roster()
    rows = []
    for uid_s, info in roster.items():
        uid = int(uid_s)
        bought = hist.get(uid, 0)
        price = _eligma_price(bought)
        to_next = 0 if price >= ELIGMA_CAP else ELIGMA_STEP - (bought % ELIGMA_STEP)
        name = info.get('name') or char_names.get(uid_s, f'#{uid}')
        shard_icon = (shard_icons.get(name) or '').rsplit('/', 1)[-1]
        rows.append({
            'uid': uid,
            'name': name,
            'iconUrl': f'/static/icons/{shard_icon}.png' if shard_icon else '',
            'star': info.get('star'),
            'bought': bought,
            'price': price,
            'toNext': to_next,
            'capped': price >= ELIGMA_CAP,
        })
    rows.sort(key=lambda r: (-r['bought'], r['name']))
    return {'rows': rows, 'step': ELIGMA_STEP, 'cap': ELIGMA_CAP,
            'note': '每买 20 片涨 1 精髓，1 起 5 封顶；只能买已拥有角色的碎片'}


# ---------- 每日免费礼包 ----------
# 商店里的每日免费商品：10000 信用点 + 10 行动点，每日 4:00 重置。
# 实测 CountList 里还有 ShopCashId 1514（ResetDate 停在 2024 年，非每日），不要碰。
GIFT_CASH_ID = 900000


@app.get('/api/gift/state')
def gift_state():
    _, pkt = call_session('/api/billing/purchaselistbyyostar', 29002)
    items = pkt.get('CountList') or []
    item = next((x for x in items if x.get('ShopCashId') == GIFT_CASH_ID), None)
    return {
        'shopCashId': GIFT_CASH_ID,
        'available': item is not None,
        'purchased': bool(item and (item.get('PurchaseCount') or 0) > 0),
        'resetDate': (item or {}).get('ResetDate'),
    }


@app.post('/api/gift/claim')
def gift_claim():
    try:
        _, pkt = call_session('/api/billing/purchasefreeproduct', 29003,
                              business={'ShopCashId': GIFT_CASH_ID})
    except Exception as e:
        raise HTTPException(400, f'领取免费礼包失败：{e}')
    pr = pkt.get('ParcelResult') or {}
    _sync['ts'] = 0.0
    return {
        'ok': True,
        'rewards': _sum_parcels([pr.get('DisplaySequence')]),
        'product': pkt.get('PurchaseProduct'),
    }


# 一键清日常：把本模块作为宿主注入（runner 要调各业务函数），再挂上它的路由
daily.init(sys.modules[__name__])
app.include_router(daily.router)
