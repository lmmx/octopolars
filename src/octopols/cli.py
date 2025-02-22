"""Provides the `octopols` CLI command for Octopolars."""

from __future__ import annotations

import click

from .inventory import Inventory
from .issues import IssuesInventory


class DefaultCommandGroup(click.Group):
    """A custom Group class to provide a default command by argument parser override.

    - Checks if the user typed a known subcommand or a global option.
    - If not, it inserts 'repos' as the subcommand, so that "octopols lmmx"
      behaves like "octopols repos lmmx".
    """

    def parse_args(self, ctx, args):
        """Intervene to set repos as default command unless user gave no arguments."""
        if not args or ctx.resilient_parsing:
            return super().parse_args(ctx, args)

        # The first token after 'octopols'
        cmd_name = args[0]

        # Is this first token a recognized subcommand name or a global option like --help?
        recognized_subcommands = list(self.commands.keys())
        if cmd_name not in recognized_subcommands and not cmd_name.startswith("-"):
            # Not a known subcommand, so treat this token as if it were for 'repos'.
            # Insert "repos" at position 0; "lmmx" becomes the first argument to `repos`.
            args.insert(0, "repos")

        return super().parse_args(ctx, args)


@click.group(cls=DefaultCommandGroup)
def octopols():
    """GitHub CLI with 2 subcommands (see their help text for more information).

    If no subcommand is given, the `repos` command is called by default.
    """


@octopols.command(
    help="""
    Octopols - A CLI for listing GitHub repos or files by username, with filters.

    By default, this prints a table of repositories.

      The --walk/-w flag walks the files rather than just listing the repos.

      The --extract/-x flag reads all matching files (use with caution).

      The --filter/-f flag (1+ times) applies `filter` exprs, or f-string-like column DSL (e.g., '{name}.str.starts_with("a")').

      The --select/-s flag (1+ times) applies `select` exprs, or f-string-like column DSL (e.g., '{foo}.alias("bar")').

      The --addcols/-a flag (1+ times) applies `with_columns` exprs, or f-string-like column DSL (e.g., '{total} * 2').

      The --quiet/-q flag switches to a minimal, abridged view. By default, rows and cols are unlimited (-1).

    \b
    Examples
    --------

    - List all repos

        octopols lmmx

    - List all repos that start with 'd'

        octopols lmmx -f '{name}.str.starts_with("d")'

    - List only file paths from matching repos

        octopols lmmx -w -f '{name} == "myrepo"'

    - Read the *content* of all files from matching repos

        octopols lmmx -x -f '{name}.str.starts_with("d3")'

    - Filter and sort the repos by stars

        octopols lmmx -f '{stars} > 8' -s 'pl.all().sort_by("stars", descending=True)'
    """,
)
@click.argument("username", type=str)
@click.option("-w", "--walk", is_flag=True, help="Walk files (default lists repos).")
@click.option(
    "-x",
    "--extract",
    is_flag=True,
    help="Read the text content of each file (not directories). Use with caution!",
)
@click.option(
    "-o",
    "--output-format",
    default="table",
    help="Output format: table, csv, json, or ndjson.",
)
@click.option(
    "-c",
    "--cols",
    default=-1,
    type=int,
    help="Number of table columns to show. Default -1 means show all.",
)
@click.option(
    "-r",
    "--rows",
    default=-1,
    type=int,
    help="Number of table rows to show. Default -1 means show all.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Quiet mode: overrides --rows and --cols by setting both to None.",
)
@click.option(
    "-f",
    "--filter",
    "filter_exprs",
    default=None,
    type=str,
    multiple=True,
    help=(
        "One or more Polars expressions or a shorthand DSL expression. "
        "In the DSL, use {column} to refer to pl.col('column'), "
        """e.g. '{name}.str.starts_with("a")'."""
    ),
)
@click.option(
    "-s",
    "--select",
    "select_exprs",
    default=None,
    type=str,
    multiple=True,
    help=(
        "One or more Polars expressions or a shorthand DSL expression. "
        "In the DSL, use {column} to refer to pl.col('column'), "
        """e.g. '{foo}.alias("bar")'."""
    ),
)
@click.option(
    "-a",
    "--addcols",
    "addcols_exprs",
    default=None,
    type=str,
    multiple=True,
    help=(
        "One or more Polars expressions or a shorthand DSL expression. "
        "In the DSL, use {column} to refer to pl.col('column'), "
        """e.g. '{total} * 2'."""
    ),
)
def repos(
    username: str,
    walk: bool,
    extract: bool,
    output_format: str,
    rows: int,
    cols: int,
    quiet: bool,
    filter_exprs: tuple[str, ...] | None,
    select_exprs: tuple[str, ...] | None,
    addcols_exprs: tuple[str, ...] | None,
) -> None:
    """CLI to print a user's repo listings, with options to walk and read files."""
    # Determine table dimensions
    show_tbl_rows = rows
    show_tbl_cols = cols
    if quiet:
        show_tbl_rows = None
        show_tbl_cols = None

    # Initialise Inventory (nothing is requested until fetching)
    inventory = Inventory(
        username=username,
        show_tbl_rows=show_tbl_rows,
        show_tbl_cols=show_tbl_cols,
        filter_exprs=filter_exprs,
        select_exprs=select_exprs,
        addcols_exprs=addcols_exprs,
    )

    try:
        if extract:
            # Read all files from each matched repository
            items = inventory.read_files()
        elif walk:
            # Merely list file paths
            items = inventory.walk_file_trees()
        else:
            # Default: list repositories
            items = inventory.list_repos()
    except Exception as exc:
        import traceback

        click.echo(click.style(traceback.format_exc(), fg="red"))
        click.echo(f"An error occurred: {exc}", err=True)
        raise SystemExit(1)

    # Output in the requested format
    if output_format == "csv":
        click.echo(items.write_csv())
    elif output_format == "json":
        click.echo(items.write_json())
    elif output_format == "ndjson":
        click.echo(items.write_ndjson())
    else:
        # Default: simple table
        click.echo(items)


