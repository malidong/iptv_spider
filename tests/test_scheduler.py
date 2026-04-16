# -*- coding: utf-8 -*-
"""Tests for cron scheduler."""

import os
import unittest
from pathlib import Path
import tempfile

from iptv_spider.scheduler import (
    CronSchedule,
    Scheduler,
    create_scheduler,
    LOCK_FILE,
)


class TestScheduler(unittest.TestCase):
    """Test scheduler."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scheduler = Scheduler(cron_expression="0 2 * * *")
        self.scheduler.lock_file = Path(self.temp_dir) / LOCK_FILE

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scheduler_initialization(self):
        """Test scheduler is initialized with correct value."""
        sched = Scheduler(cron_expression="0 2 * * *")
        self.assertEqual(sched.cron_expression, "0 2 * * *")

    def test_should_run_without_cron(self):
        """Test should_run returns False when no CRON is set."""
        sched = Scheduler()
        self.assertFalse(sched.should_run())

    def test_should_run_with_lock_active(self):
        """Test should_run returns False when lock is active."""
        self.scheduler.acquire_lock()
        self.assertFalse(self.scheduler.should_run())

    def test_acquire_lock(self):
        """Test acquiring lock returns run ID."""
        run_id = self.scheduler.acquire_lock()
        self.assertTrue(run_id.startswith("run_"))
        self.assertTrue(self.scheduler.lock_file.exists())

    def test_release_lock(self):
        """Test releasing lock removes lock file."""
        run_id = self.scheduler.acquire_lock()
        self.scheduler.release_lock(run_id)
        self.assertFalse(self.scheduler.lock_file.exists())

    def test_release_lock_wrong_id(self):
        """Test releasing lock with wrong ID does nothing."""
        self.scheduler.acquire_lock()
        self.scheduler.release_lock("wrong_id")
        self.assertTrue(self.scheduler.lock_file.exists())

    def test_get_last_run_info_no_lock(self):
        """Test get_last_run_info returns None when no lock."""
        info = self.scheduler.get_last_run_info()
        self.assertIsNone(info)

    def test_get_last_run_info_with_lock(self):
        """Test get_last_run_info returns run info when lock exists."""
        run_id = self.scheduler.acquire_lock()
        info = self.scheduler.get_last_run_info()
        self.assertIsNotNone(info)
        self.assertEqual(info["run_id"], run_id)


class TestCreateScheduler(unittest.TestCase):
    """Test scheduler factory."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scheduler = create_scheduler()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_scheduler_no_cron(self):
        """Test create_scheduler without IPTV_CRON_SCHEDULE."""
        sched = create_scheduler()
        self.assertIsNone(sched.cron_expression)

    def test_create_scheduler_with_cron(self):
        """Test create_scheduler with IPTV_CRON_SCHEDULE."""
        os.environ["IPTV_CRON_SCHEDULE"] = "0 2 * * *"
        sched = create_scheduler()
        self.assertEqual(sched.cron_expression, "0 2 * * *")
        del os.environ["IPTV_CRON_SCHEDULE"]


class TestCronSchedule(unittest.TestCase):
    """Test CronSchedule dataclass."""

    def test_cron_schedule_creation(self):
        """Test CronSchedule is created with correct values."""
        schedule = CronSchedule(expression="0 2 * * *", enabled=True)
        self.assertEqual(schedule.expression, "0 2 * * *")
        self.assertTrue(schedule.enabled)

    def test_cron_schedule_disabled(self):
        """Test CronSchedule disabled state."""
        schedule = CronSchedule(expression="0 2 * * *", enabled=False)
        self.assertFalse(schedule.enabled)


if __name__ == "__main__":
    unittest.main()
