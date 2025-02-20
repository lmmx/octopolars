"""Retrieve and parse a GitHub user's repositories/files."""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl
import polars.selectors as cs  # noqa: F401
import polars_hopper  # noqa: F401
from github import Github
from platformdirs import user_cache_dir
from upath import UPath

from .auth import ENV_GH_TOKEN
from .exprs import prepare_expr


class Inventory:
    """Retrieve and parse a GitHub user's public repositories into a Polars DataFrame.

    Results are cached locally to avoid repeated API calls.
    """

    def __init__(
        self,
        username: str,
        lazy: bool = False,
        token: str | None = None,
        use_cache: bool = True,
        force_refresh: bool = False,
        filter_exprs: tuple[str, ...] | tuple[pl.Expr, ...] = None,
        select_exprs: tuple[str, ...] | tuple[pl.Expr, ...] = None,
        addcols_exprs: tuple[str, ...] | tuple[pl.Expr, ...] = None,
        show_tbl_cols: int | None = None,
        show_tbl_rows: int | None = None,
    ) -> None:
        """Initialise the Inventory object.

        Args:
        ----
            username: The GitHub username to fetch repositories for.
            lazy: Whether to allow lazy Polars operations (not all transformations may be supported).
            token: An optional GitHub personal access token for higher rate limits.
            use_cache: Whether to use cached results if available.
            force_refresh: If True, always refetch from GitHub and overwrite the cache.
            filter_exprs: One or more Polars schema (column) names to filter (where True),
                          or an Expr to filter the repository listing or file walk tree.
            select_exprs: One or more Polars schema (column) names to select, or an
                          Expr to evaluate for the repository listing or file walk tree.
            addcols_exprs: One or more Polars schema (column) names to with_columns, or an
                           Expr to evaluate for the repository listing or file walk tree.
            show_tbl_cols: Configure Polars to print N columns if `int` (default: None).
            show_tbl_rows: Configure Polars to print N rows if `int` (default: None).

        """
        self.username = username
        self.lazy = lazy
        self.token = token if token is not None else ENV_GH_TOKEN
        self.use_cache = use_cache
        self.force_refresh = force_refresh
        self.filter_exprs = tuple(map(prepare_expr, filter_exprs or []))
        self.select_exprs = tuple(map(prepare_expr, select_exprs or []))
        self.addcols_exprs = tuple(map(prepare_expr, addcols_exprs or []))
        self._inventory_df: pl.DataFrame | None = None

        # Initialize the cache location
        self._cache_dir = Path(user_cache_dir(appname="octopols"))
        self._cache_dir.mkdir(exist_ok=True)
        self._cache_file = self._cache_dir / f"{username}_repos.json"
        self._cfg = pl.Config()
        if show_tbl_cols is not None:
            self._cfg.set_tbl_cols(show_tbl_cols)
        if show_tbl_rows is not None:
            self._cfg.set_tbl_rows(show_tbl_rows)

    def list_repos(self) -> pl.DataFrame:
        """Fetch and parse the public repositories for the specified GitHub user.

        Checks the local cache first (unless force_refresh=True). Returns a Polars DataFrame
        with the columns 'name', 'html_url', and 'description'.
        """
        self._inventory_df = self._retrieve_repos()
        return self._inventory_df

    def review_version_changes(
        self,
        from_v: str = "first",
        to_v: str = "latest",
    ) -> pl.DataFrame:
        """Compare repository metadata across two versions (placeholder).

        Currently returns a trivial DataFrame.
        """
        return pl.DataFrame({"from_v": [from_v], "to_v": [to_v]})

    def _retrieve_repos(self) -> pl.DataFrame:
        """Try to use cached results if use_cache=True (and not force_refresh).

        Otherwise, fetch from GitHub and cache the JSON if successful.
        """
        if self.use_cache and not self.force_refresh:
            cached_data = self._read_cache()
            if cached_data is not None:
                repos = cached_data
            else:
                repos = self._fetch_from_github()
                self._write_cache(repos)
        else:
            try:
                repos = self._fetch_from_github()
                self._write_cache(repos)
            except Exception as e:
                cached_data = self._read_cache()
                if cached_data is not None:
                    print(f"GitHub fetch failed ({e}), returning cached data.")
                    repos = cached_data
                else:
                    raise

        repos.hopper.add_filters(*self.filter_exprs)
        repos.hopper.add_selects(*self.select_exprs)
        repos.hopper.add_addcols(*self.addcols_exprs)
        repos = repos.hopper.apply_ready_exprs()
        self.filter_exprs = tuple(repos.hopper.list_filters())
        self.select_exprs = tuple(repos.hopper.list_selects())
        self.addcols_exprs = tuple(repos.hopper.list_addcols())
        return repos

    def _fetch_from_github(self) -> pl.DataFrame:
        """Use PyGithub to retrieve the user's public repositories.

        Returns a Polars DataFrame with repo information.
        """
        gh = Github(self.token) if self.token else Github()
        gh.per_page = 100
        user = gh.get_user(self.username)
        repos = user.get_repos()

        data = [
            {
                "name": repo.name,
                "default_branch": repo.default_branch,
                "description": repo.description or "",
                "archived": repo.archived,
                "is_fork": repo.fork,
                "issues": repo.open_issues,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "size": repo.size,
            }
            for repo in repos
        ]
        df = pl.DataFrame(
            data,
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
        return df.lazy().collect() if self.lazy else df

    def _read_cache(self) -> pl.DataFrame | None:
        """Read previously cached JSON data from disk.

        Returns None if no file or if something fails to load.
        """
        if not self._cache_file.is_file():
            return None
        try:
            return pl.read_ndjson(self._cache_file)
        except OSError:
            return None

    def _write_cache(self, data: pl.DataFrame) -> None:
        """Write JSON data to the cache file."""
        try:
            data.write_ndjson(self._cache_file)
        except OSError as e:
            print(f"Failed to write to cache: {e}")

    def walk_file_trees(
        self,
        pattern: str = "**",
        no_recurse: bool = False,
        skip_larger_than_mb: int | None = None,
    ) -> pl.DataFrame:
        """Walk (recursively enumerate) files in each repository via UPath.

        Discovers (but does not read) file paths that match a given glob pattern.

        Args:
        ----
            pattern: Glob pattern for file listing. By default "**" (recursive).
            no_recurse: If True, uses "*" (non-recursive) instead of the default "**".
            skip_larger_than_mb: If set, skip listing files larger than this many MB.
                                 By default, None (don't skip based on size).

        Returns:
        -------
            A Polars DataFrame with columns:
                - "repository_name": str
                - "file_path": str
                - "is_directory": bool
                - "file_size_bytes": int

        """
        if self._inventory_df is None:
            self.list_repos()
        if no_recurse:
            pattern = "*"
        records = []
        for row in self._inventory_df.to_dicts():
            repo_name = row["name"]
            default_branch = row["default_branch"]
            ghpath = UPath(
                "/",
                protocol="github",
                org=self.username,
                repo=repo_name,
                sha=default_branch,
                username=self.username,
                token=self.token,
            )
            for p in ghpath.glob(pattern):
                if is_dir := p.is_dir():
                    file_size_bytes = 0
                else:
                    file_size_bytes = p.stat().st_size
                    if skip_larger_than_mb is not None:
                        threshold_bytes = skip_larger_than_mb * 1_048_576
                        if file_size_bytes > threshold_bytes:
                            continue
                records.append(
                    {
                        "repository_name": repo_name,
                        "file_path": os.path.join(*p.parts),
                        "is_directory": is_dir,
                        "file_size_bytes": file_size_bytes,
                    },
                )
        files = pl.DataFrame(
            records,
            schema={
                "repository_name": pl.String,
                "file_path": pl.String,
                "is_directory": pl.Boolean,
                "file_size_bytes": pl.Int64,
            },
        )
        files.hopper.add_filters(*self.filter_exprs)
        files.hopper.add_selects(*self.select_exprs)
        files.hopper.add_addcols(*self.addcols_exprs)
        files = files.hopper.apply_ready_exprs()
        self.filter_exprs = tuple(files.hopper.list_filters())
        self.select_exprs = tuple(files.hopper.list_selects())
        self.addcols_exprs = tuple(files.hopper.list_addcols())
        return files

    def read_files(
        self,
        pattern: str = "**",
        no_recurse: bool = False,
        skip_larger_than_mb: int | None = None,
    ) -> pl.DataFrame:
        """Read *all* file contents in each matched repository path.

        This enumerates all files (via walk_file_trees) that match `pattern`,
        then reads their text content if they are not directories.

        Args:
        ----
            pattern: Glob pattern for file listing. Default "**" means recursive.
            no_recurse: If True, uses "*" instead of "**".
            skip_larger_than_mb: Optional size limit in MB. If set, skip any file above it.

        Returns:
        -------
            A Polars DataFrame with columns:
                - "repository_name": str
                - "file_path": str
                - "file_size_bytes": int
                - "content": str (file content, or empty if directory/failed)

        """
        # First, get a listing
        file_tree = self.walk_file_trees(
            pattern=pattern,
            no_recurse=no_recurse,
            skip_larger_than_mb=skip_larger_than_mb,
        )
        if file_tree.is_empty():
            return file_tree

        # We'll accumulate a new DataFrame with the file content
        rows = []
        for row in file_tree.to_dicts():
            if row["is_directory"]:
                # Skip directories; no content to read
                rows.append(
                    {
                        "repository_name": row["repository_name"],
                        "file_path": row["file_path"],
                        "file_size_bytes": row["file_size_bytes"],
                        "content": "",
                    },
                )
                continue

            repo_name = row["repository_name"]
            file_path = row["file_path"]
            # We'll look up the default branch from the known repos
            default_branch = (
                self._inventory_df.filter(pl.col("name") == repo_name)
                .select("default_branch")
                .item()
            )

            ghpath = UPath(
                "/",
                protocol="github",
                org=self.username,
                repo=repo_name,
                sha=default_branch,
                username=self.username,
                token=self.token,
            )
            p = ghpath / file_path
            try:
                content_str = p.read_text()
            except Exception:
                content_str = ""

            rows.append(
                {
                    "repository_name": repo_name,
                    "file_path": file_path,
                    "file_size_bytes": row["file_size_bytes"],
                    "content": content_str,
                },
            )
        return pl.DataFrame(rows)
