"""webui/momotalk.py — MomoTalk 好感剧情收割。

协议与实测结论见 `docs/模块/MomoTalk.md`（2026-10-28 晴奈实弹）：

  - 服务端**不校验读取进度**，没读到过的剧情组也能直接登记完成
  - 每条剧情 = `scenario/grouphistoryupdate(ScenarioSriptGroupId, 4)` + `momotalk/favorschedule(Id)`
  - `scenario/skip` 不需要；`momotalk/read` 可选（幂等，只影响客户端已读状态）
  - 重复领奖报 `400 Alreday Attend Favor Schedule`，幂等，可安全重跑

数据来源：`_srv.login_sync()`（已带 SyncProtocols 33000/19000/20000）+ 本地表 + 名册好感。
业务函数由宿主 `webui/server.py` 注入，避免循环依赖。
"""
import datetime
import json
import logging
import os
import threading

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger('autoba')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP_DIR)
TABLES = os.path.join(ROOT, 'tables', 'full', 'ExcelDB')

SCENARIO_TYPE_MOMOTALK = 4

_srv = None
_tab = {'sched_by_char': None, 'group_by_sched': None, 'msg_by_group': None,
        'first_group': None}
# 领奖与清红点共用一把锁：两个操作都发写请求，必须互斥，否则会话 rid 会互相打断
_op_lock = threading.Lock()

# 清红点任务状态（长任务，后台线程 + 前端轮询）
_read_task = {
    'running': False, 'startedAt': None, 'finishedAt': None,
    'charDone': 0, 'charTotal': 0, 'readCount': 0, 'claimCount': 0, 'stone': 0,
    'current': None, 'error': None, 'stopRequested': False,
}


def init(server_module):
    global _srv
    _srv = server_module


# ---------- 纯函数（可直接单测） ----------

def classify_char(schedules: list, done_ids, rank: int, group_by_sched: dict) -> dict:
    """把一个角色的剧情定义分成「可领」与「卡好感」两类。

    schedules: AcademyFavorScheduleExcel 里该角色的行
    done_ids:  服务端 FavorScheduleRecords 给出的已完成 Id 集合
    rank:      当前好感等级
    """
    claimable, locked = [], []
    for s in schedules:
        if s['Id'] in done_ids:
            continue
        item = {
            'id': s['Id'],
            'favorRank': s['FavorRank'],
            'scriptGroup': s['ScenarioSriptGroupId'],
            'group': group_by_sched.get(s['Id'], 0),
            'stone': _stones(s),
        }
        (locked if s['FavorRank'] > rank else claimable).append(item)
    claimable.sort(key=lambda x: x['id'])
    locked.sort(key=lambda x: x['id'])
    return {'claimable': claimable, 'locked': locked}


def _stones(s) -> int:
    """奖励里的免费青辉石（Currency 3 = GemBonus）。"""
    return sum(a for t, i, a in zip(s['RewardParcelType'], s['RewardParcelId'], s['RewardAmount'])
               if t == 'Currency' and i == 3)


def summarize(rows: list) -> dict:
    """汇总：条数与青辉石。rows 为 build_state 的每角色条目。"""
    claim = sum(len(r['claimable']) for r in rows)
    locked = sum(len(r['locked']) for r in rows)
    return {
        'claimCount': claim,
        'lockedCount': locked,
        'claimStone': sum(i['stone'] for r in rows for i in r['claimable']),
        'lockedStone': sum(i['stone'] for r in rows for i in r['locked']),
        'chars': sum(1 for r in rows if r['claimable'] or r['locked']),
        'totalChars': len(rows),
        'doneChars': sum(1 for r in rows if not r['claimable'] and not r['locked']),
    }


# ---------- 静态表 ----------

def _load(name):
    with open(os.path.join(TABLES, name), encoding='utf-8') as f:
        return json.load(f)


