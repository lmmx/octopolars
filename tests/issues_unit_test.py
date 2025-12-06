"""Unit tests for IssuesInventory class methods that don't require GitHub."""

import polars as pl
import pytest

from octopols.issues import IssuesInventory


class TestIssuesInventoryInit:
    """Test IssuesInventory initialization."""

    def test_default_initialization(self):
        """Verify default initialization sets expected values."""
        inv = IssuesInventory(username="testuser", repo_name="testrepo")
        assert inv.username == "testuser"
        assert inv.repo_name == "testrepo"
        assert inv.state == "open"
        assert inv.use_cache is True

    def test_with_state_all(self):
        """Verify state can be set to 'all'."""
        inv = IssuesInventory(username="testuser", repo_name="testrepo", state="all")
        assert inv.state == "all"

    def test_with_filter_exprs(self):
        """Verify filter expressions are parsed correctly."""
        inv = IssuesInventory(
            username="testuser",
            repo_name="testrepo",
            filter_exprs=('{state} == "open"',),
        )
        assert len(inv.filter_exprs) == 1


class TestIssuesInventoryCaching:
    """Test IssuesInventory cache operations."""

    @pytest.fixture
    def temp_issues_inventory(self, tmp_path):
        """Create an IssuesInventory with a temporary cache directory."""
        inv = IssuesInventory(username="testuser", repo_name="testrepo")
        inv._cache_dir = tmp_path
        inv._cache_file = tmp_path / "testuser_testrepo.json"
        return inv

    @pytest.fixture
    def sample_issues_df(self):
        """Return a sample issues DataFrame for cache testing."""
        return pl.DataFrame(
            {
                "number": [1, 2],
                "title": ["Issue 1", "Issue 2"],
                "state": ["open", "closed"],
                "comments": [0, 5],
                "created_at": ["2024-01-01T00:00:00", "2024-01-02T00:00:00"],
                "updated_at": ["2024-01-01T00:00:00", "2024-01-03T00:00:00"],
                "author": ["alice", "bob"],
                "labels": [["bug"], ["feature"]],
                "body": ["Body 1", "Body 2"],
            },
        )

    def test_write_and_read_cache(self, temp_issues_inventory, sample_issues_df):
        """Verify cache write and read round-trips correctly."""
        temp_issues_inventory._write_cache(sample_issues_df)
        assert temp_issues_inventory._cache_file.exists()

        cached = temp_issues_inventory._read_cache()
        assert cached is not None
        assert cached["number"].to_list() == [1, 2]

    def test_read_nonexistent_cache(self, temp_issues_inventory):
        """Verify reading nonexistent cache returns None."""
        result = temp_issues_inventory._read_cache()
        assert result is None
