"""Shared pytest fixtures."""

import polars as pl
import pytest


@pytest.fixture
def mock_repos_data():
    """Return mock repository data for testing."""
    return [
        {
            "name": "project-alpha",
            "default_branch": "main",
            "description": "First project",
            "archived": False,
            "is_fork": False,
            "issues": 5,
            "stars": 100,
            "forks": 10,
            "size": 1024,
        },
        {
            "name": "demo-beta",
            "default_branch": "master",
            "description": "Demo project",
            "archived": False,
            "is_fork": True,
            "issues": 0,
            "stars": 5,
            "forks": 0,
            "size": 512,
        },
        {
            "name": "old-gamma",
            "default_branch": "main",
            "description": "Archived project",
            "archived": True,
            "is_fork": False,
            "issues": 0,
            "stars": 50,
            "forks": 5,
            "size": 2048,
        },
    ]


@pytest.fixture
def mock_repos_df(mock_repos_data):
    """Return a DataFrame from mock repository data."""
    return pl.DataFrame(
        mock_repos_data,
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
