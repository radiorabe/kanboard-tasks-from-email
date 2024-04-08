"""Contains global fixtures for pytest."""

from email.message import EmailMessage
from os import environ
from unittest.mock import MagicMock, Mock

import kanboard
import pytest

environ["IMAPS_SERVER"] = "imap.example.org"
environ["IMAPS_USERNAME"] = "imaps-user"
environ["IMAPS_PASSWORD"] = "imaps-pass"

environ["KANBOARD_CONNECT_URL"] = "https://kanboard.example.org"
environ["KANBOARD_API_TOKEN"] = "l33tT0k3n"


@pytest.fixture()
def kb() -> kanboard.Client:
    """Mock the kanboard client.

    This mock is used by various tests and can be extended with more methods should they
    be needed.
    """
    kb = Mock(kanboard.Client)
    kb.add_group_member = Mock()
    kb.create_comment = Mock()
    kb.create_task = Mock()
    kb.create_task_file = Mock()
    kb.create_user = Mock()
    kb.get_all_users = Mock()
    kb.get_project_by_name = Mock()
    kb.get_task = Mock()
    kb.open_task = Mock()
    kb.update_task = Mock()
    return kb


@pytest.fixture()
def email_message() -> EmailMessage:
    """Mock an email.message.EmailMessage object."""
    mail = MagicMock(EmailMessage)
    mail.walk.return_value = []
    return mail