def _tables():
    if _tab['sched_by_char'] is None:
        sched = _load('AcademyFavorScheduleExcel.json')
        msgs = _load('AcademyMessangerExcel.json')
        by_char = {}
        for r in sched:
            by_char.setdefault(str(r['CharacterId']), []).append(r)
        # 一条剧情可能由多个消息组触发，取最小编号（表里是 1:1，这里只做兜底）
        gmap, mg, first = {}, {}, {}
        for m in msgs:
            g = m['MessageGroupId']
            mg.setdefault(g, []).append(m)
            sid = m['FavorScheduleId']
            if sid and (sid not in gmap or g < gmap[sid]):
                gmap[sid] = g
            cid = str(m['CharacterId'] or '')
            if cid and cid != '0' and (cid not in first or g < first[cid]):
                first[cid] = g
        _tab.update(sched_by_char=by_char, group_by_sched=gmap,
                    msg_by_group=mg, first_group=first)
    return _tab['sched_by_char'], _tab['group_by_sched']


# ---------- 状态 ----------

def build_state() -> dict:
    """全账号 MomoTalk 进度。

    **数据源是名册 + 剧情表，不是服务端会话列表**：`MomoTalkOutLineDBs` 只包含
    "有过互动的角色"（测试号 174 个名册角色里只有 60 个），漏掉的角色照样能领奖
    （2026-10-28 实测：无会话记录的艾米 ghu + favor 直接成功）。
    会话记录只用来标注 started，以及带上 LatestMessageGroupId。
    """
    pkt = _srv.login_sync()
    mo = pkt.get('MomoTalkOutLineResponse') or {}
    outlines = {str(o['CharacterId']): o for o in (mo.get('MomoTalkOutLineDBs') or [])}
    done_map = mo.get('FavorScheduleRecords') or {}
    roster = _srv.fetch_roster()
    sched_by_char, group_by_sched = _tables()

    rows = []
    for cid, info in roster.items():
        schedules = sched_by_char.get(cid) or []
        if not schedules:
            continue
        rank = info.get('rank') or 0
        done = set(done_map.get(cid) or [])
        parts = classify_char(schedules, done, rank, group_by_sched)
        ol = outlines.get(cid) or {}
        rows.append({
            'charId': cid,
            'name': info.get('name') or _srv.char_names.get(cid, f'#{cid}'),
            'dbId': info.get('serverId') or ol.get('CharacterDBId'),   # ServerId 即 CharacterDBId
            'rank': rank,
            'latest': ol.get('LatestMessageGroupId') or 0,
            'started': bool(ol),
            'total': len(schedules),
            'done': len(schedules) - len(parts['claimable']) - len(parts['locked']),
            'doneIds': sorted(done),
            **parts,
        })
    rows.sort(key=lambda r: (-len(r['claimable']), -len(r['locked']), r['name']))
    return {'rows': rows, 'summary': summarize(rows)}


# ---------- 执行 ----------

def _reward_name(p: dict) -> str:
    key = p.get('Key') or {}
    t, i = key.get('Type'), key.get('Id')
    if t == 2:
        return _srv.currency_names.get(str(i), f'Currency {i}')
    if t == 8:                      # 神名文字，Id 是 CharacterId
        return (_srv.char_names.get(str(i)) or f'#{i}') + ' 神名文字'
    if t == 4:
        return _srv.item_names.get(str(i), f'Item {i}')
    return f'Type{t}:{i}'


def claim(char_ids=None, include_locked: bool = False) -> dict:
    """按角色领取未完成的剧情奖励。char_ids 为空表示全部。"""
    if not _op_lock.acquire(blocking=False):
        return {'ok': False, 'error': '有任务正在执行（领取或清红点），请稍后再试'}
    try:
        st = build_state()
        want = {str(c) for c in char_ids} if char_ids else None
        steps = []
        got = stone = 0
        for row in st['rows']:
            if want and row['charId'] not in want:
                continue
            items = list(row['claimable']) + (list(row['locked']) if include_locked else [])
            for it in items:
                try:
                    _srv.call_session('/api/scenario/grouphistoryupdate', 19002,
                                      business={'ScenarioGroupUniqueId': it['scriptGroup'],
                                                'ScenarioType': SCENARIO_TYPE_MOMOTALK})
                    _, pkt = _srv.call_session('/api/momotalk/favorschedule', 33004,
                                               business={'ScheduleId': it['id']})
                    seq = (pkt.get('ParcelResultDB') or {}).get('DisplaySequence') or []
                    rewards = [{'name': _reward_name(p), 'amount': p.get('Amount')} for p in seq]
                    # 按 Key 判青辉石（Type 2=Currency, Id 3=GemBonus），不依赖名字映射
                    stone += sum(p.get('Amount') or 0 for p in seq
                                 if (p.get('Key') or {}).get('Type') == 2
                                 and (p.get('Key') or {}).get('Id') == 3)
                    got += 1
                    steps.append({'ok': True, 'char': row['name'], 'id': it['id'], 'rewards': rewards})
                except Exception as e:
                    msg = str(e)
                    # 已领过 = 幂等成功，不算失败
                    if 'Alreday Attend' in msg or 'Already Attend' in msg:
                        steps.append({'ok': True, 'char': row['name'], 'id': it['id'],
                                      'rewards': [], 'note': '此前已领'})
                        continue
                    logger.exception('[MomoTalk] %s 剧情 %s 领取失败', row['name'], it['id'])
                    steps.append({'ok': False, 'char': row['name'], 'id': it['id'], 'error': msg[:160]})
        _srv._sync['ts'] = 0.0          # 完成后让下次 loginsync 重新拉完成清单
        return {'ok': True, 'steps': steps, 'claimed': got, 'stone': stone}
    finally:
        _op_lock.release()


