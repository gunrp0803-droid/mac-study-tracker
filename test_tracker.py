import unittest
import sys
import types

tkinter_stub = types.ModuleType("tkinter")
tkinter_stub.messagebox = types.ModuleType("tkinter.messagebox")
tkinter_stub.ttk = types.ModuleType("tkinter.ttk")
sys.modules.setdefault("tkinter", tkinter_stub)
sys.modules.setdefault("tkinter.messagebox", tkinter_stub.messagebox)
sys.modules.setdefault("tkinter.ttk", tkinter_stub.ttk)
sys.modules.setdefault("requests", types.ModuleType("requests"))

from tracker import StudyTrackerApp


class StudyTrackerPureLogicTests(unittest.TestCase):
    def setUp(self):
        self.app = StudyTrackerApp.__new__(StudyTrackerApp)
        self.app.target_hours = 3.0
        self.app.accumulated_seconds = 0
        self.app.is_tracking = False
        self.app.blocked_apps = ["league of legends"]

    def test_parse_target_time(self):
        self.assertEqual(self.app.parse_str_to_hours("02:30"), 2.5)
        self.assertEqual(self.app.parse_str_to_hours("3"), 3.0)
        self.assertIsNone(self.app.parse_str_to_hours("01:60"))
        self.assertIsNone(self.app.parse_str_to_hours("nan"))

    def test_format_target_time_rolls_over_minutes(self):
        self.assertEqual(self.app.format_hours_to_str(1.999), "02:00")
        self.assertEqual(self.app.format_hours_to_str(2.5), "02:30")

    def test_invalid_target_cannot_reach_goal(self):
        self.app.target_hours = float("nan")
        self.assertEqual(self.app.target_seconds(), 0)
        payload = self.app.build_study_status_payload(today_study_seconds=999999)
        self.assertFalse(payload["goal_reached"])

    def test_payload_clamps_negative_study_time(self):
        payload = self.app.build_study_status_payload(today_study_seconds=-1)
        self.assertEqual(payload["today_study_seconds"], 0)
        self.assertEqual(payload["target_study_seconds"], 10800)
        self.assertFalse(payload["goal_reached"])

    def test_blocked_app_matching_is_case_insensitive(self):
        self.assertTrue(self.app.check_app_blocked("League of Legends"))
        self.assertFalse(self.app.check_app_blocked("Visual Studio Code"))


if __name__ == "__main__":
    unittest.main()
