"""Tests for CLI validation functions."""

import pytest

from octopols.cli import validate_issue_state


class TestValidateIssueState:
    """Test the issue state validator."""

    def test_valid_open(self):
        """Verify 'open' is accepted as a valid state."""
        result = validate_issue_state(None, None, "open")
        assert result == "open"

    def test_valid_closed(self):
        """Verify 'closed' is accepted as a valid state."""
        result = validate_issue_state(None, None, "closed")
        assert result == "closed"

    def test_valid_all(self):
        """Verify 'all' is accepted as a valid state."""
        result = validate_issue_state(None, None, "all")
        assert result == "all"

    def test_invalid_state(self):
        """Verify invalid states raise BadParameter."""
        from click import BadParameter

        with pytest.raises(BadParameter):
            validate_issue_state(None, None, "invalid")
