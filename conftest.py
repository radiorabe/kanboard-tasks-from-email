"""Contains global fixtures for pytest"""
from os import environ

import pytest
import kanboard
from email.message import EmailMessage

environ['IMAPS_SERVER'] = 'imap.example.org'
environ['IMAPS_USERNAME'] = 'imaps-user'
environ['IMAPS_PASSWORD'] = 'imaps-pass'

environ['KANBOARD_CONNECT_URL'] = 'https://kanboard.example.org'
environ['KANBOARD_API_TOKEN'] = 'l33tT0k3n'

@pytest.fixture
def kb(mocker):
    """
    A mock of the kanboard client.

    This mock is used by various tests and can be extended with more methods should they be needed.
    """
    kb = mocker.Mock(kanboard.Client)
    kb.add_group_member = mocker.Mock()
    kb.create_comment = mocker.Mock()
    kb.create_task = mocker.Mock()
    kb.create_task_file = mocker.Mock()
    kb.create_user = mocker.Mock()
    kb.get_all_users = mocker.Mock()
    kb.get_project_by_name = mocker.Mock()
    kb.get_task = mocker.Mock()
    kb.open_task = mocker.Mock()
    kb.update_task = mocker.Mock()
    return kb

@pytest.fixture
def email_message(mocker):
    """
    Mock an email.message.EmailMessage object
    """
    mail = mocker.MagicMock(EmailMessage)
    mail.walk.return_value = []
    return mail
