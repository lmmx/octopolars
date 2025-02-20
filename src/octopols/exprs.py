"""Allow user-friendly short DSL expressions that get expanded to `pl.col` syntax."""

from __future__ import annotations

import re

import polars as pl
import polars.selectors as cs  # noqa: F401
import polars_hopper  # noqa: F401


dsl_pattern = re.compile(r"\{(\w+)\}")


def expand_short_expr(expr: str) -> str:
    """Convert DSL tokens like '{name}' into 'pl.col("name")' for Polars expressions.

    Example: '{name}.str.startswith("a")' -> 'pl.col("name").str.startswith("a")'.
    """
    return dsl_pattern.sub(r'pl.col("\g<1>")', expr)


def prepare_expr(expr: str | pl.Expr | None) -> pl.Expr | None:
    """Prepare a Polars expression from either a string DSL or an existing pl.Expr.

    Evaluates the DSL expression if given a string, expanding short filter tokens,
    and returns the resulting Polars expression. Returns None if expr is None.
    """
    if expr is not None:
        match expr:
            case pl.Expr() as expr:
                pass
            case str() as dsl_str:
                try:
                    expr = eval(expand_short_expr(dsl_str))
                except Exception as e:
                    print(e)
                    raise ValueError(f"Failed to evaluate: {expr=}: {e}")
            case _:
                raise ValueError(f"Expected pl.Expr or str: {expr}")
    return expr
