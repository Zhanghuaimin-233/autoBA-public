"""从双向明文抓包自动生成接口文档。
产出：docs/API.md（人读）+ api_doc.json（机器读，供 apiclient 用）
跑法：python gen_api_doc.py
"""
import glob
import io
import json
import os
import time
from collections import defaultdict

HERE = r'.'
CAP = r'capture/ba'


# ===== 脱敏：再生文档前把账号真值统一替换为占位 =====
# 真值清单从本地凭据文件 yostar_credentials.json 读取（不入库，见 .gitignore），
# 本文件自身不硬编码任何账号数据。
def _load_secret_map():
    try:
        c = json.load(open(f'{HERE}/yostar_credentials.json', encoding='utf-8'))
    except Exception:
        return []
    vals = []
    for k, v in c.items():
        if k == 'secrets' and isinstance(v, list):
            vals += [str(x) for x in v if len(str(x)) >= 6]
        elif isinstance(v, (str, int)) and len(str(v)) >= 6:
            vals.append(str(v))
    vals.sort(key=len, reverse=True)  # 长串先替换，避免子串误伤
    return [(v, '<REDACTED>') for v in vals]


_SEC_MAP = _load_secret_map()


def _redact(s):
    for old, sub in _SEC_MAP:
        s = s.replace(old, sub)
    return s

