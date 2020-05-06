import pytest
from freezegun import freeze_time

from tasks_from_email import convert_to_kb_date


class TestConvertToKbDate:
    @pytest.mark.parametrize(
        "date_str,expected",
        [
            ("Mon, 20 Nov 1995 19:12:08 -0500", "20.11.1995 19:12"),
            ("20 Nov 1995 7:12 PM", "20.11.1995 19:12"),
            ("20 Nov 1995 0:00 +0000", "20.11.1995 00:00"),
        ],
    )
    @freeze_time("2012-01-14 03:21:34", tz_offset=0)
    def test_date_str_calls(self, date_str, expected):
        result = convert_to_kb_date(date_str)
        assert result == expected

    @pytest.mark.parametrize(
        "increment,expected",
        [
            (0, "20.11.1995 19:12"),
            (1, "20.11.1995 20:12"),
            # rollover to the next day
            (5, "21.11.1995 00:12"),
            # negative numbers are ignored like 0
            (-1, "20.11.1995 19:12"),
        ],
    )
    @freeze_time("2012-01-14 03:21:34", tz_offset=0)
    def test_increment_by_hours(self, increment, expected):
        result = convert_to_kb_date(
            "Mon, 20 Nov 1995 19:12:08 -0500", increment_by_hours=increment
        )
        assert result == expected
