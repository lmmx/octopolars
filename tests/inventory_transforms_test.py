"""Tests for Inventory data transformations (no GitHub API calls)."""

import polars as pl
import pytest

from octopols.exprs import prepare_expr


class TestRepoDataTransforms:
    """Test transformations on repo-like DataFrames."""

    @pytest.fixture
    def repos_df(self):
        """Return a DataFrame mimicking _fetch_from_github output."""
        return pl.DataFrame(
            {
                "name": ["octopolars", "demo-app", "d3-charts", "archived-proj"],
                "default_branch": ["main", "master", "main", "master"],
                "description": [
                    "GitHub repo tool",
                    "A demo application",
                    "D3 visualizations",
                    "Old project",
                ],
                "archived": [False, False, False, True],
                "is_fork": [False, True, False, False],
                "issues": [5, 0, 12, 0],
                "stars": [100, 3, 50, 1],
                "forks": [10, 0, 5, 0],
                "size": [1024, 512, 2048, 256],
            },
            schema={
                "name": pl.Utf8,
                "default_branch": pl.String,
                "description": pl.String,
                "archived": pl.Boolean,
                "is_fork": pl.Boolean,
                "issues": pl.Int64,
                "stars": pl.Int64,
                "forks": pl.Int64,
                "size": pl.Int64,
            },
        )

    def test_filter_by_name_prefix(self, repos_df):
        """Verify filtering by name prefix works correctly."""
        expr = prepare_expr('{name}.str.starts_with("d")')
        result = repos_df.filter(expr)
        assert len(result) == 2
        assert set(result["name"].to_list()) == {"demo-app", "d3-charts"}

    def test_filter_by_stars_threshold(self, repos_df):
        """Verify filtering by stars threshold works correctly."""
        expr = prepare_expr("{stars} > 10")
        result = repos_df.filter(expr)
        assert result["name"].to_list() == ["octopolars", "d3-charts"]

    def test_filter_non_archived(self, repos_df):
        """Verify filtering out archived repos works correctly."""
        expr = prepare_expr("{archived} == False")
        result = repos_df.filter(expr)
        assert len(result) == 3
        assert "archived-proj" not in result["name"].to_list()

    def test_filter_non_forks(self, repos_df):
        """Verify filtering out forks works correctly."""
        expr = prepare_expr("{is_fork} == False")
        result = repos_df.filter(expr)
        assert "demo-app" not in result["name"].to_list()

    def test_select_subset_columns(self, repos_df):
        """Verify selecting a subset of columns works correctly."""
        expr = prepare_expr('pl.col("name", "stars")')
        result = repos_df.select(expr)
        assert result.columns == ["name", "stars"]

    def test_sort_by_stars_descending(self, repos_df):
        """Verify sorting by stars descending works correctly."""
        expr = prepare_expr('pl.all().sort_by("stars", descending=True)')
        result = repos_df.select(expr)
        assert result["name"].to_list() == [
            "octopolars",
            "d3-charts",
            "demo-app",
            "archived-proj",
        ]

    def test_add_computed_column(self, repos_df):
        """Verify adding a computed column works correctly."""
        expr = prepare_expr('{description}.str.contains("D3").alias("has_d3")')
        result = repos_df.with_columns(expr)
        assert "has_d3" in result.columns
        assert result.filter(pl.col("has_d3"))["name"].to_list() == ["d3-charts"]

    def test_chained_filters(self, repos_df):
        """Verify chaining multiple filters works correctly."""
        filters = [
            prepare_expr("{stars} > 5"),
            prepare_expr("{archived} == False"),
        ]
        result = repos_df
        for f in filters:
            result = result.filter(f)
        assert result["name"].to_list() == ["octopolars", "d3-charts"]


