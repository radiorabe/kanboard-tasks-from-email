import pytest

from src.tasks_from_email import reopen_and_update


class TestReopenAndUpdate:
    @pytest.mark.parametrize(
        ("kb_task", "open_called"),
        [
            ({"is_active": 1}, False),
            ({"is_active": 0}, True),
        ],
    )
    def test_call_open_task(self, kb, kb_task, open_called):
        reopen_and_update(kb, kb_task, 956, None, None, None)
        if open_called:
            kb.open_task.assert_called_with(task_id=956)
        else:
            assert not kb.open_task.called

    def test_call_create_comment_with_args(self, kb):
        reopen_and_update(kb, {"is_active": 1}, 956, 0, "text", None)
        kb.create_comment.assert_called_with(task_id=956, user_id=0, content="text")

    def test_call_update_task_with_args(self, kb):
        reopen_and_update(kb, {"is_active": 1}, 956, None, None, "20.11.1995 12:00")
        kb.update_task.assert_called_with(id=956, date_due="20.11.1995 12:00")
