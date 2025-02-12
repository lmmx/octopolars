"""Provides the `octopols` CLI command for Octopolars."""

from __future__ import annotations

import click

from .inventory import Inventory


@click.command(
    help="""Octopols - A CLI for listing GitHub repos or files by username, with filters.

    By default, this prints a table of repositories.

      The --walk/-w flag walks the files rather than just listing the repos.

      The --extract/-x flag reads all matching files (use with caution).

      The --filter/-f flag (if provided) applies 1+ Polars expressions, or f-string-like column DSL that is expanded to them (e.g., '{name}.str.starts_with("a")'), to the DataFrame of repos.

      The --short/-s flag switches to a minimal, abridged view. By default, rows and cols are unlimited (-1).

    \b
    Examples
    --------

    - List all repos

        octopols lmmx

    - List all repos that start with 'd'

        octopols lmmx -f '{name}.str.starts_with("d")'

    - List only file paths from matching repos

        octopols lmmx -w --filter='{name} == "myrepo"'

    - Read the *content* of all files from matching repos

        octopols lmmx -x --filter='{name}.str.starts_with("d3")'
""",
)
@click.argument("username", type=str)
@click.option("-w", "--walk", is_flag=True, help="Walk files (default lists repos).")
@click.option(
    "-x",
    "--extract",
    is_flag=True,
    help="Read the text content of each file (not directories). Use with caution on large sets!",
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
    "-s",
    "--short",
    is_flag=True,
    help="Short mode: overrides --rows and --cols by setting both to None.",
)
@click.option(
    "--filter",
    "-f",
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
def octopols(
    username: str,
    walk: bool,
    extract: bool,
    output_format: str,
    rows: int,
    cols: int,
    short: bool,
    filter_exprs: tuple[str, ...] | None,
) -> None:
    """CLI to print a user's repo listings, with options to walk and read files."""
    # Determine table dimensions
    show_tbl_rows = rows
    show_tbl_cols = cols
    if short:
        show_tbl_rows = None
        show_tbl_cols = None

    # Initialise Inventory (nothing is requested until fetching)
    inventory = Inventory(
        username=username,
        show_tbl_rows=show_tbl_rows,
        show_tbl_cols=show_tbl_cols,
        filter_exprs=filter_exprs,
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
