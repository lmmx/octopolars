# octopols

**A CLI and library for listing and filtering GitHub repositories and files using Polars-based data transformations.**

`octopols` leverages [PyGithub](https://github.com/PyGithub/PyGithub) (for GitHub API access) and [fsspec](https://github.com/fsspec/filesystem_spec) within [Universal Pathlib](https://github.com/fsspec/universal_pathlib) with `github` support (for enumerating files in GitHub repos). It uses [Polars](https://www.pola.rs/) for efficient data filtering and output formatting. Through a simple command-line interface, you can:

- **List Repositories**: Fetch public repositories for a specified GitHub user.  
- **List Files**: Recursively or non-recursively walk through a repository’s file tree.  
- **Apply Filters**: Use either raw Polars expressions or a shorthand DSL (e.g. `{name}.str.startswith("foo")`) to narrow your data.  
- **Choose Output Format**: Display results as a table (default), CSV, JSON, or NDJSON.  
- **Control Table Size**: Limit the number of rows or columns displayed, or use `--short` mode to quickly preview data.

## Features

- **GitHub Repo Enumeration**: Retrieve user’s public repos (caching results to speed up repeated calls).  
- **File Tree Listing**: Enumerate files in each repository using `fsspec[github]`, supporting recursion and optional size filters.  
- **Polars-Based Filtering**: Apply complex queries (`pl.col("name").str.contains("test")`) or simpler DSL expressions (`'{name}.str.startswith("a")'`).  
- **Flexible Output**: Display data in a pretty table (Polars-style) or export to CSV/JSON/NDJSON.  
- **Caching**: By default, results are cached in the user’s cache directory to avoid repeated API calls (unless you force refresh).  

## Installation

```bash
pip install octopols[polars]
```

> If you need compatibility with older CPUs, install:
> ```bash
> pip install octopols[polars-lts-cpu]
> ```

### Requirements

- Python 3.9+  
- A GitHub token in your environment (either via `$GITHUB_TOKEN` or by configuring [gh](https://cli.github.com/)) to avoid rate limits and enable file listings.

## Usage

### Command-Line Interface

```bash
octopols [OPTIONS] USERNAME
```

**Options:**

- `-F, --files`: List files instead of repos.  
- `-R, --recursive`: Recursively list items (applies to files if `--files` is set).  
- `-o, --output-format {table,csv,json,ndjson}`: Control output format (default: table).  
- `-r, --rows <INT>` / `-c, --cols <INT>`: Limit how many rows/columns to show (default: -1 means unlimited).  
- `-s, --short`: Override rows/cols limits by setting both to `None` for a concise preview.  
- `-f, --filter <EXPR>`: A Polars expression or DSL expression to filter the DataFrame.

#### Example 1: List All Repos for a User

```bash
octopols lmmx --short
```

Displays a table of all repositories belonging to "lmmx" in short format.

```py
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

```py
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
octopols lmmx -f '{name}.str.starts_with("d3")' --files
```

Lists *all* files in every repository starting with "d3" owned by "lmmx", as a table of file paths.

```py
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
