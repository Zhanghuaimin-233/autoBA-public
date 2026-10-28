"""webui/daily.py — 一键清日常的后端执行器。

设计：docs/设计/一键清日常后端化.md

职责：
  - 任务状态对象 `_daily_task` + 串行 worker + 四档状态（ok/skip/fail/abort）
  - 三个接口：POST /api/daily/run、GET /api/daily/status、POST /api/daily/stop
  - dry 演练：只读状态、算计划，不发写请求
  - 状态落盘 `webui/daily_state.json`，按**游戏日**（本地 04:00 为界，BA 国服日常刷新时间）
    判断是否提示「上次被中断」——跨周期的旧状态只在操作日志里留痕，不干扰新一天

业务函数（各模块的 build/执行入口）由宿主 `webui/server.py` 注入，避免循环依赖。
"""
import datetime
import json
import logging
import os
import threading
import time

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger('autoba')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(APP_DIR, 'daily_state.json')

DAILY_LABELS = {
    'plan': '学园日程', 'cafe': '咖啡厅', 'bounty': '悬赏通缉', 'scrim': '学院交流会',
    'clan': '社交小组', 'arena': '战术对抗赛', 'gift': '免费礼包',
    'mail': '邮箱', 'mission': '任务奖励', 'shop': '商店', 'momotalk': 'MomoTalk',
}
DAILY_DEFAULT_ORDER = ['arena', 'plan', 'cafe', 'bounty', 'scrim',
                       'clan', 'gift', 'mail', 'mission', 'shop', 'momotalk']
DAILY_STALE_S = 600          # 超过 10 分钟仍在 running，视为僵死

# 宿主模块（webui/server.py）在启动时注入，runner 通过它调用业务函数
_srv = None


def init(server_module):
    global _srv
    _srv = server_module


# ---------- 纯函数（可直接单测） ----------

def game_day(ts=None) -> str:
    """游戏日：以本地 04:00 为界。

    蓝档案国服服务器重置时间为北京时间凌晨 04:00（官网公告与 wiki 一致），
    所以 03:59 仍算前一天。
    """
    ts = ts or datetime.datetime.now()
    if ts.hour < 4:
        ts = ts - datetime.timedelta(days=1)
    return ts.strftime('%Y-%m-%d')


def looks_like_session_dead(msg: str) -> bool:
    """会话彻底失效的特征（与 call_session 里的重登条件保持一致）。"""
    return any(k in msg for k in ('33004', '33005', '过期', 'time over'))


def fit_counts(counts: dict, balance, maps: list) -> dict:
    """按关卡顺序贪心分配券（前端 fitCounts 的后端版）。

    balance 为 None（券数未知）时原样返回配置。
    """
    if balance is None:
        return dict(counts)
    left = max(0, int(balance))
    out = {}
    for m in maps or []:
        want = max(0, int(counts.get(m['key'], 0) or 0))
        give = min(want, left)
        out[m['key']] = give
        left -= give
    return out


# ---------- 状态对象与落盘 ----------

_daily_task = {
    'running': False, 'dry': False, 'startedAt': None, 'finishedAt': None,
    'current': None, 'stopRequested': False, 'order': [], 'steps': [],
    '_startedTs': 0.0,
}

_STEP_KEYS = ('key', 'label', 'status', 'reason', 'ms')


def _save_state(status: str):
    """任务快照写盘（不含 log，明细已在操作日志 jsonl）。"""
    try:
        data = {
            'gameDay': game_day(),
            'startedAt': _daily_task['startedAt'],
            'finishedAt': _daily_task['finishedAt'],
            'status': status,                 # running / done
            'dry': _daily_task['dry'],
            'order': _daily_task['order'],
            'steps': [{k: s.get(k) for k in _STEP_KEYS} for s in _daily_task['steps']],
        }
        tmp = STATE_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STATE_FILE)
    except Exception:
        logger.warning('一键清状态落盘失败', exc_info=True)


