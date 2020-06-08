import pytest

import imaplib

from tasks_from_email import imap_connect, imap_close, imap_search_unseen

class TestImapFunctions:
    def test_imap_connect(self, mocker):
        mocker.patch('imaplib.IMAP4_SSL')

        connection = mocker.Mock()
        imaplib.IMAP4_SSL.return_value = connection

        imap_connection = imap_connect('servername', 'username', 'password')

        imaplib.IMAP4_SSL.assert_called_once_with('servername')
        assert imap_connection == connection

    def test_imap_close(self, mocker):
        imap_connection = mocker.Mock()

        imap_close(imap_connection)

        imap_connection.close.assert_called_once()
        imap_connection.logout.assert_called_once()

    def test_image_search_unseen(self, mocker):
        imap_connection = mocker.Mock()
        imap_connection.search.return_value = ('typ', 'data')

        typ, data = imap_search_unseen(imap_connection)

        imap_connection.select.assert_called_once_with('INBOX')
        imap_connection.search.assert_called_once_with(None, 'unseen')
        assert typ == 'typ'
        assert data == 'data'
