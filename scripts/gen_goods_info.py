"""从 ExcelDB.db 的 GoodsDBSchema 生成 goods_info.json。

思路：GoodsDB 每条是 flatbuffer，里面明文内嵌 Unity 资源路径（如
UIs/01_Common/03_NonEquipment/Item_Icon_SecretStone_Aru）。
item_names.json 里的 1061 条道具带同名 icon 字段，于是用「图标路径」做连接键，
就能给绝大多数商品补上中文名/描述/稀有度，不必解 flatbuffer。

跑法：python scripts/gen_goods_info.py
产出：tables/goods_info.json  {goodsId: {name, desc, rarity, category, icon}}
"""
import json
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'tables', 'ExcelDB.db')
NAMES = os.path.join(ROOT, 'tables', 'item_names.json')
OUT = os.path.join(ROOT, 'tables', 'goods_info.json')

ICON_RE = re.compile(rb'UIs/[ -~]+')

# item_names 里没有的货币类图标，按游戏内显示名补（只收能确定的）
ICON_NAMES = {
    'Currency_Icon_Gold': ('信用积分', '通用货币，用于强化与购买。', 'N'),
    'Currency_Icon_AP': ('行动点', '挑战关卡所需的行动点。', 'N'),
    'Currency_Icon_Gem': ('青辉石', '珍贵的青辉石。', 'N'),
}


def main():
    items = json.load(open(NAMES, encoding='utf-8'))
    by_icon = {}
    for v in items.values():
        ic = (v or {}).get('icon')
        if ic:
            by_icon.setdefault(ic, v)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    rows = cur.execute('select Id, Bytes from GoodsDBSchema').fetchall()

    out = {}
    for gid, blob in rows:
        m = ICON_RE.search(blob)
        if not m:
            continue
        icon = m.group(0).decode('utf-8', 'ignore').split('\x00')[0]
        meta = by_icon.get(icon) or {}
        name, desc, rarity = meta.get('name_cn'), meta.get('desc_cn'), meta.get('rarity')
        if not name:
            fb = ICON_NAMES.get(icon.rsplit('/', 1)[-1].rsplit('.', 1)[0])
            if fb:
                name, desc, rarity = fb
        out[str(gid)] = {
            'icon': icon,
            'name': name or '',
            'desc': desc or '',
            'rarity': rarity or '',
            'category': meta.get('category') or '',
        }

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    named = sum(1 for v in out.values() if v['name'])
    print(f'[+] GoodsDB {len(rows)} 条 → 有图标 {len(out)} 条 → 有中文名 {named} 条')
    print(f'[+] 写出 {OUT}')


if __name__ == '__main__':
    main()