def load_prev():
    """上次任务快照。跨游戏日的旧状态就地清除并标 stalePeriod。

    玩家的日常已经翻篇，昨天的中断不该在今天弹提示——日志里还留着记录。
    """
    try:
        with open(STATE_FILE, encoding='utf-8') as f:
            st = json.load(f)
    except Exception:
        return None
    if st.get('gameDay') != game_day():
        st['stalePeriod'] = True
        try:
            os.remove(STATE_FILE)
            logger.info('一键清：清理跨游戏日的旧状态（%s）', st.get('gameDay'))
        except Exception:
            pass
        return st
    st['stalePeriod'] = False
    return st


# ---------- 状态查询 ----------

def _daily_pref(key, default=None):
    """读 ui_state 里的配置（一键清没有前端上下文，名单/票数都从这里取）。"""
    st = _srv._load_ui_state()
    return st[key] if key in st else default


def _daily_is_stale() -> bool:
    return bool(_daily_task['running'] and _daily_task['_startedTs']
                and time.time() - _daily_task['_startedTs'] > DAILY_STALE_S)


def status_snapshot() -> dict:
    out = {k: v for k, v in _daily_task.items() if k != '_startedTs'}
    out['stale'] = _daily_is_stale()
    out['gameDay'] = game_day()
    if not out['running']:
        out['prev'] = load_prev()
    return out


# ---------- 10 个模块 runner：统一签名 (log, dry) -> (status, reason) ----------

def _run_plan(log, dry):
    students = _daily_pref('schStudents', []) or []
    built = _srv.build_plan(students)
    plan_items = built.get('plan') or []
    if not plan_items:
        return 'skip', '方案为空（没有可清的 Zone）'
    if dry:
        tk = built.get('tickets')
        tk_n = tk.get('estimated') if isinstance(tk, dict) else tk
        log.append(f'将执行 {len(plan_items)} 个 Zone（券 {tk_n}）')
        for it in plan_items[:12]:
            names = '、'.join(t['name'] for t in it.get('targets') or [])
            log.append(f"  Zone {it['zone']} {it['locationName']} → {names}")
        return 'ok', f'演练：{len(plan_items)} 个 Zone'
    j = _srv.schedule_clear(_srv.PlanReq(students=students))
    for s in j.get('steps') or []:
        ch = '、'.join(f"{c['name']} R{c['rank']}" for c in s.get('characters') or []) or '无入账'
        log.append(f"[{s['roundLabel']}] Zone {s['zone']} {s['locationName']} → {ch}；券余 {s['tickets']}")
    if j.get('stopKind') == 'error':
        raise RuntimeError(j.get('stopped') or '日程清票中断')
    return ('ok' if j.get('steps') else 'skip'), (j.get('stopped') or f"{len(j.get('steps') or [])} 次")


def _run_cafe(log, dry):
    students = _daily_pref('cafeStudents', []) or []
    if dry:
        built = _srv.build_cafe_plan(students)
        log.append(f"将领取产出 + 摸头 + 按名单邀请 {len(built.get('plan') or [])} 人")
        if not students:
            log.append('邀请名单为空（在页面上选过学生后会自动同步到后端）')
        return 'ok', '演练'
    j = _srv.cafe_run(_srv.CafePlanReq(students=students))
    for s in j.get('steps') or []:
        t = s.get('type')
        if t == 'claim':
            log.append('[领取] 咖啡厅产出 ' + ('成功' if s.get('ok', True) else f"失败：{s.get('error')}"))
        elif t == 'pet':
            log.append(f"[摸头] {s.get('name')} " + ('✓' if s.get('ok') else f"✗ {s.get('error')}"))
        else:
            log.append(f"[邀请] {s.get('name')} → {s.get('cafeId')} 号厅 " + ('✓' if s.get('ok') else '✗'))
    if j.get('stopKind') == 'error':
        raise RuntimeError(j.get('stopped') or '咖啡厅执行中断')
    reason = j.get('stopped')
    if not students:
        reason = f'{reason}；' if reason else ''
        reason += '未邀请（名单为空）'
    return 'ok', reason


