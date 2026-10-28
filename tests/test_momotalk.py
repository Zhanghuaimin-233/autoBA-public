"""webui/momotalk.py 的纯逻辑测试。

跑法：./.venv/Scripts/python.exe -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webui import momotalk


def _sched(sid, favor_rank, script_group, stone=20, parcel_id=3):
    return {
        'Id': sid, 'FavorRank': favor_rank, 'ScenarioSriptGroupId': script_group,
        'RewardParcelType': ['Currency'], 'RewardParcelId': [parcel_id],
        'RewardAmount': [stone], 'SecretStoneAmount': 1,
    }


class TestClassify(unittest.TestCase):
    SCHEDULES = [
        _sched(100022, 2, 1000202, 20),
        _sched(100023, 3, 1000203, 40),
        _sched(100025, 15, 1000205, 120),
    ]
    GROUPS = {100022: 100020050, 100023: 100020150, 100025: 100020240}

    def test_split_by_favor(self):
        out = momotalk.classify_char(self.SCHEDULES, set(), 5, self.GROUPS)
        self.assertEqual([i['id'] for i in out['claimable']], [100022, 100023])
        self.assertEqual([i['id'] for i in out['locked']], [100025])

    def test_done_excluded(self):
        out = momotalk.classify_char(self.SCHEDULES, {100022}, 2, self.GROUPS)
        self.assertEqual([i['id'] for i in out['claimable']], [])
        self.assertEqual([i['id'] for i in out['locked']], [100023, 100025])

    def test_group_and_stone_carried(self):
        out = momotalk.classify_char(self.SCHEDULES, set(), 30, self.GROUPS)
        first = out['claimable'][0]
        self.assertEqual(first['group'], 100020050)
        self.assertEqual(first['scriptGroup'], 1000202)
        self.assertEqual(first['stone'], 20)

    def test_unknown_group_defaults_zero(self):
        out = momotalk.classify_char(self.SCHEDULES, set(), 30, {})
        self.assertTrue(all(i['group'] == 0 for i in out['claimable']))

    def test_stone_ignores_other_currency(self):
        s = _sched(1, 2, 100, 999, parcel_id=1)          # Currency 1 = Gold，不算青辉石
        self.assertEqual(momotalk._stones(s), 0)


class TestSummarize(unittest.TestCase):
    def test_totals(self):
        rows = [
            {'claimable': [{'stone': 20}, {'stone': 40}], 'locked': [{'stone': 120}]},
            {'claimable': [{'stone': 60}], 'locked': []},
            {'claimable': [], 'locked': []},
        ]
        sm = momotalk.summarize(rows)
        self.assertEqual(sm['claimCount'], 3)
        self.assertEqual(sm['lockedCount'], 1)
        self.assertEqual(sm['claimStone'], 120)
        self.assertEqual(sm['lockedStone'], 120)
        self.assertEqual(sm['chars'], 2)                 # 有可领或卡好感的角色
        self.assertEqual(sm['totalChars'], 3)            # 剧情表里有的全部角色
        self.assertEqual(sm['doneChars'], 1)             # 全部已完成的角色

    def test_empty(self):
        sm = momotalk.summarize([])
        self.assertEqual(sm['claimCount'], 0)
        self.assertEqual(sm['chars'], 0)


if __name__ == '__main__':
    unittest.main()