# 中文映射：官方枚举语义 + 国服社区叫法。标 (？) 的为待游戏内确认。
CN_NAMES = {
    '/api/account/auth': '登录认证（Token 换会话）',
    '/api/account/loginsync': '登录同步（批量拉取变更）',
    '/api/account/gettutorial': '教程完成状态查询',
    '/api/account/settutorial': '教程完成状态上报',
    '/api/academy/getinfo': '学园日程信息',
    '/api/academy/attendschedule': '学园日程·执行（地点+100经验，掉对应学校技术笔记）',
    '/api/arena/enterlobby': '战术对抗赛·进入大厅',
    '/api/arena/opponentlist': '战术对抗赛·对手列表',
    '/api/arena/enterbattle': '战术对抗赛·开始战斗',
    '/api/arena/dailyreward': '战术对抗赛·每日奖励领取',
    '/api/arena/cumulativetimereward': '战术对抗赛·累计时数奖励',
    '/api/arena/syncechelonsettingtime': '战术对抗赛·同步防守编队',
    '/api/attendance/reward': '出勤奖励（签到）',
    '/api/battlepass/getinfo': '通行证·信息',
    '/api/battlepass/check': '通行证·任务进度检查',
    '/api/battlepass/missionlist': '通行证·任务列表',
    '/api/battlepass/receivereward': '通行证·领取等级奖励',
    '/api/battlepass/missionmultiplereward': '通行证·批量领取任务奖励',
    '/api/billing/purchaselistbyyostar': '商城·商品列表查询',
    '/api/billing/purchasefreeproduct': '商城·免费商品领取',
    '/api/cafe/ack': '咖啡厅·状态确认',
    '/api/cafe/interact': '咖啡厅·互动（摸头/送礼）',
    '/api/cafe/receivecurrency': '咖啡厅·领取体力和信用点',
    '/api/cafe/summoncharacter': '咖啡厅·邀请学生入店',
    '/api/campaign/list': '关卡开放信息（活动副本列表）',
    '/api/clan/check': '社团·状态检查',
    '/api/clan/lobby': '社团·大厅',
    '/api/clan/chat/records': '社团·聊天记录',
    '/api/contentsave/get': '云存档读取',
    '/api/contentsweep/request': '扫荡·执行',
    '/api/contentsweep/multisweep': '扫荡·多关卡批量扫荡',
    '/api/contentsweep/setmultisweeppreset': '扫荡·保存扫荡预设',
    '/api/craft/list': '制造·节点列表',
    '/api/craft/reward': '制造·领取成品',
    '/api/craft/updatenodelevel': '制造·节点升级',
    '/api/craft/selectnode': '制造·选择节点',
    '/api/craft/beginprocess': '制造·开始制造',
    '/api/craft/shiftingbeginprocess': '制造·切换节点开始（三解）',
    '/api/echelon/list': '编队·列表',
    '/api/echelon/save': '编队·保存',
    '/api/event/rewardincrease': '账号加成信息（掉落/经验加成，刷界面时高频）',
    '/api/eventcontent/adventurelist': '活动·关卡列表',
    '/api/eventcontent/collectionlist': '活动·收集进度',
    '/api/eventcontent/enterstorystage': '活动·进入剧情关',
    '/api/eventcontent/storystageresult': '活动·剧情关结算',
    '/api/eventcontent/scenariogrouphistoryupdate': '活动·剧情历史更新',
    '/api/eventcontent/shoplist': '活动·商店列表',
    '/api/eventcontent/shopbuymerchandise': '活动·商店购买',
    '/api/friend/check': '好友·状态检查',
    '/api/item/list': '道具·列表',
    '/api/mail/check': '邮件·未读检查',
    '/api/mail/list': '邮件·列表',
    '/api/mail/listsemipermanent': '邮件·永久邮箱列表',
    '/api/mail/receive': '邮件·领取附件',
    '/api/management/data': '主界面数据（管理局汇总）',
    '/api/minigame/missionlist': '小游戏·任务列表',
    '/api/mission/list': '任务·列表',
    '/api/mission/reward': '任务·领取奖励（单个）',
    '/api/mission/multiplereward': '任务·批量领取奖励',
    '/api/mission/guidemissionseasonlist': '任务·引导任务赛季',
    '/api/networktime/sync': '服务器时间同步',
    '/api/notification/eventcontentreddotcheck': '红点检查（活动未读）',
    '/api/opencondition/eventlist': '开放条件·活动列表',
    '/api/raid/lobby': '总力战·大厅',
    '/api/raid/opponentlist': '总力战·排名列表 (？)',
    '/api/raid/createbattle': '总力战·创建战斗',
    '/api/raid/enterbattle': '总力战·进入战斗',
    '/api/raid/endbattle': '总力战·战斗结算',
    '/api/raid/sweep': '总力战·扫荡',
    '/api/raid/seasonreward': '总力战·赛季奖励',
    '/api/raid/rankingindex': '总力战·排名索引',
    '/api/scenario/skip': '剧情·跳过',
    '/api/schooldungeon/list': '学院副本·列表 (？)',
    '/api/eliminateraid/lobby': '大决战·大厅（EliminateRaid）',
    '/api/resetablecontent/get': '可重置内容·获取',
    '/api/shop/list': '商店·列表（信用点/青辉石）',
    '/api/shop/buymerchandise': '商店·购买商品（普通商店/战术对抗赛商店）',
    '/api/shop/refresh': '商店·刷新商品列表',
    '/api/shop/buyrefreshmerchandise': '商店·手动刷新商品',
    '/api/toast/list': '弹窗通知列表',
    '/api/weekdungeon/list': '周常副本·列表（课程表）(？)',
    '/api/state': '客户端状态上报（非标准端点）',
}
STD_REQ = {'Protocol', 'Resendable', 'Hash', 'IsTest', 'SessionKey', 'AccountId', 'OSType'}
MASK_KEYS = {'MxToken', 'Token'}


def jtype(v):
    if isinstance(v, bool): return 'bool'
    if isinstance(v, int): return 'int'
    if isinstance(v, float): return 'float'
    if isinstance(v, str): return 'str'
    if isinstance(v, list): return 'array'
    if isinstance(v, dict): return 'object'
    if v is None: return 'null'
    return '?'


def short(v, n=48):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + '…'


def mask(k, v):
    if isinstance(v, str) and k in MASK_KEYS and len(v) > 12:
        return v[:8] + '…'
    return v


