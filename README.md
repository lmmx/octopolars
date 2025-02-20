# octopolars

<!-- [![downloads](https://static.pepy.tech/badge/octopolars/month)](https://pepy.tech/project/octopolars) -->
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/octopolars.svg)](https://pypi.org/project/octopolars)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/octopolars.svg)](https://pypi.org/project/octopolars)
[![License](https://img.shields.io/pypi/l/octopolars.svg)](https://pypi.python.org/pypi/octopolars)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lmmx/octopolars/master.svg)](https://results.pre-commit.ci/latest/github/lmmx/octopolars/master)

Pull, filter, walk, and read a GitHub user's repositories with Polars.

## Installation

```bash
pip install octopolars
```

> The `polars` dependency is required but not included in the package by default.
> It is shipped as an optional extra which can be activated by passing it in square brackets:
> ```bash
> pip install octopolars[polars]          # most users can install regular Polars
> pip install octopolars[polars-lts-cpu]  # for backcompatibility with older CPUs
> ```

### Requirements

- Python 3.9+
- [gh](https://cli.github.com/) GitHub CLI tool, for a [PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
  to avoid rate limits and enable file listings.
    - **alternatively** set the `GH_TOKEN` environment variable as your GitHub token.

octopolars is supported by:

- [Polars](https://www.pola.rs/) for efficient data filtering and output formatting.
- [PyGithub](https://github.com/PyGithub/PyGithub) (for GitHub API access to enumerate the repos)
- [fsspec](https://github.com/fsspec/filesystem_spec) within [Universal Pathlib](https://github.com/fsspec/universal_pathlib)
  which provides a `github://` protocol that enables enumerating files in GitHub repos as if they were local file paths.

## Features

- **GitHub repo enumeration**: Retrieve user’s public repos (caching results to speed up repeated calls).
- **Apply filters**: Use either raw Polars expressions or a shorthand DSL (e.g. `{name}.str.starts_with("foo")`) to filter repos.
- **File tree walking**: Enumerate all files in each repository using `fsspec[github]`, supporting recursion and optional size filters.
- **Output formats**: Display data in a Polars repr table (which can be [read back in](https://docs.pola.rs/api/python/stable/reference/api/polars.from_repr.html))
  or export to CSV/JSON/NDJSON.
- **Control table size**: Limit the number of rows or columns displayed, or use `--quiet` mode to quickly preview data.
- **Caching**: By default, results are cached in the user’s cache directory to avoid repeated API calls (unless you force refresh).

## Usage

### Command-Line Interface

There are 2 subcommands, `repos` and `issues`.

```sh
$ octopols --help
Usage: octopols [OPTIONS] COMMAND [ARGS]...

  GitHub CLI with 2 subcommands (see their help text for more information).

  If no subcommand is given, the `repos` command is called by default.

Options:
  --help  Show this message and exit.

Commands:
  issues  List issues for the given GitHub username.
  repos   Octopols - A CLI for listing GitHub repos or files by username,...
```

The `repos` one is the default subcommand, and will run with just the `octopols` command plus a username.

### octopols repos

```bash
Usage: octopols [OPTIONS] USERNAME

  Octopols - A CLI for listing GitHub repos or files by username, with
  filters.

  By default, this prints a table of repositories.

    The --walk/-w flag walks the files rather than just listing the repos.

    The --extract/-x flag reads all matching files (use with caution).

    The --filter/-f flag (1+ times) applies `filter` exprs, or f-string-like
    column DSL (e.g., '{name}.str.starts_with("a")').

    The --select/-s flag (1+ times) applies `select` exprs, or f-string-like
    column DSL (e.g., '{foo}.alias("bar")').

    The --addcols/-a flag (1+ times) applies `with_columns` exprs, or
    f-string-like column DSL (e.g., '{total} * 2').

    The --quiet/-q flag switches to a minimal, abridged view. By default, rows
    and cols are unlimited (-1).

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

      octopols lmmx -f '{stars} > 8' -s 'pl.all().sort_by("stars",
      descending=True)'

Options:
  -w, --walk                Walk files (default lists repos).
  -x, --extract             Read the text content of each file (not
                            directories). Use with caution on large sets!
  -o, --output-format TEXT  Output format: table, csv, json, or ndjson.
  -c, --cols INTEGER        Number of table columns to show. Default -1 means
                            show all.
  -r, --rows INTEGER        Number of table rows to show. Default -1 means
                            show all.
  -q, --quiet               Quiet mode: overrides --rows and --cols by setting
                            both to None.
  -f, --filter TEXT         One or more Polars expressions or a shorthand DSL
                            expression. In the DSL, use {column} to refer to
                            pl.col('column'), e.g.
                            '{name}.str.starts_with("a")'.
  -s, --select TEXT         One or more Polars expressions or a shorthand DSL
                            expression. In the DSL, use {column} to refer to
                            pl.col('column'), e.g. '{foo}.alias("bar")'.
  -a, --addcols TEXT        One or more Polars expressions or a shorthand DSL
                            expression. In the DSL, use {column} to refer to
                            pl.col('column'), e.g. '{total} * 2'.
  --help                    Show this message and exit.
```

#### Example 1: List All Repos for a User

```bash
octopols lmmx --quiet
```

Displays a table of all repositories belonging to "lmmx" in abridged format.

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
octopols lmmx -f '{name}.str.contains("demo")'
```

Uses the DSL expression to select only repositories with “demo” in the repo name.

```
shape: (9, 9)
┌──────────────────────────────┬────────────────┬─────────────────────────────────┬──────────┬─────────┬────────┬───────┬───────┬───────┐
│ name                         ┆ default_branch ┆ description                     ┆ archived ┆ is_fork ┆ issues ┆ stars ┆ forks ┆ size  │
│ ---                          ┆ ---            ┆ ---                             ┆ ---      ┆ ---     ┆ ---    ┆ ---   ┆ ---   ┆ ---   │
│ str                          ┆ str            ┆ str                             ┆ bool     ┆ bool    ┆ i64    ┆ i64   ┆ i64   ┆ i64   │
╞══════════════════════════════╪════════════════╪═════════════════════════════════╪══════════╪═════════╪════════╪═══════╪═══════╪═══════╡
│ aiohttp-demos                ┆ master         ┆ Demos for aiohttp project       ┆ false    ┆ true    ┆ 0      ┆ 0     ┆ 0     ┆ 45445 │
│ demopyrs                     ┆ master         ┆ Demo Python/Rust extension lib… ┆ false    ┆ false   ┆ 0      ┆ 0     ┆ 0     ┆ 18    │
│ importstring_demo            ┆ master         ┆ Demo of deptry inability to de… ┆ false    ┆ false   ┆ 0      ┆ 1     ┆ 0     ┆ 7     │
│ pyd2ts-demo                  ┆ master         ┆ Demo of a Pydantic model conve… ┆ false    ┆ false   ┆ 0      ┆ 0     ┆ 0     ┆ 761   │
│ react-htmx-demo              ┆ master         ┆ Demo app combining HTMX and Re… ┆ false    ┆ false   ┆ 0      ┆ 0     ┆ 0     ┆ 2     │
│ self-serve-demo              ┆ master         ┆ Python package auto-generated … ┆ false    ┆ false   ┆ 1      ┆ 1     ┆ 0     ┆ 14    │
│ sphinx-type-annotations-demo ┆ master         ┆ [Resolved] A demo of how to bu… ┆ false    ┆ false   ┆ 1      ┆ 0     ┆ 0     ┆ 39    │
│ uv-doc-url-demo              ┆ master         ┆ Proof-of-concept for extractin… ┆ false    ┆ false   ┆ 0      ┆ 0     ┆ 0     ┆ 27    │
│ uv-ws-demo                   ┆ master         ┆ A simple demo of the new works… ┆ false    ┆ false   ┆ 0      ┆ 1     ┆ 0     ┆ 15    │
└──────────────────────────────┴────────────────┴─────────────────────────────────┴──────────┴─────────┴────────┴───────┴───────┴───────┘
```

#### Example 3: Walk an Entire Repo

```bash
octopols lmmx -f '{name} == "mvdef"' --walk --quiet
```

Lists all files in the repository named "mvdef", abbreviating the output table in 'quiet' format.

```
shape: (121, 4)
┌─────────────────┬─────────────────────────────────┬──────────────┬─────────────────┐
│ repository_name ┆ file_path                       ┆ is_directory ┆ file_size_bytes │
│ ---             ┆ ---                             ┆ ---          ┆ ---             │
│ str             ┆ str                             ┆ bool         ┆ i64             │
╞═════════════════╪═════════════════════════════════╪══════════════╪═════════════════╡
│ mvdef           ┆ .github                         ┆ true         ┆ 0               │
│ mvdef           ┆ .github/CONTRIBUTING.md         ┆ false        ┆ 3094            │
│ mvdef           ┆ .github/workflows               ┆ true         ┆ 0               │
│ mvdef           ┆ .github/workflows/master.yml    ┆ false        ┆ 3398            │
│ mvdef           ┆ .gitignore                      ┆ false        ┆ 204             │
│ …               ┆ …                               ┆ …            ┆ …               │
│ mvdef           ┆ tools                           ┆ true         ┆ 0               │
│ mvdef           ┆ tools/github                    ┆ true         ┆ 0               │
│ mvdef           ┆ tools/github/install_miniconda… ┆ false        ┆ 353             │
│ mvdef           ┆ tox.ini                         ┆ false        ┆ 1251            │
│ mvdef           ┆ vercel.json                     ┆ false        ┆ 133             │
└─────────────────┴─────────────────────────────────┴──────────────┴─────────────────┘
```

#### Example 4: Filter Repos by Name, List All Files

```bash
octopols lmmx -f '{name}.str.starts_with("d3")' --walk
```

List all files in every repository owned by "lmmx" whose repo name starts with "d3".

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

#### Example 5: Filter Repos by Name, Read All Files

```bash
octopols lmmx -x --filter='{name}.str.contains("uv")' --quiet
```

Read the content of all files whose repo name starts with "d3" owned by "lmmx".

```
shape: (28, 4)
┌─────────────────┬────────────────────────────┬─────────────────┬─────────────────────────────────┐
│ repository_name ┆ file_path                  ┆ file_size_bytes ┆ content                         │
│ ---             ┆ ---                        ┆ ---             ┆ ---                             │
│ str             ┆ str                        ┆ i64             ┆ str                             │
╞═════════════════╪════════════════════════════╪═════════════════╪═════════════════════════════════╡
│ uv-doc-url-demo ┆ .gitignore                 ┆ 8               ┆ /target                         │
│                 ┆                            ┆                 ┆                                 │
│ uv-doc-url-demo ┆ Cargo.lock                 ┆ 90700           ┆ # This file is automatically @… │
│ uv-doc-url-demo ┆ Cargo.toml                 ┆ 632             ┆ [package]                       │
│                 ┆                            ┆                 ┆ name = "uv-doc-url-d…           │
│ uv-doc-url-demo ┆ README.md                  ┆ 2361            ┆ # uv-doc-url-demo               │
│                 ┆                            ┆                 ┆                                 │
│                 ┆                            ┆                 ┆ A Rust proo…                    │
│ uv-doc-url-demo ┆ src                        ┆ 0               ┆                                 │
│ …               ┆ …                          ┆ …               ┆ …                               │
│ uv-ws-demo      ┆ src                        ┆ 0               ┆                                 │
│ uv-ws-demo      ┆ src/workspaces             ┆ 0               ┆                                 │
│ uv-ws-demo      ┆ src/workspaces/__init__.py ┆ 45              ┆ from .cli import greet          │
│                 ┆                            ┆                 ┆                                 │
│                 ┆                            ┆                 ┆ __all_…                         │
│ uv-ws-demo      ┆ src/workspaces/cli.py      ┆ 461             ┆ from sys import argv            │
│                 ┆                            ┆                 ┆                                 │
│                 ┆                            ┆                 ┆ from pyd…                       │
│ uv-ws-demo      ┆ uv.lock                    ┆ 19814           ┆ version = 1                     │
│                 ┆                            ┆                 ┆ requires-python = …             │
└─────────────────┴────────────────────────────┴─────────────────┴─────────────────────────────────┘
```

#### Example 6: Filter Repos by Name, Add Columns Based on Description

```bash
octopols lmmx -f '{name}.str.starts_with("d3")' -a '{description}.str.contains("AWS").alias("Will It Cloud?")'
```

Adds a boolean column called "Will It Cloud?" based on whether the repo description contains "AWS".

```
shape: (2, 10)
┌────────────────────┬────────────────┬─────────────────────────────────┬──────────┬─────────┬────────┬───────┬───────┬──────┬────────────────┐
│ name               ┆ default_branch ┆ description                     ┆ archived ┆ is_fork ┆ issues ┆ stars ┆ forks ┆ size ┆ Will It Cloud? │
│ ---                ┆ ---            ┆ ---                             ┆ ---      ┆ ---     ┆ ---    ┆ ---   ┆ ---   ┆ ---  ┆ ---            │
│ str                ┆ str            ┆ str                             ┆ bool     ┆ bool    ┆ i64    ┆ i64   ┆ i64   ┆ i64  ┆ bool           │
╞════════════════════╪════════════════╪═════════════════════════════════╪══════════╪═════════╪════════╪═══════╪═══════╪══════╪════════════════╡
│ d3-step-functions  ┆ master         ┆ AWS Step Function visualisatio… ┆ false    ┆ false   ┆ 1      ┆ 1     ┆ 0     ┆ 94   ┆ true           │
│ d3-wiring-diagrams ┆ master         ┆ Wiring diagram operad visualis… ┆ false    ┆ false   ┆ 2      ┆ 2     ┆ 0     ┆ 111  ┆ false          │
└────────────────────┴────────────────┴─────────────────────────────────┴──────────┴─────────┴────────┴───────┴───────┴──────┴────────────────┘
```

#### Example 7: Filter Repos by Stars, Sort By Stars

```sh
octopols lmmx -f '{stars} > 8' -s 'pl.all().sort_by("stars", descending=True)'
```

```
shape: (6, 9)
┌──────────────────────────┬────────────────┬─────────────────────────────────┬──────────┬─────────┬────────┬───────┬───────┬───────┐
│ name                     ┆ default_branch ┆ description                     ┆ archived ┆ is_fork ┆ issues ┆ stars ┆ forks ┆ size  │
│ ---                      ┆ ---            ┆ ---                             ┆ ---      ┆ ---     ┆ ---    ┆ ---   ┆ ---   ┆ ---   │
│ str                      ┆ str            ┆ str                             ┆ bool     ┆ bool    ┆ i64    ┆ i64   ┆ i64   ┆ i64   │
╞══════════════════════════╪════════════════╪═════════════════════════════════╪══════════╪═════════╪════════╪═══════╪═══════╪═══════╡
│ gdocs2md-html            ┆ master         ┆ Convert a Google Drive Documen… ┆ true     ┆ false   ┆ 12     ┆ 289   ┆ 37    ┆ 92    │
│ page-dewarp              ┆ master         ┆ Document image dewarping libra… ┆ false    ┆ false   ┆ 8      ┆ 138   ┆ 20    ┆ 11171 │
│ deforum-stable-diffusion ┆ master         ┆ Refactor of the Deforum Stable… ┆ false    ┆ false   ┆ 6      ┆ 105   ┆ 17    ┆ 68    │
│ devnotes                 ┆ master         ┆ obscure technical resolutions … ┆ false    ┆ false   ┆ 1      ┆ 89    ┆ 7     ┆ 6122  │
│ tabsave                  ┆ master         ┆ Super simple Chrome extension … ┆ false    ┆ false   ┆ 20     ┆ 64    ┆ 21    ┆ 1020  │
│ range-streams            ┆ master         ┆ Streaming range requests in Py… ┆ false    ┆ false   ┆ 10     ┆ 9     ┆ 0     ┆ 402   │
└──────────────────────────┴────────────────┴─────────────────────────────────┴──────────┴─────────┴────────┴───────┴───────┴───────┘
```


### octopols issues

The issues is an extra feature, and paginates 100 issues at a time (anything above that
may make you wait a little while).

```sh
time octopols issues huggingface/transformers > /dev/null
```

```
Listing issues for user: huggingface, repo: transformers

real    0m24.350s
user    0m3.148s
sys     0m0.195s
```

Some more example usage follows.

### Example 1: Sort issues by frequency of a keyword

```sh
octopols issues pola-rs/polars -a '{body}.str.count_matches("foo").alias("matches")' -s 'pl.all().sort_by({matches}, descending=True)' -s 'pl.col("number", "title", "body")' -f '{matches} > 0' -o json
```

This one could be used interactively with `jq` to pretty-print the JSON output, or in a CI workflow.

It says:

- List all the issues on the pola-rs/polars repo
- Add a "matches" column made from the count of the string "foo" in the "body" column
- Sort the rows by the matches column
- Select just the columns "number", "title", "body"
- Filter to rows with at least one match
- Write as JSON to STDOUT

### Library Usage

You can also import `octopols.Inventory` directly:

```python
from octopols import Inventory

inv = Inventory(username="lmmx")
repos_df = inv.list_repos()
```

If you want to apply a filter expression programmatically and walk the file trees:

```python
import polars as pl

inv = Inventory(username="lmmx", filter_exprs=[pl.col("name").str.contains("demo")])
files_df = inv.walk_file_trees()
```

## Project Structure

- `cli.py`: Defines the CLI (`octopols`) with all available options and flags.
- `inventory.py`: Core logic for retrieving repos, walking file trees, caching, and applying filters.

## Contributing

Maintained by [lmmx](https://github.com/lmmx). Contributions welcome!

1. **Issues & Discussions**: Please open a GitHub issue or discussion for bugs, feature requests, or questions.
2. **Pull Requests**: PRs are welcome!
   - Install the dev extra (e.g. with [uv](https://docs.astral.sh/uv/): `uv pip install -e .[dev]`)
   - Run tests (when available) and include updates to docs or examples if relevant.
   - If reporting a bug, please include the version and the error message/traceback if available.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
