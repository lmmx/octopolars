"""Tests for the expression DSL expansion and preparation."""

import polars as pl
import pytest

from octopols.exprs import expand_short_expr, prepare_expr


class TestExpandShortExpr:
    """Tests for the DSL token expansion."""

    def test_single_column_reference(self):
        """Verify single column reference expands correctly."""
        result = expand_short_expr("{name}")
        assert result == 'pl.col("name")'

    def test_column_with_method_chain(self):
        """Verify column reference with method chain expands correctly."""
        result = expand_short_expr('{name}.str.starts_with("foo")')
        assert result == 'pl.col("name").str.starts_with("foo")'

    def test_multiple_column_references(self):
        """Verify multiple column references expand correctly."""
        result = expand_short_expr("{a} + {b}")
        assert result == 'pl.col("a") + pl.col("b")'

    def test_no_column_references(self):
        """Verify expressions without column references pass through."""
        result = expand_short_expr("pl.lit(5)")
        assert result == "pl.lit(5)"

    def test_column_with_alias(self):
        """Verify column reference with alias expands correctly."""
        result = expand_short_expr('{total}.alias("sum")')
        assert result == 'pl.col("total").alias("sum")'

    def test_complex_expression(self):
        """Verify complex expressions expand correctly."""
        result = expand_short_expr("{stars} > 8")
        assert result == 'pl.col("stars") > 8'


class TestPrepareExpr:
    """Tests for expression preparation from strings or Expr objects."""

    def test_none_input(self):
        """Verify None input returns None."""
        assert prepare_expr(None) is None

    def test_polars_expr_passthrough(self):
        """Verify Polars Expr objects pass through unchanged."""
        expr = pl.col("name")
        result = prepare_expr(expr)
        assert result.meta.eq(expr)

    def test_string_dsl_conversion(self):
        """Verify string DSL converts to Polars Expr."""
        result = prepare_expr('{name} == "test"')
        assert isinstance(result, pl.Expr)

    def test_raw_polars_string(self):
        """Verify raw Polars expression strings convert correctly."""
        result = prepare_expr('pl.col("stars") > 5')
        assert isinstance(result, pl.Expr)

    def test_invalid_expression_raises(self):
        """Verify invalid expressions raise ValueError."""
        with pytest.raises(ValueError, match="Failed to evaluate"):
            prepare_expr("{nonexistent_syntax!!!")


class TestExpressionEvaluation:
    """Tests that prepared expressions work correctly on DataFrames."""

    @pytest.fixture
    def sample_df(self):
        """Return a sample DataFrame for testing expressions."""
        return pl.DataFrame(
            {
                "name": ["alpha", "beta", "gamma", "delta"],
                "stars": [10, 5, 20, 3],
                "archived": [False, True, False, False],
            },
        )

    def test_filter_by_string_contains(self, sample_df):
        """Verify string contains filter works correctly."""
        expr = prepare_expr('{name}.str.contains("ph")')
        result = sample_df.filter(expr)
        assert result["name"].to_list() == ["alpha"]

    def test_filter_by_numeric_comparison(self, sample_df):
        """Verify numeric comparison filter works correctly."""
        expr = prepare_expr("{stars} > 8")
        result = sample_df.filter(expr)
        assert result["name"].to_list() == ["alpha", "gamma"]

    def test_filter_by_boolean_column(self, sample_df):
        """Verify boolean column filter works correctly."""
        expr = prepare_expr("{archived}")
        result = sample_df.filter(expr)
        assert result["name"].to_list() == ["beta"]

    def test_select_with_alias(self, sample_df):
        """Verify select with alias works correctly."""
        expr = prepare_expr('{name}.alias("repo_name")')
        result = sample_df.select(expr)
        assert "repo_name" in result.columns
        assert result["repo_name"].to_list() == ["alpha", "beta", "gamma", "delta"]

    def test_with_columns_computed(self, sample_df):
        """Verify computed columns are added correctly."""
        expr = prepare_expr('({stars} * 2).alias("double_stars")')
        result = sample_df.with_columns(expr)
        assert result["double_stars"].to_list() == [20, 10, 40, 6]