def _run_bounty(log, dry):
    cfg_counts = _daily_pref('bountyCounts', {}) or {}
    force = bool(_daily_pref('bountyForce', False))
    st = _srv.build_bounty_state(force=True)
    plan_counts = fit_counts(cfg_counts, st.get('tickets'), st.get('maps'))
    total = sum(plan_counts.values())
    if total <= 0:
        return 'skip', '配置为 0'
    if dry:
        detail = '、'.join(f'{k}×{v}' for k, v in plan_counts.items() if v)
        log.append(f'将用 {total} 张券扫荡：{detail}')
        return 'ok', f'演练：{total} 张'
    j = _srv.bounty_sweep(_srv.BountySweepReq(counts=plan_counts, force=force))
    for s in j.get('steps') or []:
        if s.get('ok'):
            rw = '、'.join(f"{r['name']}×{r['amount']}" for r in s.get('rewards') or []) or '无掉落'
            log.append(f"[悬赏] {s['map']} {s['stage']} ×{s['count']} → 券余 {s['tickets']}；{rw}")
        else:
            log.append(f"[悬赏] {s['map']} 失败：{s.get('error')}")
    if j.get('stopKind') == 'error':
        raise RuntimeError(j.get('stopped') or '悬赏扫荡失败')
    return 'ok', (j.get('stopped') or f'{total} 张')


def _run_scrim(log, dry):
    cfg_counts = _daily_pref('scrimCounts', {}) or {}
    force = bool(_daily_pref('scrimForce', False))
    st = _srv.build_scrim_state(force=True)
    plan_counts = fit_counts(cfg_counts, st.get('tickets'), st.get('maps'))
    total = sum(plan_counts.values())
    if total <= 0:
        return 'skip', '配置为 0'
    if dry:
        detail = '、'.join(f'{k}×{v}' for k, v in plan_counts.items() if v)
        log.append(f'将用 {total} 张券扫荡：{detail}')
        return 'ok', f'演练：{total} 张'
    j = _srv.scrimmage_sweep(_srv.BountySweepReq(counts=plan_counts, force=force))
    for s in j.get('steps') or []:
        if s.get('ok'):
            log.append(f"[交流会] {s['map']} {s['stage']} ×{s['count']} → 券余 {s['tickets']}")
        else:
            log.append(f"[交流会] {s['map']} 失败：{s.get('error')}")
    if j.get('stopKind') == 'error':
        raise RuntimeError(j.get('stopped') or '交流会扫荡失败')
    return 'ok', (j.get('stopped') or f'{total} 张')


def _run_clan(log, dry):
    if dry:
        log.append('将检查并签到（进大厅即签到）')
        return 'ok', '演练'
    j = _srv.clan_checkin()
    days = ((j.get('me') or {}).get('attendance'))
    if j.get('checkedToday'):
        log.append(f"[签到] 已签到，出勤 {days} 天")
        return 'skip', '今日已签到'
    log.append(f"[签到] 完成，出勤 {days} 天")
    return 'ok', None


def _run_arena(log, dry):
    if _srv._arena_clear['running']:
        return 'skip', '上一轮清票仍在进行'
    if dry:
        log.append('将后台清 5 场（30s/场，等待期间继续跑后续模块）')
        return 'ok', '演练'
    j = _srv.arena_clear(_srv.ArenaClearReq(maxBattles=5))
    if not j.get('ok'):
        return 'skip', (j.get('error') or '清票未能启动')
    log.append(f"[竞技场] 后台清票已启动（券 {j.get('tickets')}），30s/场")
    return 'ok', '后台清票中'