def outline(v, depth=0, maxdepth=3):
    """渲染响应结构树（缩进 bullet）。"""
    pad = '  ' * depth
    if isinstance(v, dict):
        if depth >= maxdepth:
            return [f'{pad}- …({len(v)} keys)']
        lines = []
        for k, x in v.items():
            t = jtype(x)
            if isinstance(x, (dict, list)):
                lines.append(f'{pad}- **{k}**: {t}')
                lines += outline(x, depth + 1, maxdepth)
            else:
                lines.append(f'{pad}- **{k}**: {t} = `{short(mask(k, x))}`')
        return lines
    if isinstance(v, list):
        if depth >= maxdepth:
            return [f'{pad}- …(array len={len(v)})']
        if not v:
            return [f'{pad}- (空数组)']
        lines = [f'{pad}- [0] ({jtype(v[0])}):']
        lines += outline(v[0], depth + 1, maxdepth)
        if len(v) > 1:
            lines.append(f'{pad}- …共 {len(v)} 个元素')
        return lines
    return [f'{pad}- `{short(v)}`']


def main():
    reqs = [json.loads(l) for l in io.open(f'{HERE}/session_plain_all.jsonl', encoding='utf-8')]
    resps = {}
    for l in io.open(f'{HERE}/resp_plain_all.jsonl', encoding='utf-8'):
        r = json.loads(l)
        resps[r['file']] = r

    api = json.load(open(f'{HERE}/api_map_v2.json', encoding='utf-8'))

    # 聚合：url → 请求字段统计 / 响应结构样本 / N 序列
    fields = defaultdict(lambda: defaultdict(lambda: {'types': set(), 'examples': []}))
    resp_keys = defaultdict(lambda: defaultdict(lambda: {'types': set(), 'examples': []}))
    resp_sub = {}
    # N 序列（仅今天 17:21 重登会话——时间线与 first_call_N_today 用）
    ns = defaultdict(list)
    for r in reqs:
        if r['file'] < '1791883316863':
            continue
        ns[r['url']].append((r['json']['Hash'] & 0xffffffff, r['file']))
    for r in reqs:
        url = r['url']
        j = r['json']
        for k, v in j.items():
            if k in STD_REQ:
                continue
            e = fields[url][k]
            e['types'].add(jtype(v))
            if len(e['examples']) < 3:
                e['examples'].append(mask(k, v))

    for fname, r in resps.items():
        url = r['url']
        pk = r['json'].get('packet')
        if isinstance(pk, str):
            try:
                pk = json.loads(pk)
            except Exception:
                pk = None
        if isinstance(pk, dict):
            for k, v in pk.items():
                e = resp_keys[url][k]
                e['types'].add(jtype(v))
                if len(e['examples']) < 2:
                    e['examples'].append(v)
                    resp_sub.setdefault(url, {})[k] = v

    # 今天的日常会话调用顺序
    sess = [r for r in reqs if r['file'] >= '1791883316863']
    sess.sort(key=lambda r: r['file'])
    order = []
    for r in sess:
        u = r['url']
        if u not in order:
            order.append(u)

    # ===== 生成 api_doc.json =====
    doc = {}
    for url, info in sorted(api.items()):
        d = {'protocol': info['protocol'], 'obf': info['obf'], 'samples': info['samples'],
             'cn': CN_NAMES.get(url, '')}
        d['request_fields'] = {k: {'types': sorted(v['types']),
                                   'example': short(v['examples'][0], 60)}
                               for k, v in sorted(fields.get(url, {}).items())}
        d['response_packet_keys'] = {k: {'types': sorted(v['types'])}
                                     for k, v in sorted(resp_keys.get(url, {}).items())}
        d['first_call_N_today'] = ns[url][0][0] if ns.get(url) else None
        doc[url] = d
    doc_s = _redact(json.dumps(doc, ensure_ascii=False, indent=1))
    open(f'{HERE}/api_doc.json', 'w', encoding='utf-8').write(doc_s)

    # ===== 生成 docs/API.md =====
    os.makedirs(f'{HERE}/docs', exist_ok=True)
    md = io.open(f'{HERE}/docs/API.md', 'w', encoding='utf-8')
    w = lambda s: md.write(_redact(s))
    w('# autoBA 国服接口文档\n\n')
    w('> 自动生成自 867 组抓包双向明文（2026-10-11 ~ 10-13，测试号 10000000000）。\n')
    w('> 请求 Hash = (Protocol << 32) | N；N 为会话级全局计数，auth 起算 N=1。\n')
    w('> 请求/响应 key 均明文附在密文尾部（请求=b64-hex ASCII 形态，响应=原始二进制形态），IV 固定 JOSY。\n\n')

    w('## 目录\n\n')
    w('| 接口 | 中文 | Protocol |\n|---|---|---|\n')
    for url in sorted(api):
        cn = CN_NAMES.get(url, '')
        anchor = url.replace('/', '')
        w(f'| [{url}](#{anchor}) | {cn} | {api[url]["protocol"]} |\n')
    w('\n')

    w('## 今日日常会话时间线（17:21 重登，127 请求）——你在游戏里干了啥\n\n')
    w('**登录批次 N=1~30**：登录认证 → 学园日程信息 → 登录同步 → 道具列表 → 时间同步 → 云存档 → 通行证信息 → 主界面数据 → 任务列表×3 → 通行证任务 → 红点/邮件/社团/好友检查 → 商城列表 → 永久邮箱\n\n')
    w('**之后你干的事（按首次调用）：**\n\n')
    daily = []
    for u, lst in ns.items():
        gt30 = [n for n, _ in lst if n > 30]
        if gt30:
            daily.append((min(gt30), u))
    daily.sort()
    for n, u in daily:
        cn = CN_NAMES.get(u, u)
        w(f'- {cn}（N={n}）\n')
    w('\n---\n\n')

    cats = defaultdict(list)
    for url in sorted(api):
        cat = url.split('/')[2] if url.count('/') >= 3 else 'other'
        cats[cat].append(url)
    for cat, urls in sorted(cats.items()):
        w(f'# {cat}\n\n')
        for url in sorted(urls):
            info = api[url]
            cn = CN_NAMES.get(url, '')
            w(f'## {url}\n\n')
            w(f'- **中文**: {cn}\n')
            w(f'- **Protocol**: {info["protocol"]}　**混淆名**: `{info["obf"]}`　**样本**: {info["samples"]}\n')
            biz = fields.get(url, {})
            if biz:
                w('\n### 请求业务字段\n\n')
                w('| 字段 | 类型 | 示例 |\n|---|---|---|\n')
                for k, v in sorted(biz.items()):
                    ts = '/'.join(sorted(v['types']))
                    ex = short(v['examples'][0], 60)
                    w(f'| {k} | {ts} | `{ex}` |\n')
            else:
                w('\n请求无业务字段（仅标准头）。\n')
            rk = resp_keys.get(url, {})
            if rk:
                w('\n### 响应 packet 顶层\n\n')
                for k, v in sorted(rk.items()):
                    ts = '/'.join(sorted(v['types']))
                    w(f'- **{k}**: {ts}\n')
                # 结构树（取第一个有内容的子结构样本，限深）
                sub = resp_sub.get(url, {})
                w('\n<details><summary>响应结构示例（限深 3 层）</summary>\n\n```\n')
                for k, v in sorted(sub.items()):
                    w(f'- **{k}**\n')
                    for line in outline(v, 1, 3):
                        w(line + '\n')
                w('```\n</details>\n\n')
            else:
                w('\n响应 packet 为空/非对象。\n')
            w('\n')
    md.close()
    print(f'[+] docs/API.md ({os.path.getsize(f"{HERE}/docs/API.md")} B)')
    print(f'[+] api_doc.json ({len(doc)} 接口)')


if __name__ == '__main__':
    main()
