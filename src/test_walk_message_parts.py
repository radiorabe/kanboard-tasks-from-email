
import pytest

from email import header

from tasks_from_email import walk_message_parts


class TestWalkMessageParts:
    def test_empty_message(self, email_message):
        body, attachments = walk_message_parts(email_message)

        email_message.walk.assert_called_once()
        assert body == None
        assert attachments == {}

    def test_call_with_multipart_maintype(self, email_message):
        email_message.walk.return_value = [email_message]
        email_message.get_content_maintype.return_value = 'multipart'

        body, _ = walk_message_parts(email_message)

        email_message.walk.assert_called_once()
        email_message.get_content_maintype.assert_called_once()
        assert body == None

    def test_call_with_text_plain(self, email_message):
        email_message.walk.return_value = [email_message]
        email_message.get_content_maintype.return_value = ''
        email_message.get.return_value = None
        email_message.get_content_type.return_value = 'text/plain'
        email_message.get_payload.return_value = b'example-body'

        body, _ = walk_message_parts(email_message)

        email_message.walk.assert_called_once()
        email_message.get_content_maintype.assert_called_once()
        email_message.get.assert_called_once_with('Content-Disposition')
        email_message.get_content_type.assert_called_once()
        email_message.get_payload.assert_called_once_with(decode=True)
        assert body == 'example-body'

    def test_call_multipart_email(self, mocker, email_message):
        mocker.patch('email.header.decode_header')
        mocker.patch('email.header.make_header')

        main_part = email_message
        email_message.walk.return_value = [email_message]
        email_message.get_content_maintype.return_value = ''
        email_message.get.return_value = 'not None'

        email_message.get_filename.return_value = b'filename.txt'
        email_message.get_payload.return_value = b'example-body'

        header.decode_header.return_value = 'decoded-header-filename'
       
        header.make_header.return_value = 'real-filename.txt'

        body, attachments = walk_message_parts(email_message)

        email_message.walk.assert_called_once()
        email_message.get_content_maintype.assert_called_once()
        email_message.get.assert_called_once_with('Content-Disposition')
        email_message.get_filename.assert_called_once()
        email_message.get_payload.assert_called_once_with(decode=True)
        assert body == 'None\n\n<< Attachment: real-filename.txt >>'
        assert attachments == {
                'real-filename.txt': b'ZXhhbXBsZS1ib2R5'
        }