def validate_repo_id(ctx, param, repo_id):
    """Ensure the user typed something like 'owner/repo' with a slash."""
    if "/" not in repo_id:
        raise click.BadParameter(
            "Repository must be in the format 'owner/repo' (missing slash).",
        )
    if repo_id.count("/") > 1:
        raise click.BadParameter(
            "Repository must be in the format 'owner/repo' (multiple slashes).",
        )
    username, repo_name = repo_id.split("/", 1)
    inventory = Inventory(
        username=username,
        filter_exprs=["{name} == " + repr(repo_name)],
        select_exprs=["{name}"],
    )
    repos_df = inventory.list_repos()
    if repos_df.is_empty():
        raise click.BadParameter(f"User {username} has no such repo {repo_name!r}")
    return repo_id


def validate_issue_state(ctx, param, state):
    """Ensure the user typed one of: "open", "closed", "all"."""
    state_options = {"open", "closed", "all"}
    if state not in state_options:
        raise click.BadParameter(f"Repository must be one of {state_options}.")
    return state


@octopols.command(help="List issues for the given GitHub username.")
@click.argument("repo_id", type=str, callback=validate_repo_id)
@click.argument("state", default="open", type=str, callback=validate_issue_state)
@click.option(
    "-o",
    "--output-format",
    default="table",
    help="Output format: table, csv, json, or ndjson.",
)
@click.option(
    "-c",
    "--cols",
    default=-1,
    type=int,
    help="Number of table columns to show. Default -1 means show all.",
)
@click.option(
    "-r",
    "--rows",
    default=-1,
    type=int,
    help="Number of table rows to show. Default -1 means show all.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Quiet mode: overrides --rows and --cols by setting both to None.",
)
@click.option(
    "-f",
    "--filter",
    "filter_exprs",
    default=None,
    type=str,
    multiple=True,
    help=(
        "One or more Polars expressions or a shorthand DSL expression. "
        "In the DSL, use {column} to refer to pl.col('column'), "
        """e.g. '{title}.str.starts_with("a")'."""
    ),
)
@click.option(
    "-s",
    "--select",
    "select_exprs",
    default=None,
    type=str,
    multiple=True,
    help=(
        "One or more Polars expressions or a shorthand DSL expression. "
        "In the DSL, use {column} to refer to pl.col('column'), "
        """e.g. '{foo}.alias("bar")'."""
    ),
)
@click.option(
    "-a",
    "--addcols",
    "addcols_exprs",
    default=None,
    type=str,
    multiple=True,
    help=(
        "One or more Polars expressions or a shorthand DSL expression. "
        "In the DSL, use {column} to refer to pl.col('column'), "
        """e.g. '{total} * 2'."""
    ),
)
def issues(
    repo_id: str,
    state: str,
    output_format: str,
    rows: int,
    cols: int,
    quiet: bool,
    filter_exprs: tuple[str, ...] | None,
    select_exprs: tuple[str, ...] | None,
    addcols_exprs: tuple[str, ...] | None,
) -> None:
    """GitHub issues subcommand: 'octopols issues <username>'."""
    show_tbl_rows = rows
    show_tbl_cols = cols
    if quiet:
        show_tbl_rows = None
        show_tbl_cols = None

    username, repo_name = repo_id.split("/", 1)
    click.echo(f"Listing issues for user: {username}, repo: {repo_name}", err=True)
    issues_inv = IssuesInventory(
        username=username,
        repo_name=repo_name,
        state=state,
        show_tbl_rows=show_tbl_rows,
        show_tbl_cols=show_tbl_cols,
        filter_exprs=filter_exprs,
        select_exprs=select_exprs,
        addcols_exprs=addcols_exprs,
    )
    items = issues_inv.list_issues()

    # Output in the requested format
    if output_format == "csv":
        click.echo(items.write_csv())
    elif output_format == "json":
        click.echo(items.write_json())
    elif output_format == "ndjson":
        click.echo(items.write_ndjson())
    else:
        # Default: simple table
        import json

        import polars as pl
        import polars.selectors as cs

        click.echo(
            items.with_columns(
                cs.string().map_elements(
                    lambda x: json.dumps(x)[1:-1],
                    return_dtype=pl.String,
                ),
            ),
        )
