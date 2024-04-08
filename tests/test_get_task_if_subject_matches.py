import pytest

from src.tasks_from_email import get_task_if_subject_matches


class TestGetTaskIfSubjectMatches:
    def test_call_with_unknown_subject(self, kb):
        result = get_task_if_subject_matches(kb, "unknown")
        assert result == (False, None)

    @pytest.mark.parametrize(
        ("subject", "expected"),
        [
            ("[KB#956]", ("956", {})),
            ("[KB#956] as prefix", ("956", {})),
            ("as suffix [KB#956]", ("956", {})),
            ("as [KB#956] affix", ("956", {})),
            ("[KB#12345678901234567890] ridiculous", ("12345678901234567890", {})),
            ("[KB#000] ridiculous", ("000", {})),
        ],
    )
    def test_call_with_known_subjects(self, kb, subject, expected):
        kb.get_task.return_value = expected[1]
        result = get_task_if_subject_matches(kb, subject)
        assert result == expected
        kb.get_task.assert_called_with(task_id=expected[0])
