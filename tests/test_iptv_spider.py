# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest

from src.iptv_spider.m3u import M3U8


class TestM3U8(unittest.TestCase):
    __slots__ = "m"

    def __init__(self):
        self.m = M3U8(path="https://live.iptv365.org/live.m3u")
        super().__init__()

    def test_download_m3u8_file(self):
        trial_url = "https://live.iptv365.org/live.m3u"
        self.assertIsInstance(self.m.download_m3u8_file(url=trial_url), str)


if __name__ == '__main__':
    unittest.main()
