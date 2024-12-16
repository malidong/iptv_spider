# -*- coding: utf-8 -*-
"""
# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package
"""
import unittest

from src.iptv_spider.m3u import M3U8


class TestM3U8(unittest.TestCase):
    """
    This class means to test all the functions in M3U8.
    """
    __slots__ = ("m",)

    def setUp(self):
        """
        Add an instance for test internally.
        :return:
        """
        self.m: M3U8 = M3U8(path="https://live.iptv365.org/live.m3u", regex_filter=r".*")

    def test_download_m3u8_file(self):
        """
        Test of M3U8.download_m3u8_file.
        :return:
        """
        trial_url = "https://live.iptv365.org/live.m3u"
        self.assertIsInstance(self.m.download_m3u8_file(url=trial_url), str)


if __name__ == '__main__':
    unittest.main()
