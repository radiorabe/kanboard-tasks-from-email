import pytest
from freezegun import freeze_time

from src.tasks_from_email import handle_well_known_forwarders

_EMAIL_FROM_FORWARDER = """
From: Forwarder <forwarder@example.org>
Subject: Example
To: staff@example.org
Date: Mon, 21 Nov 1995 19:12:08 -0500
"""
_EMAIL_TO_FORWARDER = """
From: Staff <staff@example.org>
Subject: Example
To: forwarder@example.org
Date: Mon, 21 Nov 1995 19:12:08 -0500
"""
_EMAIL_WITHOUT_FORWARDER = """
From: Staff <staff@example.org>
Subject: Example
To: user@example.org
Date: Mon, 21 Nov 1995 19:12:08 -0500
"""


class TestHandleWellKnownForwarders:
    def test_call_no_change(self):
        (
            email_address,
            start_date,
            due_date,
        ) = handle_well_known_forwarders(
            [], 0, "", "origin@example.org", "21.10.1995 21:17", "21.10.1995 21:17"
        )

        assert email_address == "origin@example.org"
        assert start_date == "21.10.1995 21:17"
        assert due_date == "21.10.1995 21:17"

    @pytest.mark.parametrize(
        ("body", "email", "expected"),
        [
            (_EMAIL_TO_FORWARDER, "user@example.org", "staff@example.org"),
            (_EMAIL_TO_FORWARDER, "anyone@example.org", "staff@example.org"),
            (_EMAIL_TO_FORWARDER, "staff@example.org", "staff@example.org"),
            (_EMAIL_FROM_FORWARDER, "user@example.org", "user@example.org"),
            (_EMAIL_FROM_FORWARDER, "anyone@example.org", "anyone@example.org"),
            (_EMAIL_FROM_FORWARDER, "staff@example.org", "staff@example.org"),
            (_EMAIL_WITHOUT_FORWARDER, "user@example.org", "user@example.org"),
            (_EMAIL_WITHOUT_FORWARDER, "anyone@example.org", "anyone@example.org"),
            (_EMAIL_WITHOUT_FORWARDER, "staff@example.org", "staff@example.org"),
        ],
    )
    def test_email_forward_from_body(self, body, email, expected):
        well_known = ["forwarder@example.org"]

        (
            email_address,
            start_date,
            due_date,
        ) = handle_well_known_forwarders(
            well_known, 0, body, email, "21.10.1995 21:17", "21.10.1995 21:17"
        )
        assert email_address == expected

    @pytest.mark.parametrize(
        ("offset", "start_expected", "due_expected"),
        [
            (0, "21.11.1995 19:12", "21.11.1995 19:12"),
            (1, "21.11.1995 19:12", "21.11.1995 20:12"),
            (5, "21.11.1995 19:12", "22.11.1995 00:12"),
        ],
    )
    @freeze_time("2012-01-14 03:21:34", tz_offset=0)
    def test_date_from_forward(self, offset, start_expected, due_expected):
        email = "staff@example.org"
        well_known = ["forwarder@example.org"]

        (
            email_address,
            start_date,
            due_date,
        ) = handle_well_known_forwarders(
            well_known,
            offset,
            _EMAIL_TO_FORWARDER,
            email,
            "21.10.1995 21:17",
            "21.10.1995 21:17",
        )
        assert start_date == start_expected
        assert due_date == due_expected