# ---------- 清红点：把消息组推到链尾（遇剧情组顺手领） ----------

def _char_last_group():
    """每个角色的链尾组（从首组沿 NextGroupId 走到头）。"""
    if _tab.get('last_group') is None:
        _tables()
        mg, first = _tab['msg_by_group'], _tab['first_group']
        last = {}
        for cid, g0 in first.items():
            g, seen, tail = g0, set(), g0
            while g and g not in seen:
                seen.add(g)
                tail = g
                rows = mg.get(g) or []
                g = rows[0]['NextGroupId'] if rows else 0
            last[cid] = tail
        _tab['last_group'] = last
    return _tab['last_group']


def _read_one_char(row, done_ids: set) -> dict:
    """把一个角色从 latest 推到链尾；碰到未完成的剧情组就登记 + 领奖。"""
    _tables()
    db = row['dbId']
    if not db:
        return {'reads': 0, 'claims': 0, 'stone': 0, 'skip': '无 CharacterDBId'}
    mg = _tab['msg_by_group']
    g = row['latest'] or _tab['first_group'].get(row['charId'], 0)
    if not g:
        return {'reads': 0, 'claims': 0, 'stone': 0, 'skip': '表里没有该角色的消息'}
    reads = claims = stone = 0
    seen = set()
    while g and g not in seen and reads < 300:
        seen.add(g)
        rows = mg.get(g) or []
        if not rows:
            break
        ans = [r for r in rows if r['MessageCondition'] == 'Answer']
        # Answer 组必须带有效 Id；传 null 会让这次推进整段作废（2026-10-28 实测）
        chosen = ans[0]['Id'] if ans else None
        _srv.call_session('/api/momotalk/read', 33002,
                          business={'CharacterDBId': db, 'LastReadMessageGroupId': g,
                                    'ChosenMessageId': chosen})
        reads += 1
        fs = next((r['FavorScheduleId'] for r in rows if r['FavorScheduleId']), 0)
        if fs and fs not in done_ids:
            sched = next((x for x in _tab['sched_by_char'].get(row['charId'], [])
                          if x['Id'] == fs), None)
            if sched:
                try:
                    _srv.call_session('/api/scenario/grouphistoryupdate', 19002,
                                      business={'ScenarioGroupUniqueId': sched['ScenarioSriptGroupId'],
                                                'ScenarioType': SCENARIO_TYPE_MOMOTALK})
                    _, pkt = _srv.call_session('/api/momotalk/favorschedule', 33004,
                                               business={'ScheduleId': fs})
                    seq = (pkt.get('ParcelResultDB') or {}).get('DisplaySequence') or []
                    stone += sum(p.get('Amount') or 0 for p in seq
                                 if (p.get('Key') or {}).get('Type') == 2
                                 and (p.get('Key') or {}).get('Id') == 3)
                    claims += 1
                except Exception as e:
                    if 'Alreday Attend' not in str(e):
                        logger.warning('[MomoTalk] %s 剧情 %s 领取失败：%s', row['name'], fs, e)
        nxt = rows[0]['NextGroupId']
        if not nxt:
            break
        g = nxt
    return {'reads': reads, 'claims': claims, 'stone': stone}