def _run_gift(log, dry):
    g = _srv.gift_state()
    if not g.get('available'):
        return 'skip', '商店无此商品'
    if g.get('purchased'):
        return 'skip', '今日已领取'
    if dry:
        log.append('将领取免费礼包')
        return 'ok', '演练'
    j = _srv.gift_claim()
    rw = '、'.join(f"{r['name']}×{r['amount']}" for r in j.get('rewards') or []) or '无奖励'
    log.append(f'[礼包] 领取成功：{rw}')
    return 'ok', None


def _run_mail(log, dry):
    st = _srv.mail_state()
    n = st.get('unread') or 0
    if dry:
        log.append(f'将领取邮箱（待领 {n} 封）' if n else '邮箱没有待领邮件')
        return ('ok' if n else 'skip'), ('演练' if n else '没有可领取的邮件')
    j = _srv.mail_claim()
    n = j.get('count') or 0
    if not n:
        return 'skip', '没有可领取的邮件'
    rw = '、'.join(f"{r['name']}×{r['amount']}" for r in j.get('rewards') or []) or '已领取'
    log.append(f'[邮箱] 领取 {n} 封：{rw}')
    return 'ok', None


def _run_mission(log, dry):
    if dry:
        log.append('将领取任务奖励（日常 / 周常 / 成就）')
        return 'ok', '演练'
    j = _srv.mission_claim(_srv.MissionClaimReq(categories=[1, 2, 3]))
    got = 0
    for s in j.get('steps') or []:
        cat = s.get('category')
        if s.get('skipped'):
            log.append(f'[任务] 类别 {cat}：{s["skipped"]}')
        elif s.get('ok'):
            got += 1
            rw = '、'.join(f"{r['name']}×{r['amount']}" for r in s.get('rewards') or []) or '已领取'
            log.append(f'[任务] 类别 {cat}：{rw}')
        else:
            log.append(f'[任务] 类别 {cat} 失败：{s.get("error")}')
    return ('ok' if got else 'skip'), (None if got else '无可领取')


def _run_shop(log, dry):
    cfg = _srv._autobuy_cfg()
    if not cfg['enabled']:
        return 'skip', '自动购买未启用'
    if not cfg['items']:
        return 'skip', '没有配置商品'
    if dry:
        log.append(f"将按 {len(cfg['items'])} 件商品执行自动购买（含刷新轮）")
        return 'ok', '演练'
    j = _srv._autobuy_run(False)
    if j.get('skipped'):
        return 'skip', str(j.get('skipped'))
    for s in j.get('steps') or []:
        if s.get('ok'):
            log.append(f"[商店] 第 {s.get('round')} 轮：{s.get('name')} ×{s.get('count')}")
        elif s.get('error'):
            log.append(f"[商店] {s.get('name') or s.get('shopExcelId')} 失败：{s['error']}")
    return 'ok', f"{j.get('bought', 0)} 件 / 刷新 {j.get('refreshed', 0)} 次"


def _run_momotalk(log, dry):
    """MomoTalk 剧情收割：逻辑在 webui/momotalk.py，这里只做转交。"""
    return _srv.momotalk.run_claim(log, dry)


DAILY_RUNNERS = {
    'plan': _run_plan, 'cafe': _run_cafe, 'bounty': _run_bounty, 'scrim': _run_scrim,
    'clan': _run_clan, 'arena': _run_arena, 'gift': _run_gift, 'mail': _run_mail,
    'mission': _run_mission, 'shop': _run_shop, 'momotalk': _run_momotalk,
}

_CLS_BY_STATUS = {'ok': 'ok', 'skip': 'sub', 'fail': 'err', 'abort': 'err'}


class _DailyAbort(RuntimeError):
    """致命错误：整个一键清中止（会话彻底失效等）。"""


