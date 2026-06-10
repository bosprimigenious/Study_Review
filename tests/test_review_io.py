#!/usr/bin/env python3
"""Unit tests for review_io helpers (Epic 5-02)."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_io import due_dates_from_rating  # noqa: E402


class TestDueDatesFromRating(unittest.TestCase):
    def test_forgot(self) -> None:
        result = due_dates_from_rating("忘了", date(2026, 6, 10))
        self.assertEqual(result, [date(2026, 6, 10), date(2026, 6, 11)])

    def test_hard(self) -> None:
        result = due_dates_from_rating("困难", date(2026, 6, 10))
        self.assertEqual(result, [date(2026, 6, 11)])

    def test_ok(self) -> None:
        result = due_dates_from_rating("还行", date(2026, 6, 10))
        self.assertEqual(result, [date(2026, 6, 13)])

    def test_easy(self) -> None:
        result = due_dates_from_rating("很熟", date(2026, 6, 10))
        self.assertEqual(result, [date(2026, 6, 17)])

    def test_cross_month(self) -> None:
        result = due_dates_from_rating("困难", date(2026, 1, 31))
        self.assertEqual(result, [date(2026, 2, 1)])

    def test_cross_year(self) -> None:
        result = due_dates_from_rating("忘了", date(2026, 12, 31))
        self.assertEqual(result, [date(2026, 12, 31), date(2027, 1, 1)])

    def test_leap_year_feb(self) -> None:
        result = due_dates_from_rating("困难", date(2028, 2, 28))
        self.assertEqual(result, [date(2028, 2, 29)])

    def test_invalid_rating(self) -> None:
        with self.assertRaises(ValueError):
            due_dates_from_rating("不知道", date(2026, 6, 10))


if __name__ == "__main__":
    unittest.main()
