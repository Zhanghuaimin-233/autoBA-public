"""全量解码 CharacterDBSchema（LocalizeEtc 哈希扫描法，绕过 JP flat 漂移）
→ tables/char_names.json {CharacterId: 中文名}
"""
import json
import sqlite3
import struct

HERE = r'.'


def main():
    loc_rows = json.load(open(f'{HERE}/tables/full/ExcelDB/LocalizeEtcExcel.json', encoding='utf-8'))
    names = {r['Key']: (r.get('NameKr') or '').strip() for r in loc_rows}
    keys = set(k for k, v in names.items() if v)

    conn = sqlite3.connect(f'{HERE}/tables/ExcelDB.db')
    out = {}
    fail = 0
    for cid, blob in conn.execute('SELECT Id, Bytes FROM CharacterDBSchema'):
        hits = []
        for off in range(0, len(blob) - 3):
            v = struct.unpack_from('<I', blob, off)[0]
            if v in keys:
                hits.append((off, v))
        if not hits:
            fail += 1
            continue
        # 名称引用位于偏移 ~312-320 区间（实测），多个命中时取该区段优先
        hits.sort(key=lambda h: (abs(h[0] - 316), h[0]))
        out[cid] = names[hits[0][1]]
    json.dump(out, open(f'{HERE}/tables/char_names.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'[+] char_names.json: {len(out)} 角色, 无命中 {fail}')
    for cid in (10111, 10045, 13003, 10009, 10000):
        print(f'  {cid}: {out.get(cid, "?")}')


if __name__ == '__main__':
    main()