class TestFileTreeDataTransforms:
    """Test transformations on file-tree-like DataFrames."""

    @pytest.fixture
    def files_df(self):
        """Return a DataFrame mimicking walk_file_trees output."""
        return pl.DataFrame(
            {
                "repository_name": ["myrepo"] * 6,
                "file_path": [
                    ".github",
                    ".github/workflows",
                    ".github/workflows/ci.yml",
                    "src",
                    "src/main.py",
                    "README.md",
                ],
                "is_directory": [True, True, False, True, False, False],
                "file_size_bytes": [0, 0, 1024, 0, 2048, 512],
            },
            schema={
                "repository_name": pl.String,
                "file_path": pl.String,
                "is_directory": pl.Boolean,
                "file_size_bytes": pl.Int64,
            },
        )

    def test_filter_files_only(self, files_df):
        """Verify filtering to files only works correctly."""
        expr = prepare_expr("{is_directory} == False")
        result = files_df.filter(expr)
        assert len(result) == 3
        assert all(not d for d in result["is_directory"].to_list())

    def test_filter_by_extension(self, files_df):
        """Verify filtering by file extension works correctly."""
        expr = prepare_expr('{file_path}.str.ends_with(".py")')
        result = files_df.filter(expr)
        assert result["file_path"].to_list() == ["src/main.py"]

    def test_filter_by_path_contains(self, files_df):
        """Verify filtering by path substring works correctly."""
        expr = prepare_expr('{file_path}.str.contains("github")')
        result = files_df.filter(expr)
        assert len(result) == 3

    def test_filter_by_size(self, files_df):
        """Verify filtering by file size works correctly."""
        expr = prepare_expr("{file_size_bytes} > 1000")
        result = files_df.filter(expr)
        assert set(result["file_path"].to_list()) == {
            ".github/workflows/ci.yml",
            "src/main.py",
        }


class TestIssuesDataTransforms:
    """Test transformations on issues-like DataFrames."""

    @pytest.fixture
    def issues_df(self):
        """Return a DataFrame mimicking IssuesInventory output."""
        return pl.DataFrame(
            {
                "number": [1, 2, 3, 4],
                "title": [
                    "Bug: crash on startup",
                    "Feature: add dark mode",
                    "Bug: memory leak",
                    "Docs: update README",
                ],
                "state": ["open", "open", "closed", "open"],
                "comments": [5, 2, 10, 0],
                "author": ["alice", "bob", "alice", "charlie"],
                "labels": [
                    ["bug"],
                    ["enhancement"],
                    ["bug", "fixed"],
                    ["documentation"],
                ],
                "body": [
                    "App crashes when foo",
                    "Please add dark mode support",
                    "Memory grows unbounded",
                    "README needs updating",
                ],
            },
            schema={
                "number": pl.Int64,
                "title": pl.String,
                "state": pl.String,
                "comments": pl.Int64,
                "author": pl.String,
                "labels": pl.List(pl.String),
                "body": pl.String,
            },
        )

    def test_filter_open_issues(self, issues_df):
        """Verify filtering to open issues works correctly."""
        expr = prepare_expr('{state} == "open"')
        result = issues_df.filter(expr)
        assert len(result) == 3

    def test_filter_by_title_prefix(self, issues_df):
        """Verify filtering by title prefix works correctly."""
        expr = prepare_expr('{title}.str.starts_with("Bug")')
        result = issues_df.filter(expr)
        assert len(result) == 2

    def test_filter_by_author(self, issues_df):
        """Verify filtering by author works correctly."""
        expr = prepare_expr('{author} == "alice"')
        result = issues_df.filter(expr)
        assert result["number"].to_list() == [1, 3]

    def test_filter_by_comment_count(self, issues_df):
        """Verify filtering by comment count works correctly."""
        expr = prepare_expr("{comments} >= 5")
        result = issues_df.filter(expr)
        assert result["number"].to_list() == [1, 3]

    def test_add_keyword_match_column(self, issues_df):
        """Verify adding a keyword match column works correctly."""
        expr = prepare_expr('{body}.str.contains("foo").alias("mentions_foo")')
        result = issues_df.with_columns(expr)
        assert result.filter(pl.col("mentions_foo"))["number"].to_list() == [1]

    def test_count_matches_in_body(self, issues_df):
        """Verify counting matches in body works correctly."""
        expr = prepare_expr('{body}.str.count_matches("a").alias("a_count")')
        result = issues_df.with_columns(expr)
        assert "a_count" in result.columns
        assert result.filter(pl.col("number") == 1)["a_count"].item() == 1
