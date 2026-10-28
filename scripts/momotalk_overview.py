"""MomoTalk 只读进度盘点（零请求，读抓包快照 + 本地表）。

用法:
    ./.venv/Scripts/python.exe scripts/momotalk_overview.py [--json out.json]

口径与 `webui/momotalk.py` 的 build_state 一致：**名册 ∩ 剧情表**，
排除已完成、按好感分两类（可领 / 卡好感）。"尚未读到"这一档已取消——
服务端不校验读取进度，没读过也能直接领（见 docs/模块/MomoTalk.md 第五节）。

数据来源:
    1. $AUTOBA_CAPTURE_DIR 里最新的 loginsync → CharacterDBs（名册/好感）+ FavorScheduleRecords（已完成）
    2. tables/full/ExcelDB/AcademyFavorScheduleExcel.json（1053 条剧情定义）

注意：这是**抓包快照**的离线盘点，实时数据以 WebUI 的 `/api/momotalk/state` 为准。
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import ba_crypto  # noqa: E402

CAP = os.environ.get("AUTOBA_CAPTURE_DIR") or os.path.join(ROOT, "capture", "ba")
TABLES = os.path.join(ROOT, "tables", "full", "ExcelDB")


def _newest(pattern):
    best = None
    for f in glob.glob(os.path.join(CAP, pattern)):
        base = os.path.basename(f).split("_")[0]
        if not base.isdigit():
            continue
        if best is None or int(base) > best[0]:
            best = (int(base), f)
    return best[1] if best else None


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _stones(s) -> int:
    """剧情奖励里的免费青辉石（Currency 3 = GemBonus）。"""
    return sum(a for t, i, a in zip(s["RewardParcelType"], s["RewardParcelId"], s["RewardAmount"])
               if t == "Currency" and i == 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    sync_f = _newest("*loginsync.json")
    if not sync_f:
        sys.exit("没找到 loginsync 抓包")

    pkt = ba_crypto.decrypt_response(_load(sync_f)["resp_body"])["packet"]
    roster = {str(c["UniqueId"]): c for c in
              (pkt.get("CharacterListResponse") or {}).get("CharacterDBs") or []}
    done_map = (pkt.get("MomoTalkOutLineResponse") or {}).get("FavorScheduleRecords") or {}

    sched = _load(os.path.join(TABLES, "AcademyFavorScheduleExcel.json"))
    names = _load(os.path.join(ROOT, "tables", "char_names.json"))
    by_char = {}
    for r in sched:
        by_char.setdefault(str(r["CharacterId"]), []).append(r)

    rows = []
    for cid, info in roster.items():
        schedules = by_char.get(cid) or []
        if not schedules:
            continue
        rank = info.get("FavorRank") or 0
        done = set(done_map.get(cid) or [])
        todo = [r for r in schedules if r["Id"] not in done]
        claimable = [r for r in todo if r["FavorRank"] <= rank]
        locked = [r for r in todo if r["FavorRank"] > rank]
        rows.append({
            "charId": cid,
            "name": names.get(cid, f"#{cid}"),
            "rank": rank,
            "total": len(schedules),
            "done": len(schedules) - len(todo),
            "claimable": claimable,
            "locked": locked,
            "stone": sum(_stones(x) for x in claimable),
        })
    rows.sort(key=lambda r: (-len(r["claimable"]), -len(r["locked"]), r["name"]))

    n_claim = sum(len(r["claimable"]) for r in rows)
    n_lock = sum(len(r["locked"]) for r in rows)
    stone = sum(r["stone"] for r in rows)
    stone_lock = sum(_stones(x) for r in rows for x in r["locked"])

    print(f"快照: loginsync={os.path.basename(sync_f)}")
    print(f"名册 {len(roster)} 人，其中有剧情定义 {len(rows)} 人")
    print(f"可领 {n_claim} 条 / 青辉石 {stone}（{sum(1 for r in rows if r['claimable'])} 个角色）")
    print(f"卡好感 {n_lock} 条 / 青辉石 {stone_lock}（{sum(1 for r in rows if r['locked'])} 个角色）")
    print()
    print(f"{'角色':<10}{'好感':>4}  {'已完成':>6}  {'可领':>4}  {'卡好感':>6}  {'青辉石':>6}")
    for r in rows:
        if not (r["claimable"] or r["locked"]):
            continue
        print(f"{r['name']:<10}{r['rank']:>4}  {r['done']:>4}/{r['total']:<3}"
              f"{len(r['claimable']):>4}  {len(r['locked']):>6}  {r['stone']:>6}")

    if args.json:
        out = [{"charId": r["charId"], "name": r["name"], "rank": r["rank"],
                "done": r["done"], "total": r["total"],
                "claimable": [x["Id"] for x in r["claimable"]],
                "locked": [{"id": x["Id"], "favor": x["FavorRank"]} for x in r["locked"]]}
               for r in rows]
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"\n明细已写入 {args.json}")


if __name__ == "__main__":
    main()
