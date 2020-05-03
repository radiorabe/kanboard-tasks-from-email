import pytest

from tasks_from_email import create_user_for_sender


class TestCreateUserForSender:
    _EMAIL = "username@example.org"

    def test_call_with_no_users(self, kb):
        kb.get_all_users.return_value = []

        result = create_user_for_sender(kb, self._EMAIL)
        kb.create_user.assert_called_with(
            username=self._EMAIL, password=self._EMAIL, email=self._EMAIL
        )

    def test_call_with_no_matching_users(self, kb):
        kb.get_all_users.return_value = [
            {"id": 103, "email": "otheruser@example.org"},
        ]
        kb.create_user.return_value = 956

        result = create_user_for_sender(kb, self._EMAIL)
        assert result == 956
        kb.create_user.assert_called_with(
            username=self._EMAIL, password=self._EMAIL, email=self._EMAIL
        )

    def test_call_with_matching_user(self, kb):
        kb.get_all_users.return_value = [
            {"id": 956, "email": self._EMAIL},
        ]

        result = create_user_for_sender(kb, self._EMAIL)
        assert result == 956
        assert not kb.create_user.called
