"""webui/daily.py 的纯逻辑测试。

跑法：./.venv/Scripts/python.exe -m unittest discover -s tests -v
（只依赖标准库 unittest，不引入 pytest）
"""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webui import daily


class TestFitCounts(unittest.TestCase):
    MAPS = [{'key': 'A'}, {'key': 'B'}, {'key': 'C'}]

    def test_enough_balance(self):
        out = daily.fit_counts({'A': 2, 'B': 2, 'C': 2}, 10, self.MAPS)
        self.assertEqual(out, {'A': 2, 'B': 2, 'C': 2})

    def test_short_balance_greedy(self):
        """券不够时按关卡顺序先满足前面的。"""
        out = daily.fit_counts({'A': 2, 'B': 2, 'C': 2}, 3, self.MAPS)
        self.assertEqual(out, {'A': 2, 'B': 1, 'C': 0})

    def test_zero_balance(self):
        out = daily.fit_counts({'A': 2}, 0, self.MAPS)
        self.assertEqual(out, {'A': 0, 'B': 0, 'C': 0})

    def test_unknown_balance_passthrough(self):
        """券数未知（None）时按配置原样下发，交给服务端判断。"""
        out = daily.fit_counts({'A': 2, 'B': 1}, None, self.MAPS)
        self.assertEqual(out, {'A': 2, 'B': 1})

    def test_negative_and_missing(self):
        out = daily.fit_counts({'A': -1, 'B': 0}, 5, self.MAPS)
        self.assertEqual(out, {'A': 0, 'B': 0, 'C': 0})

    def test_negative_balance_clamped(self):
        out = daily.fit_counts({'A': 2}, -3, self.MAPS)
        self.assertEqual(out['A'], 0)


class TestSessionDead(unittest.TestCase):
    def test_detects_session_errors(self):
        for msg in ('33004 rid 链断裂', '33005 N 不匹配', '会话已过期', 'time over'):
            self.assertTrue(daily.looks_like_session_dead(msg), msg)

    def test_ignores_other_errors(self):
        for msg in ('挑战券已用尽', 'Connection reset', '500 Internal'):
            self.assertFalse(daily.looks_like_session_dead(msg), msg)


class TestGameDay(unittest.TestCase):
    """日常刷新以本地 04:00 为界（BA 国服服务器重置时间）。"""

    def test_before_reset_belongs_to_previous_day(self):
        self.assertEqual(daily.game_day(datetime.datetime(2026, 10, 28, 3, 59)), '2026-10-27')
        self.assertEqual(daily.game_day(datetime.datetime(2026, 10, 28, 0, 0)), '2026-10-27')

    def test_at_and_after_reset_is_new_day(self):
        self.assertEqual(daily.game_day(datetime.datetime(2026, 10, 28, 4, 0)), '2026-10-28')
        self.assertEqual(daily.game_day(datetime.datetime(2026, 10, 28, 23, 59)), '2026-10-28')

    def test_month_boundary(self):
        self.assertEqual(daily.game_day(datetime.datetime(2026, 11, 1, 2, 30)), '2026-10-31')


if __name__ == '__main__':
    unittest.main()
