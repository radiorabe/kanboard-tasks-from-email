import pytest

import email
import kanboard

import tasks_from_email


class TestMain:
    def test_call_no_results(self, mocker):
        mocker.patch("tasks_from_email.imap_connect")
        mocker.patch("tasks_from_email.imap_search_unseen")
        mocker.patch("tasks_from_email.imap_close")

        tasks_from_email.imap_search_unseen.return_value = ("typ", [""])

        tasks_from_email.main()

        tasks_from_email.imap_connect.assert_called_once()
        tasks_from_email.imap_search_unseen.assert_called_once()
        tasks_from_email.imap_close.assert_called_once()

    @pytest.mark.parametrize("create", [(True), (False)])
    def test_call_with_mocks(self, mocker, kb, email_message, create):
        mocker.patch("tasks_from_email.imap_connect")
        mocker.patch("tasks_from_email.imap_search_unseen")
        mocker.patch("tasks_from_email.imap_close")
        mocker.patch("tasks_from_email.convert_to_kb_date")
        mocker.patch("tasks_from_email.create_user_for_sender")
        mocker.patch("tasks_from_email.get_task_if_subject_matches")
        mocker.patch("tasks_from_email.reopen_and_update")
        mocker.patch("email.message_from_bytes")
        mocker.patch("email.header.make_header")
        mocker.patch("kanboard.Client")

        imap_connection = mocker.Mock()
        imap_connection.fetch.return_value = ("typ", [(None, b"raw")])
        tasks_from_email.imap_connect.return_value = imap_connection
        tasks_from_email.imap_search_unseen.return_value = ("typ", ["a"])
        email.message_from_bytes.return_value = email_message
        mock_data = {
            "Date": "rfcdate",
            "From": "from@example.org",
            "To": "to@example.org",
            "Subject": "subject",
        }

        def getitem(name):
            return mock_data[name]

        email_message.__getitem__.side_effect = getitem
        tasks_from_email.convert_to_kb_date.return_value = "converted-date"
        tasks_from_email.create_user_for_sender.return_value = 2
        kanboard.Client.return_value = kb
        kb.get_project_by_name.return_value = {"id": 1}
        if create:
            tasks_from_email.get_task_if_subject_matches.return_value = (None, None)
        else:
            tasks_from_email.get_task_if_subject_matches.return_value = (
                1,
                {"is_active": True},
            )
        email.header.make_header.return_value = "ExampleHeader"
        kb.create_task.return_value = 1

        tasks_from_email.main()

        tasks_from_email.imap_connect.assert_called_once()
        tasks_from_email.imap_search_unseen.assert_called_once()
        imap_connection.fetch.assert_called_once_with("a", "(RFC822)")
        email.message_from_bytes.assert_called_once_with(b"raw")
        tasks_from_email.convert_to_kb_date.assert_has_calls(
            [mocker.call("rfcdate"), mocker.call("rfcdate", 48)]
        )
        assert email_message.__getitem__.call_args_list == [
            mocker.call("Date"),
            mocker.call("Date"),
            mocker.call("From"),
            mocker.call("To"),
            mocker.call("Subject"),
        ]
        kanboard.Client.assert_called_once()
        tasks_from_email.create_user_for_sender.called_once_with(kb, "from@example.org")
        kb.add_group_member.assert_not_called()
        kb.get_project_by_name.assert_called_once_with(name="Support")
        tasks_from_email.get_task_if_subject_matches.assert_called_once_with(
            kb, "ExampleHeader"
        )
        if create:
            kb.create_task.assert_called_once_with(
                project_id="1",
                title="ExampleHeader",
                creator_id=2,
                date_started="converted-date",
                date_due="converted-date",
                description="From: from@example.org\n\nTo: to@example.org\n\nDate: converted-date\n\nSubject: ExampleHeader\n\nNone",
            )
            tasks_from_email.reopen_and_update.assert_not_called()
        else:
            kb.create_task.assert_not_called()
            tasks_from_email.reopen_and_update.called_once_with(
                kb, {"is_active": True}, 1, 2, "None", "converted-date"
            )
        kb.create_task_file.assert_called_once_with(
            project_id="1",
            task_id="1",
            filename="ExampleHeader.mbox",
            blob="cmF3",  # None
        )

        tasks_from_email.imap_close.assert_called_once()