def _worker(order):
    fails = 0
    _save_state('running')
    try:
        for step in _daily_task['steps']:
            if _daily_task['stopRequested']:
                step['status'], step['reason'] = 'skip', '用户停止'
                _save_state('running')
                continue
            step['status'] = 'running'
            _daily_task['current'] = step['key']
            t0 = time.time()
            try:
                status, reason = DAILY_RUNNERS[step['key']](step['log'], _daily_task['dry'])
                step['status'], step['reason'] = status, reason
                fails = fails + 1 if status == 'fail' else 0
            except _DailyAbort as e:
                step['status'], step['reason'] = 'abort', str(e)[:200]
                for s in _daily_task['steps']:
                    if s['status'] == 'pending':
                        s['status'], s['reason'] = 'skip', '任务已中止'
                break
            except Exception as e:
                logger.exception('[一键清] %s 失败', step['key'])
                step['status'], step['reason'] = 'fail', str(e)[:200]
                fails += 1
                if fails >= 2 and looks_like_session_dead(str(e)):
                    raise _DailyAbort(f'连续失败且会话失效：{str(e)[:120]}')
            finally:
                step['ms'] = int((time.time() - t0) * 1000)
                for line in step['log']:
                    _srv._log_line(line, _CLS_BY_STATUS.get(step['status'], 'sub'))
                _save_state('running')
    finally:
        _daily_task.update(
            running=False, current=None, stopRequested=False, _startedTs=0.0,
            finishedAt=datetime.datetime.now().astimezone().isoformat(timespec='seconds'))
        _save_state('done')
        steps = _daily_task['steps']
        bad = [DAILY_LABELS.get(s['key'], s['key']) for s in steps if s['status'] in ('fail', 'abort')]
        skipped = [DAILY_LABELS.get(s['key'], s['key']) for s in steps if s['status'] == 'skip']
        tag = '（演练）' if _daily_task['dry'] else ''
        if bad:
            tail, cls = f"结束{tag}，失败：{'、'.join(bad)}", 'err'
        elif skipped:
            tail, cls = f"完成{tag}，跳过：{'、'.join(skipped)}", 'ok'
        else:
            tail, cls = f"全部完成{'（演练，未执行）' if _daily_task['dry'] else ''}", 'ok'
        _srv._log_line(f'[一键清] {tail}', cls)


# ---------- 接口 ----------

router = APIRouter()


class DailyRunReq(BaseModel):
    dry: bool = False
    order: list[str] = []
    only: list[str] = []


@router.post('/api/daily/run')
def daily_run(req: DailyRunReq):
    if _daily_task['running'] and not _daily_is_stale():
        return {'ok': False, 'skipped': True, 'error': '一键清正在执行中'}
    order = req.only or req.order or (_daily_pref('moduleOrder') or DAILY_DEFAULT_ORDER)
    order = [k for k in order if k in DAILY_RUNNERS]
    if not req.only:
        # 老配置里没有的模块（后续新增的）补到末尾，否则永远轮不到它执行
        order += [k for k in DAILY_DEFAULT_ORDER if k not in order]
    if not order:
        return {'ok': False, 'error': '没有可执行的模块'}
    started = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    _daily_task.update(
        running=True, dry=bool(req.dry), startedAt=started, finishedAt=None,
        current=None, stopRequested=False, order=order, _startedTs=time.time(),
        steps=[{'key': k, 'label': DAILY_LABELS.get(k, k), 'status': 'pending',
                'reason': None, 'ms': None, 'log': []} for k in order])
    _srv._log_line(f"[一键清] 开始{'（演练）' if req.dry else ''}："
                   f"{' → '.join(DAILY_LABELS.get(k, k) for k in order)}")
    threading.Thread(target=_worker, args=(order,), daemon=True).start()
    return {'ok': True, 'startedAt': started, 'order': order, 'dry': bool(req.dry)}


@router.get('/api/daily/status')
def daily_status():
    return status_snapshot()


@router.post('/api/daily/stop')
def daily_stop():
    if not _daily_task['running']:
        return {'ok': True, 'running': False}
    _daily_task['stopRequested'] = True
    return {'ok': True, 'stopRequested': True}
