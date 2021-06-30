from modules.util import conversion

import unittest


class TestFloatToHMS(unittest.TestCase):

    def setUp(self):
        self.secondsPerDay = 86400

    def test_zero(self):
        assert conversion.floatToHMS(0.0) == "0:00:00"

    def test_positive(self):
        assert conversion.floatToHMS(60.0) == "0:01:00"

    def test_negative(self):
        try:
            conversion.floatToHMS(-60.0)
        except ValueError as e:
            assert str(e) == "Duration must be non-negative"

    def test_big(self):
        assert conversion.floatToHMS(self.secondsPerDay-1) == "23:59:59"

    def test_hour_3_digits(self):
        secondsIn100Hours = 360000
        assert conversion.floatToHMS(secondsIn100Hours) == "100:00:00"
