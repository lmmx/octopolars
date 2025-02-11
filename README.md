# octopols

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/octopolars.svg)](https://pypi.org/projects/octopolars)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/octopolars.svg)](https://pypi.org/project/octopolars)
[![downloads](https://static.pepy.tech/badge/octopolars/month)](https://pepy.tech/project/octopolars)
[![License](https://img.shields.io/pypi/l/octopolars.svg)](https://pypi.python.org/pypi/octopolars)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lmmx/octopolars/master.svg)](https://results.pre-commit.ci/latest/github/lmmx/octopolars/master)

List and filter GitHub user repo inventories and their files with Polars.

## Installation

```bash
pip install octopols[polars]
```

> If you need compatibility with older CPUs, install:
> ```bash
> pip install octopols[polars-lts-cpu]
> ```

## Features

- **GitHub repo enumeration**: Retrieve user’s public repos (caching results to speed up repeated calls).
- **Apply filters**: Use either raw Polars expressions or a shorthand DSL (e.g. `{name}.str.startswith("foo")`) to filter repos.
- **File tree walking**: Enumerate all files in each repository using `fsspec[github]`, supporting recursion and optional size filters.
- **Output formats**: Display data in a Polars repr table (which can be [read back in](https://docs.pola.rs/api/python/stable/reference/api/polars.from_repr.html))
  or export to CSV/JSON/NDJSON.
- **Control table size**: Limit the number of rows or columns displayed, or use `--short` mode to quickly preview data.
- **Caching**: By default, results are cached in the user’s cache directory to avoid repeated API calls (unless you force refresh).

### Requirements

- Python 3.9+
- A GitHub token in your environment (either via `$GITHUB_TOKEN` or by configuring [gh](https://cli.github.com/)) to avoid rate limits and enable file listings.

`octopols` is supported by these tools:

- [Polars](https://www.pola.rs/) for efficient data filtering and output formatting.
- [PyGithub](https://github.com/PyGithub/PyGithub) (for GitHub API access to enumerate the repos)
- [fsspec](https://github.com/fsspec/filesystem_spec) within [Universal Pathlib](https://github.com/fsspec/universal_pathlib)
  which provides a `github://` protocol that enables enumerating files in GitHub repos as if they were local file paths.

## Usage

### Command-Line Interface

```bash
Usage: octopols [OPTIONS] USERNAME

  octopols - A CLI for listing GitHub repos or files by username, with
  optional recursion, table formatting, and Polars-based filtering.

    By default, rows and cols are unlimited (-1). Use --short/-s to switch to
    a minimal view.

    The --filter/-f flag (if provided) applies a Polars expression or DSL
    expression   (e.g., '{name}.str.startswith("a")') to the DataFrame of
    items.

    Examples:

      octopols alice

      octopols alice -f '{name}.str.startswith("a")'

      octopols alice -FR --filter='pl.col("filename").str.contains("test")'

Options:
  -F, --files               List files (default lists repos).
  -R, --recursive           Recursively list items (repos or files).
  -o, --output-format TEXT  Output format: table, csv, json, or ndjson.
  -r, --rows INTEGER        Number of table rows to show. Default -1 means
                            show all.
  -c, --cols INTEGER        Number of table columns to show. Default -1 means
                            show all.
  -s, --short               Short mode: overrides --rows and --cols by setting
                            both to None.
  -f, --filter TEXT         A Polars expression or a shorthand DSL expression.
                            In the DSL, use {column} to refer to
                            pl.col('column'), e.g.
                            '{name}.str.startswith("a")'
  --help                    Show this message and exit.
```

#### Example 1: List All Repos for a User

```bash
octopols lmmx --short
```

Displays a table of all repositories belonging to "lmmx" in short format.

```
shape: (226, 9)
┌────────────────────────┬────────────────┬─────────────────────────────────┬──────────┬───┬────────┬───────┬───────┬───────┐
│ name                   ┆ default_branch ┆ description                     ┆ archived ┆ … ┆ issues ┆ stars ┆ forks ┆ size  │
│ ---                    ┆ ---            ┆ ---                             ┆ ---      ┆   ┆ ---    ┆ ---   ┆ ---   ┆ ---   │
│ str                    ┆ str            ┆ str                             ┆ bool     ┆   ┆ i64    ┆ i64   ┆ i64   ┆ i64   │
╞════════════════════════╪════════════════╪═════════════════════════════════╪══════════╪═══╪════════╪═══════╪═══════╪═══════╡
│ 2020-viz               ┆ master         ┆                                 ┆ false    ┆ … ┆ 10     ┆ 0     ┆ 0     ┆ 1459  │
│ 3dv                    ┆ master         ┆ Some 3D file handling with num… ┆ false    ┆ … ┆ 0      ┆ 0     ┆ 0     ┆ 21096 │
│ AbbrevJ                ┆ master         ┆ JS journal abbreviation genera… ┆ true     ┆ … ┆ 0      ┆ 0     ┆ 0     ┆ 724   │
│ AdaBins                ┆ main           ┆ Official implementation of Ada… ┆ false    ┆ … ┆ 0      ┆ 1     ┆ 0     ┆ 560   │
│ advent-of-code-2017    ┆ master         ┆ Advent of Code 2017             ┆ true     ┆ … ┆ 0      ┆ 0     ┆ 0     ┆ 32    │
│ …                      ┆ …              ┆ …                               ┆ …        ┆ … ┆ …      ┆ …     ┆ …     ┆ …     │
│ whisper                ┆ main           ┆                                 ┆ false    ┆ … ┆ 0      ┆ 1     ┆ 0     ┆ 3118  │
│ wikitransp             ┆ master         ┆ Dataset of transparent images … ┆ false    ┆ … ┆ 3      ┆ 0     ┆ 0     ┆ 58    │
│ wotd                   ┆ master         ┆ Analysis of WOTD data from Twe… ┆ false    ┆ … ┆ 1      ┆ 1     ┆ 0     ┆ 92    │
│ wwdc-21-3d-obj-capture ┆ master         ┆ "TakingPicturesFor3DObjectCapt… ┆ false    ┆ … ┆ 1      ┆ 1     ┆ 0     ┆ 2861  │
│ YouCompleteMe          ┆ master         ┆ A code-completion engine for V… ┆ false    ┆ … ┆ 0      ┆ 1     ┆ 0     ┆ 32967 │
└────────────────────────┴────────────────┴─────────────────────────────────┴──────────┴───┴────────┴───────┴───────┴───────┘
```

#### Example 2: Filter Repos by Name

```bash
octopols lmmx -f '{name}.str.startswith("d3")'
```

Uses the DSL expression to select only repositories whose name starts with “d.”

```
shape: (2, 9)
┌────────────────────┬────────────────┬─────────────────────────────────┬──────────┬─────────┬────────┬───────┬───────┬──────┐
│ name               ┆ default_branch ┆ description                     ┆ archived ┆ is_fork ┆ issues ┆ stars ┆ forks ┆ size │
│ ---                ┆ ---            ┆ ---                             ┆ ---      ┆ ---     ┆ ---    ┆ ---   ┆ ---   ┆ ---  │
│ str                ┆ str            ┆ str                             ┆ bool     ┆ bool    ┆ i64    ┆ i64   ┆ i64   ┆ i64  │
╞════════════════════╪════════════════╪═════════════════════════════════╪══════════╪═════════╪════════╪═══════╪═══════╪══════╡
│ d3-step-functions  ┆ master         ┆ AWS Step Function visualisatio… ┆ false    ┆ false   ┆ 1      ┆ 1     ┆ 0     ┆ 94   │
│ d3-wiring-diagrams ┆ master         ┆ Wiring diagram operad visualis… ┆ false    ┆ false   ┆ 2      ┆ 2     ┆ 0     ┆ 111  │
└────────────────────┴────────────────┴─────────────────────────────────┴──────────┴─────────┴────────┴───────┴───────┴──────┘
```

#### Example 3: Filter Repos by Name, List all Files

```bash
octopols lmmx --walk -f '{name}.str.starts_with("d3")'
```

Lists *all* files in every repository starting with "d3" owned by "lmmx", as a table of file paths.

```
shape: (12, 4)
┌────────────────────┬───────────────────────────────┬──────────────┬─────────────────┐
│ repository_name    ┆ file_path                     ┆ is_directory ┆ file_size_bytes │
│ ---                ┆ ---                           ┆ ---          ┆ ---             │
│ str                ┆ str                           ┆ bool         ┆ i64             │
╞════════════════════╪═══════════════════════════════╪══════════════╪═════════════════╡
│ d3-step-functions  ┆ README.md                     ┆ false        ┆ 62              │
│ d3-step-functions  ┆ d3-step-function-diagram.html ┆ false        ┆ 498             │
│ d3-step-functions  ┆ d3.v7.min.js                  ┆ false        ┆ 278580          │
│ d3-step-functions  ┆ wd-style.css                  ┆ false        ┆ 35              │
│ d3-step-functions  ┆ wd_sample_data.json           ┆ false        ┆ 1053            │
│ d3-step-functions  ┆ wiring-diagram.js             ┆ false        ┆ 9264            │
│ d3-wiring-diagrams ┆ README.md                     ┆ false        ┆ 66              │
│ d3-wiring-diagrams ┆ d3-wiring-diagram.html        ┆ false        ┆ 484             │
│ d3-wiring-diagrams ┆ d3.v7.min.js                  ┆ false        ┆ 278580          │
│ d3-wiring-diagrams ┆ wd-style.css                  ┆ false        ┆ 35              │
│ d3-wiring-diagrams ┆ wd_sample_data.json           ┆ false        ┆ 1053            │
│ d3-wiring-diagrams ┆ wiring-diagram.js             ┆ false        ┆ 7482            │
└────────────────────┴───────────────────────────────┴──────────────┴─────────────────┘
```

### Library Usage

You can also import `octopols.Inventory` directly:

```python
from octopols import Inventory

inv = Inventory(username="lmmx")
repos_df = inv.list_repos()
```

If you want to apply a filter expression programmatically and walk the file trees:

```python
inv = Inventory(username="lmmx", repo_filter=pl.col("name").str.contains("demo"))
files_df = inv.walk_file_trees()
```

## Project Structure

- `cli.py`: Defines the CLI (`octopols`) with all available options and flags.
- `inventory.py`: Core logic for retrieving repos, walking file trees, caching, and applying filters.

## Contributing

1. **Issues & Discussions**: Please open a GitHub issue or discussion for bugs, feature requests, or questions.
2. **Pull Requests**: PRs are welcome!
   - Ensure you have [pdm](https://pdm.fming.dev/latest/) installed for local development.
   - Run tests (when available) and include updates to docs or examples if relevant.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

Maintained by [lmmx](https://github.com/lmmx). Contributions welcome!
