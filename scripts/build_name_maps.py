"""构建统一名称映射：items + currency + equipment → tables/name_maps.json"""
import json

BASE = r'./tables/full/ExcelDB'


def main():
    loc_rows = json.load(open(f'{BASE}/LocalizeEtcExcel.json', encoding='utf-8'))
    loc = {r['Key']: (r.get('NameKr') or '').strip() for r in loc_rows}

    cur = {}
    for r in json.load(open(f'{BASE}/CurrencyExcel.json', encoding='utf-8')):
        cur[str(r['ID'])] = loc.get(r['LocalizeEtcId']) or r.get('CurrencyType', '')

    equip = {}
    for r in json.load(open(f'{BASE}/EquipmentExcel.json', encoding='utf-8')):
        equip[str(r['Id'])] = loc.get(r['LocalizeEtcId']) or f'装备#{r["Id"]}'

    items = json.load(open(r'./tables/item_names.json', encoding='utf-8'))
    items = {k: v['name_cn'] or f'道具#{k}' for k, v in items.items()}

    chars = json.load(open(r'./tables/char_names.json', encoding='utf-8'))

    acad = json.load(open(f'{BASE}/AcademyLocationExcel.json', encoding='utf-8'))
    acad = acad if isinstance(acad, list) else acad.get('AcademyLocation', acad)
    academy = {}
    for r in acad:
        academy[str(r['Id'])] = loc.get(r['LocalizeEtcId']) or f'地点#{r["Id"]}'

    out = {'item': items, 'currency': cur, 'equipment': equip,
           'character': chars, 'academy_location': academy}
    json.dump(out, open(r'./tables/name_maps.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'[+] name_maps.json: item={len(items)} currency={len(cur)} equipment={len(equip)} '
          f'character={len(chars)} academy_location={len(academy)}')
    print('  货币样例:', dict(list(cur.items())[:6]))
    print('  装备样例:', dict(list(equip.items())[:3]))
    print('  地点样例:', dict(list(academy.items())[:7]))


if __name__ == '__main__':
    main()
