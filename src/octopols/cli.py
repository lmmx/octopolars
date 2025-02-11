"""This module provides the CLI command for Octopols."""

from __future__ import annotations

import sys

import click

from .inventory import Inventory


@click.command()
@click.argument("username", type=str)
@click.option("-w", "--walk", is_flag=True, help="Walk files (default lists repos).")
# @click.option(
#     "-R", "--recursive", is_flag=True, help="Recursively list items (repos or files)."
# )
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
        "e.g. '{name}.str.startswith(\"a\")'"
    ),
)
def main(
    username: str,
    files: bool,
    recursive: bool,
    output_format: str,
    rows: int,
    cols: int,
    short: bool,
    filter_expr: str,
) -> None:
    """Octopols - A CLI for listing GitHub repos or files by username, with optional recursion,
    table formatting, and Polars-based filtering.

      By default, rows and cols are unlimited (-1). Use --short/-s to switch to a minimal view.

      The --filter/-f flag (if provided) applies a Polars expression or DSL expression
      (e.g., '{name}.str.startswith("a")') to the DataFrame of items.

      The --walk/-w flag walks the files rather than just listing the repos.

    Examples
    --------
        octopols lmmx

        octopols lmmx -f '{name}.str.startswith("a")'

        octopols lmmx -w -filter='pl.col("filename").str.contains("test")'

    """
    # Determine table dimensions
    show_tbl_rows = rows
    show_tbl_cols = cols

    if short:
        show_tbl_rows = None
        show_tbl_cols = None

    # Initialize the inventory with the chosen row/col limits
    inventory = Inventory(
        username=username,
        show_tbl_rows=show_tbl_rows,
        show_tbl_cols=show_tbl_cols,
        repo_filter=filter_expr,
    )

    try:
        # Decide whether to list repos or files, recursively or not
        if files:
            items = inventory.walk_file_trees()
        else:
            items = inventory.list_repos()
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    # Finally, output in the requested format
    if output_format == "csv":
        click.echo(items.write_csv())
    elif output_format == "json":
        click.echo(items.write_json())
    elif output_format == "ndjson":
        click.echo(items.write_ndjson())
    else:
        # Default: simple table
        click.echo(items)
