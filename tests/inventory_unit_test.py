"""Unit tests for Inventory class methods that don't require GitHub."""

import polars as pl
import pytest

from octopols.inventory import Inventory


class TestInventoryInit:
    """Test Inventory initialization and configuration."""

    def test_default_initialization(self):
        """Verify default initialization sets expected values."""
        inv = Inventory(username="testuser")
        assert inv.username == "testuser"
        assert inv.use_cache is True
        assert inv.force_refresh is False
        assert inv.filter_exprs == ()
        assert inv.select_exprs == ()
        assert inv.addcols_exprs == ()

    def test_with_filter_exprs_string(self):
        """Verify filter expressions are parsed from strings."""
        inv = Inventory(
            username="testuser",
            filter_exprs=('{name}.str.starts_with("a")',),
        )
        assert len(inv.filter_exprs) == 1
        assert isinstance(inv.filter_exprs[0], pl.Expr)

    def test_with_multiple_exprs(self):
        """Verify multiple expressions are parsed correctly."""
        inv = Inventory(
            username="testuser",
            filter_exprs=("{stars} > 5", "{archived} == False"),
            select_exprs=('pl.col("name", "stars")',),
        )
        assert len(inv.filter_exprs) == 2
        assert len(inv.select_exprs) == 1

    def test_cache_directory_created(self):
        """Verify cache directory is created on initialization."""
        inv = Inventory(username="testuser")
        assert inv._cache_dir.exists()


class TestInventoryCaching:
    """Test cache read/write functionality."""

    @pytest.fixture
    def temp_inventory(self, tmp_path):
        """Create an Inventory with a temporary cache directory."""
        inv = Inventory(username="cachetest")
        inv._cache_dir = tmp_path
        inv._cache_file = tmp_path / "cachetest_repos.json"
        return inv

    @pytest.fixture
    def sample_repos_df(self):
        """Return a sample repos DataFrame for cache testing."""
        return pl.DataFrame(
            {
                "name": ["repo1", "repo2"],
                "default_branch": ["main", "master"],
                "description": ["Desc 1", "Desc 2"],
                "archived": [False, True],
                "is_fork": [False, False],
                "issues": [1, 2],
                "stars": [10, 20],
                "forks": [1, 2],
                "size": [100, 200],
            },
        )

    def test_write_and_read_cache(self, temp_inventory, sample_repos_df):
        """Verify cache write and read round-trips correctly."""
        temp_inventory._write_cache(sample_repos_df)
        assert temp_inventory._cache_file.exists()

        cached = temp_inventory._read_cache()
        assert cached is not None
        assert cached.shape == sample_repos_df.shape
        assert cached["name"].to_list() == ["repo1", "repo2"]

    def test_read_cache_nonexistent(self, temp_inventory):
        """Verify reading nonexistent cache returns None."""
        result = temp_inventory._read_cache()
        assert result is None

    def test_read_cache_corrupted(self, temp_inventory):
        """Verify reading corrupted cache raises an exception."""
        temp_inventory._cache_file.write_text("not valid json")
        with pytest.raises(Exception):
            temp_inventory._read_cache()


class TestInventoryReviewVersionChanges:
    """Test the review_version_changes placeholder method."""

    def test_returns_dataframe(self):
        """Verify method returns a DataFrame with expected columns."""
        inv = Inventory(username="testuser")
        result = inv.review_version_changes()
        assert isinstance(result, pl.DataFrame)
        assert "from_v" in result.columns
        assert "to_v" in result.columns

    def test_custom_versions(self):
        """Verify custom version arguments are stored correctly."""
        inv = Inventory(username="testuser")
        result = inv.review_version_changes(from_v="v1.0", to_v="v2.0")
        assert result["from_v"].item() == "v1.0"
        assert result["to_v"].item() == "v2.0"
