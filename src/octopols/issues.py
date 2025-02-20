"""Retrieve and parse GitHub issues for a given user's repository."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import polars as pl
from github import Github
from platformdirs import user_cache_dir

from .auth import ENV_GH_TOKEN
from .exprs import prepare_expr


class IssuesInventory:
    """Retrieve and parse a single GitHub repository’s Issues into a Polars DataFrame.

    Provides optional Polars expression filters, selections, and addcols (DSL or native).

    Usage Example:
    -------------
        inv = IssuesInventory("octocat", "Spoon-Knife", filter_exprs=["{state} == 'open'"])
        df = inv.list_issues()
        print(df)
    """

    def __init__(
        self,
        username: str,
        repo_name: str,
        lazy: bool = False,
        token: str | None = None,
        use_cache: bool = True,
        force_refresh: bool = False,
        state: Literal["open", "closed", "all"] = "open",
        filter_exprs: tuple[str | pl.Expr, ...] = None,
        select_exprs: tuple[str | pl.Expr, ...] = None,
        addcols_exprs: tuple[str | pl.Expr, ...] = None,
        show_tbl_cols: int | None = None,
        show_tbl_rows: int | None = None,
    ) -> None:
        """Inventory of GitHub issues.

        username: GitHub username/org name.
        repo_name: Name of the GitHub repository.
        lazy: Whether to allow lazy Polars operations (applies to final DataFrame).
        token: A GitHub token for higher rate limits.
        use_cache: If True, use local cache before hitting GitHub.
        force_refresh: If True, skip cache and refetch from GitHub.
        state: Whether to get "open" issues (default), "closed", or both ("all").
        filter_exprs: Polars expressions (str DSL or pl.Expr) to filter issues by.
        select_exprs: Polars expressions (str DSL or pl.Expr) to select columns.
        addcols_exprs: Polars expressions (str DSL or pl.Expr) to add computed columns.
        show_tbl_cols: If set, configure Polars to print up to N columns.
        show_tbl_rows: If set, configure Polars to print up to N rows.

        """
        self.username = username
        self.repo_name = repo_name
        self.lazy = lazy
        self.token = token if token is not None else ENV_GH_TOKEN
        self.use_cache = use_cache
        self.force_refresh = force_refresh
        self.state = state

        # Convert all DSL or Expr inputs into Polars Expr
        self.filter_exprs = tuple(map(prepare_expr, filter_exprs or []))
        self.select_exprs = tuple(map(prepare_expr, select_exprs or []))
        self.addcols_exprs = tuple(map(prepare_expr, addcols_exprs or []))

        self._issues_df: pl.DataFrame | None = None

        self._cache_dir = Path(user_cache_dir(appname="octopols.issues"))
        self._cache_dir.mkdir(exist_ok=True)
        # e.g. "octocat_Spoon-Knife_issues.json"
        self._cache_file = self._cache_dir / f"{username}_{repo_name}.json"

        self._cfg = pl.Config()
        if show_tbl_cols is not None:
            self._cfg.set_tbl_cols(show_tbl_cols)
        if show_tbl_rows is not None:
            self._cfg.set_tbl_rows(show_tbl_rows)

    def list_issues(self) -> pl.DataFrame:
        """Fetch (and possibly cache) all issues from the given repository.

        Apply any filter/select/addcols expressions. Return a Polars DataFrame.

        If `use_cache` is True, tries reading from the local cache unless `force_refresh`.
        If GitHub fetch fails, falls back to cache if available.
        """
        if self._issues_df is not None:
            return self._issues_df

        self._issues_df = self._retrieve_issues()
        return self._issues_df

    def _retrieve_issues(self) -> pl.DataFrame:
        """Load issues from cache or GitHub API, then apply Polars expressions."""
        if self.use_cache and not self.force_refresh:
            cached = self._read_cache()
            if cached is not None:
                df = cached
            else:
                df = self._fetch_issues_from_github()
                self._write_cache(df)
        else:
            try:
                df = self._fetch_issues_from_github()
                self._write_cache(df)
            except Exception as exc:
                cached = self._read_cache()
                if cached is not None:
                    print(
                        f"Warning: GitHub fetch failed ({exc}), returning cached data.",
                    )
                    df = cached
                else:
                    raise

        # Apply any DSL-based filters, selects, addcols via polars-hopper
        df.hopper.add_filters(*self.filter_exprs)
        df.hopper.add_selects(*self.select_exprs)
        df.hopper.add_addcols(*self.addcols_exprs)
        df = df.hopper.apply_ready_exprs()

        # Store final expressions that got applied
        self.filter_exprs = tuple(df.hopper.list_filters())
        self.select_exprs = tuple(df.hopper.list_selects())
        self.addcols_exprs = tuple(df.hopper.list_addcols())

        return df

    def _fetch_issues_from_github(self) -> pl.DataFrame:
        """Retrieve issues for the repo `username/repo_name` from GitHub.

        Returns a Polars DataFrame with columns like:
            'number', 'title', 'state', 'comments', 'created_at', 'updated_at', etc.
        """
        gh = Github(self.token) if self.token else Github()
        gh.per_page = 100
        repo = gh.get_user(self.username).get_repo(self.repo_name)

        data = []
        for issue in repo.get_issues(state=self.state):
            data.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "comments": issue.comments,
                    "created_at": issue.created_at.isoformat()
                    if issue.created_at
                    else None,
                    "updated_at": issue.updated_at.isoformat()
                    if issue.updated_at
                    else None,
                    "author": issue.user.login if issue.user else None,
                    "labels": [lbl.name for lbl in issue.labels],
                    "body": issue.body or "",
                },
            )

        df = pl.DataFrame(
            data,
            schema={
                "number": pl.Int64,
                "title": pl.String,
                "state": pl.String,
                "comments": pl.Int64,
                "created_at": pl.String,
                "updated_at": pl.String,
                "author": pl.String,
                "labels": pl.List(pl.String),
                "body": pl.String,
            },
        ).with_columns(
            pl.col("created_at").cast(pl.Datetime),
            pl.col("updated_at").cast(pl.Datetime),
        )
        if self.lazy:
            return df.lazy().collect()
        else:
            return df

    def _read_cache(self) -> pl.DataFrame | None:
        """Read previously cached data from disk (NDJSON)."""
        if not self._cache_file.is_file():
            return None
        try:
            return pl.read_ndjson(self._cache_file)
        except OSError:
            return None

    def _write_cache(self, data: pl.DataFrame) -> None:
        """Write NDJSON data to the cache file."""
        try:
            data.write_ndjson(self._cache_file)
        except OSError as e:
            print(f"Failed to write to cache: {e}")
