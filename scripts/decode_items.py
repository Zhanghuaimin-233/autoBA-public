"""批量转换 ItemDBSchema 每行 flatbuffer → JSON，并与 LocalizeEtc 关联生成道具中文名映射。
产出：tables/item_names.json {ItemId: {name_cn, rarity, category, icon, ...}}
"""
import json
import os
import shutil
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = r'.'
BAAX = f'{HERE}/tools/baax.exe'
FLAT = f'{HERE}/tools/japan.flat'
ROWS = f'{HERE}/tables/rows_item'
OUT = f'{HERE}/tables/decoded_items'


def convert_row(iid):
    d = f'{ROWS}/{iid}'
    os.makedirs(d, exist_ok=True)
    os.replace(f'{ROWS}/{iid}.bytes', f'{d}/ItemDBSchema.bytes') if os.path.exists(f'{ROWS}/{iid}.bytes') else None
    r = subprocess.run([BAAX, 'convert', 'flatbuffers', '-i', f'{d}/ItemDBSchema.bytes',
                        '-o', f'{OUT}/{iid}.json', '--flat', FLAT],
                       capture_output=True, text=True, timeout=60)
    return iid, r.returncode == 0


def main():
    os.makedirs(OUT, exist_ok=True)
    # 清掉旧的平铺行文件（已移入子目录的跳过）
    for f in os.listdir(ROWS):
        p = os.path.join(ROWS, f)
        if os.path.isfile(p):
            iid = f.rsplit('.', 1)[0]
            d = os.path.join(ROWS, iid)
            os.makedirs(d, exist_ok=True)
            shutil.move(p, os.path.join(d, 'ItemDBSchema.bytes'))

    ids = [d for d in os.listdir(ROWS) if os.path.isdir(os.path.join(ROWS, d)) and d.isdigit()]
    ids.sort(key=int)
    print(f'[+] {len(ids)} 行待转换')

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for iid, success in ex.map(convert_row, ids):
            if success:
                ok += 1
            else:
                fail += 1
                if fail <= 5:
                    print(f'[fail] {iid}')
    print(f'[+] 转换完成: {ok} 成功 / {fail} 失败')

    # 关联 LocalizeEtc → 道具中文名
    loc = json.load(open(f'{HERE}/tables/full/ExcelDB/LocalizeEtcExcel.json', encoding='utf-8'))
    loc_map = {r['Key']: r for r in loc}

    items = {}
    for iid in ids:
        p = f'{OUT}/{iid}.json'
        if not os.path.exists(p):
            continue
        inner = os.path.join(p, 'ItemExcel.json')
        path = inner if os.path.isfile(inner) else p
        try:
            d = json.load(open(path, encoding='utf-8'))
        except (PermissionError, IsADirectoryError, json.JSONDecodeError):
            continue
        rows = d if isinstance(d, list) else d.get('ItemExcel', d)
        if not rows:
            continue
        it = rows[0]
        li = it.get('LocalizeEtcId')
        loc_row = loc_map.get(li, {})
        items[it['Id']] = {
            'name_cn': loc_row.get('NameKr', ''),
            'desc_cn': loc_row.get('DescriptionKr', ''),
            'rarity': it.get('Rarity'),
            'category': it.get('ItemCategory'),
            'icon': it.get('Icon'),
        }
    json.dump(items, open(f'{HERE}/tables/item_names.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'[+] item_names.json: {len(items)} 道具')


if __name__ == '__main__':
    main()
