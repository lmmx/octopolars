"""Provides the `octopols` CLI command for Octopolars."""

from __future__ import annotations

import sys

import click

from .inventory import Inventory


@click.command()
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
    "filter_expr",
    default=None,
    help=(
        "A Polars expression or a shorthand DSL expression. "
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
    filter_expr: str,
) -> None:
    """Octopols - A CLI for listing GitHub repos or files by username, with filters.

    By default, this prints a table of repositories.

      The --walk/-w flag walks the files rather than just listing the repos.\n
      The --extract/-x flag reads all matching files (use with caution).\n
      The --filter/-f flag (if provided) applies a Polars expression, or column DSL that is expanded to one (e.g., '{name}.str.starts_with("a")'), to the DataFrame of repos.\n
      The --short/-s flag switches to a minimal, abridged view. By default, rows and cols are unlimited (-1).

    Examples

        - List all repos

            octopols lmmx

        - List all repos that start with 'd'

            octopols lmmx -f '{name}.str.starts_with("d")'

        - List only file paths from matching repos

            octopols lmmx -w --filter='{name} == "myrepo"'

        - Read the *content* of all files from matching repos

            octopols lmmx -x --filter='{name}.str.starts_with("d3")'
    """
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
        repo_filter=filter_expr,
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
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

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