def _read_worker(char_ids):
    if not _op_lock.acquire(blocking=False):
        _read_task.update(running=False, error='有任务正在执行（领取或清红点）')
        return
    _read_task.update(running=True, error=None, stopRequested=False, charDone=0,
                      readCount=0, claimCount=0, stone=0,
                      startedAt=_now(), finishedAt=None)
    try:
        st = build_state()
        want = {str(c) for c in char_ids} if char_ids else None
        last = _char_last_group()
        targets = [r for r in st['rows']
                   if (not want or r['charId'] in want)
                   and r['latest'] < last.get(r['charId'], 0)]
        _read_task['charTotal'] = len(targets)
        for row in targets:
            if _read_task['stopRequested']:
                break
            _read_task['current'] = row['name']
            try:
                res = _read_one_char(row, set(row.get('doneIds') or []))
                _read_task['readCount'] += res['reads']
                _read_task['claimCount'] += res['claims']
                _read_task['stone'] += res['stone']
            except Exception as e:
                logger.exception('[MomoTalk] 清红点 %s 失败', row['name'])
                _read_task['error'] = f"{row['name']}: {str(e)[:120]}"
            _read_task['charDone'] += 1
        _srv._sync['ts'] = 0.0
    except Exception as e:
        logger.exception('[MomoTalk] 清红点任务失败')
        _read_task['error'] = str(e)[:200]
    finally:
        _read_task.update(running=False, current=None, finishedAt=_now(),
                          stopRequested=False)
        _op_lock.release()


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


# ---------- 一键清 runner ----------

def run_claim(log, dry):
    st = build_state()
    sm = st['summary']
    n = sm['claimCount']
    if not n:
        return 'skip', '没有可领取的剧情'
    if dry:
        log.append(f"将领取 {sm['chars']}/{sm['totalChars']} 个角色共 {n} 条剧情（青辉石 {sm['claimStone']}）")
        for r in st['rows'][:6]:
            if r['claimable']:
                log.append(f"  {r['name']}：{len(r['claimable'])} 条 / {sum(i['stone'] for i in r['claimable'])} 石")
        return 'ok', f"演练：{n} 条"
    j = claim()
    for s in j['steps']:
        if s.get('ok'):
            rw = '、'.join(f"{x['name']}×{x['amount']}" for x in s.get('rewards') or []) or s.get('note') or '已领'
            log.append(f"[MomoTalk] {s['char']} {s['id']} → {rw}")
        else:
            log.append(f"[MomoTalk] {s['char']} {s['id']} 失败：{s.get('error')}")
    bad = [s for s in j['steps'] if not s.get('ok')]
    if bad and len(bad) == len(j['steps']):
        raise RuntimeError(f'全部 {len(bad)} 条领取失败：{bad[0].get("error")}')
    return 'ok', f"{j['claimed']} 条 / {j['stone']} 石" + (f"（失败 {len(bad)}）" if bad else '')


# ---------- 接口 ----------

router = APIRouter()


class ClaimReq(BaseModel):
    charIds: list[str] = []
    includeLocked: bool = False
    dry: bool = False


@router.get('/api/momotalk/state')
def momotalk_state():
    st = build_state()
    for r in st['rows']:
        r.pop('doneIds', None)      # 只给进程内的清红点任务用，不传给前端
    return st


@router.post('/api/momotalk/claim')
def momotalk_claim(req: ClaimReq):
    if req.dry:
        st = build_state()
        return {'ok': True, 'dry': True, 'summary': st['summary']}
    return claim(char_ids=req.charIds, include_locked=req.includeLocked)


class ReadReq(BaseModel):
    charIds: list[str] = []


@router.post('/api/momotalk/readall')
def momotalk_readall(req: ReadReq):
    if _read_task['running']:
        return {'ok': False, 'error': '清红点正在执行中'}
    threading.Thread(target=_read_worker, args=(req.charIds,), daemon=True).start()
    return {'ok': True}


@router.get('/api/momotalk/readstatus')
def momotalk_readstatus():
    return dict(_read_task)


@router.post('/api/momotalk/readstop')
def momotalk_readstop():
    if not _read_task['running']:
        return {'ok': True, 'running': False}
    _read_task['stopRequested'] = True
    return {'ok': True, 'stopRequested': True}
