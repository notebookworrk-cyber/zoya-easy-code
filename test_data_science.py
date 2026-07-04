import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zoya.data import (
    DataFrame,
    DataFrameError,
    Figure,
    Plot,
    Series,
    VisualizationError,
    create_dataframe,
    set_style,
)


class TestDataFrameCreation(unittest.TestCase):
    def test_create_from_list_of_dicts(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        df = DataFrame(data)
        self.assertEqual(df.shape, (2, 2))
        self.assertEqual(df.columns, ["a", "b"])

    def test_create_from_dict_of_lists(self):
        data = {"a": [1, 2, 3], "b": [4, 5, 6]}
        df = DataFrame(data)
        self.assertEqual(df.shape, (3, 2))
        self.assertEqual(df.columns, ["a", "b"])

    def test_create_from_list_of_lists_with_columns(self):
        data = [[1, 2], [3, 4]]
        df = DataFrame(data, columns=["x", "y"])
        self.assertEqual(df.shape, (2, 2))
        self.assertEqual(df.columns, ["x", "y"])

    def test_create_from_single_scalar(self):
        df = DataFrame([10, 20, 30])
        self.assertEqual(df.shape, (3, 1))
        self.assertEqual(df.columns, ["col0"])

    def test_create_from_single_scalar_with_columns(self):
        df = DataFrame([42], columns=["val"])
        self.assertEqual(df.shape, (1, 1))
        self.assertEqual(df["val"].values, [42])

    def test_create_empty(self):
        df = DataFrame()
        self.assertEqual(df.shape, (0, 0))
        self.assertTrue(df.empty)

    def test_create_empty_with_columns(self):
        df = DataFrame(columns=["a", "b"])
        self.assertEqual(df.shape, (0, 2))
        self.assertEqual(df.columns, ["a", "b"])


class TestDataFrameProperties(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame(
            {"a": [1, 2, 3], "b": [4.0, 5.0, 6.0], "c": ["x", "y", "z"]}
        )

    def test_shape(self):
        self.assertEqual(self.df.shape, (3, 3))

    def test_columns(self):
        self.assertEqual(self.df.columns, ["a", "b", "c"])

    def test_dtypes(self):
        dtypes = self.df.dtypes
        self.assertIn("a", dtypes)
        self.assertIn("b", dtypes)

    def test_empty_false(self):
        self.assertFalse(self.df.empty)

    def test_size(self):
        self.assertEqual(self.df.size, 9)

    def test_columns_setter(self):
        self.df.columns = ["x", "y", "z"]
        self.assertEqual(self.df.columns, ["x", "y", "z"])

    def test_columns_setter_wrong_length(self):
        with self.assertRaises(DataFrameError):
            self.df.columns = ["x", "y"]


class TestDataFrameAccess(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})

    def test_getitem_single_column_returns_series(self):
        s = self.df["a"]
        self.assertIsInstance(s, Series)
        self.assertEqual(s.name, "a")
        self.assertEqual(s.values, [1, 2, 3])

    def test_getitem_multiple_columns(self):
        df2 = self.df[["a", "c"]]
        self.assertEqual(df2.shape, (3, 2))
        self.assertEqual(df2.columns, ["a", "c"])

    def test_getitem_missing_column_raises(self):
        with self.assertRaises(DataFrameError):
            self.df["nonexistent"]

    def test_getattr_column_access(self):
        s = self.df.a
        self.assertIsInstance(s, Series)
        self.assertEqual(s.values, [1, 2, 3])

    def test_getattr_invalid_attr_raises(self):
        with self.assertRaises(AttributeError):
            self.df._internal

    def test_head_returns_correct_rows(self):
        df2 = self.df.head(2)
        self.assertEqual(df2.shape, (2, 3))
        self.assertEqual(df2["a"].values, [1, 2])

    def test_tail_returns_correct_rows(self):
        df2 = self.df.tail(2)
        self.assertEqual(df2.shape, (2, 3))
        self.assertEqual(df2["a"].values, [2, 3])

    def test_head_default(self):
        data = [{"a": i} for i in range(20)]
        df = DataFrame(data)
        h = df.head()
        self.assertEqual(h.shape, (5, 1))

    def test_iloc_row_access(self):
        row = self.df.iloc[1]
        self.assertIsInstance(row, Series)
        self.assertEqual(row.values, [2, 5, 8])

    def test_iloc_slice(self):
        sub = self.df.iloc[0:2]
        self.assertEqual(sub.shape, (2, 3))

    def test_iloc_list(self):
        sub = self.df.iloc[[0, 2]]
        self.assertEqual(sub.shape, (2, 3))

    def test_loc_boolean_indexing(self):
        mask = Series([True, False, True])
        sub = self.df.loc[mask]
        self.assertEqual(sub.shape, (2, 3))
        self.assertEqual(sub["a"].values, [1, 3])

    def test_loc_callable(self):
        sub = self.df.loc[lambda row: row["a"] > 1]
        self.assertEqual(sub.shape, (2, 3))


class TestDataFrameFilterQuery(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]})

    def test_filter_with_callable(self):
        result = self.df.filter(lambda r: r["a"] > 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["a"].values, [3, 4])

    def test_query_with_expression(self):
        result = self.df.query("a > 2")
        self.assertEqual(len(result), 2)

    def test_query_equals(self):
        result = self.df.query("a == 3")
        self.assertEqual(len(result), 1)

    def test_query_not_equals(self):
        result = self.df.query("b != 10")
        self.assertEqual(len(result), 3)

    def test_query_string_equality(self):
        df = DataFrame({"name": ["alice", "bob", "charlie"]})
        result = df.query("name == 'alice'")
        self.assertEqual(len(result), 1)

    def test_isin_filtering(self):
        result = self.df.isin("a", [1, 3])
        self.assertEqual(len(result), 2)

    def test_between_filtering(self):
        result = self.df.between("a", 2, 3)
        self.assertEqual(len(result), 2)


class TestDataFrameSortGroup(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"name": ["b", "a", "c"], "val": [30, 10, 20]})

    def test_sort_values_by_column(self):
        sorted_df = self.df.sort_values("val")
        self.assertEqual(sorted_df["val"].values, [10, 20, 30])

    def test_sort_values_descending(self):
        sorted_df = self.df.sort_values("val", ascending=False)
        self.assertEqual(sorted_df["val"].values, [30, 20, 10])

    def test_sort_values_by_string(self):
        sorted_df = self.df.sort_values("name")
        self.assertEqual(sorted_df["name"].values, ["a", "b", "c"])

    def test_group_by_sum(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        result = df.group_by("cat").sum()
        x_row = result.filter(lambda r: r["cat"] == "x")["val_sum"].values[0]
        y_row = result.filter(lambda r: r["cat"] == "y")["val_sum"].values[0]
        self.assertEqual(x_row, 3)
        self.assertEqual(y_row, 3)

    def test_group_by_mean(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [2, 4, 6]})
        result = df.group_by("cat").mean()
        x_row = result.filter(lambda r: r["cat"] == "x")["val_mean"].values[0]
        self.assertEqual(x_row, 3.0)

    def test_group_by_count(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        result = df.group_by("cat").count()
        x_count = result.filter(lambda r: r["cat"] == "x")["val_count"].values[0]
        self.assertEqual(x_count, 2)

    def test_group_by_column_access(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        gb = df.group_by("cat")
        result = gb["val"].sum()
        self.assertIsInstance(result, DataFrame)

    def test_group_by_column_attribute(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        gb = df.group_by("cat")
        result = gb.val.sum()
        self.assertIsInstance(result, DataFrame)

    def test_group_by_get_group(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        gb = df.group_by("cat")
        group = gb.get_group("x")
        self.assertEqual(len(group), 2)

    def test_group_by_ngroups(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        gb = df.group_by("cat")
        self.assertEqual(gb.ngroups, 2)

    def test_group_by_aggregate_dict(self):
        df = DataFrame({"cat": ["x", "x", "y"], "val": [1, 2, 3]})
        gb = df.group_by("cat")
        result = gb.aggregate({"val": "max"})
        self.assertIn("val_max", result.columns)

    def test_group_by_missing_column_raises(self):
        df = DataFrame({"a": [1]})
        gb = df.group_by("a")
        with self.assertRaises(AttributeError):
            gb.nonexistent_group


class TestDataFrameTransform(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    def test_apply_along_axis_0(self):
        result = self.df.apply(lambda vals: sum(vals), axis=0)
        self.assertEqual(result["a"].values[0], 6)
        self.assertEqual(result["b"].values[0], 15)

    def test_apply_along_axis_1(self):
        result = self.df.apply(lambda r: {k: v * 10 for k, v in r.items()}, axis=1)
        self.assertEqual(result["a"].values, [10, 20, 30])
        self.assertEqual(result["b"].values, [40, 50, 60])

    def test_apply_invalid_axis(self):
        with self.assertRaises(DataFrameError):
            self.df.apply(lambda x: x, axis=99)

    def test_rename_columns(self):
        renamed = self.df.rename({"a": "x", "b": "y"})
        self.assertEqual(renamed.columns, ["x", "y"])
        self.assertEqual(renamed["x"].values, [1, 2, 3])

    def test_drop_columns(self):
        dropped = self.df.drop(columns=["b"])
        self.assertEqual(dropped.columns, ["a"])
        self.assertEqual(dropped.shape, (3, 1))

    def test_drop_rows(self):
        dropped = self.df.drop(index=[0, 2])
        self.assertEqual(dropped.shape, (1, 2))
        self.assertEqual(dropped["a"].values, [2])

    def test_drop_both(self):
        dropped = self.df.drop(columns=["b"], index=[0])
        self.assertEqual(dropped.shape, (2, 1))
        self.assertEqual(dropped["a"].values, [2, 3])

    def test_set_index(self):
        df = DataFrame({"id": ["a", "b"], "val": [1, 2]})
        result = df.set_index("id")
        self.assertEqual(result.columns, ["val"])

    def test_set_index_missing_column(self):
        with self.assertRaises(DataFrameError):
            self.df.set_index("nonexistent")

    def test_reset_index(self):
        df = DataFrame({"a": [10, 20]})
        result = df.reset_index()
        self.assertIn("index", result.columns)
        self.assertEqual(result["index"].values, [0, 1])

    def test_reset_index_drop(self):
        df = DataFrame({"a": [10, 20]})
        result = df.reset_index(drop=True)
        self.assertNotIn("index", result.columns)


class TestDataFrameStats(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})

    def test_describe_returns_stats(self):
        desc = self.df.describe()
        self.assertIn("stat", desc.columns)
        stats_rows = desc["stat"].values
        self.assertIn("count", stats_rows)
        self.assertIn("mean", stats_rows)
        self.assertIn("std", stats_rows)
        self.assertIn("min", stats_rows)

    def _series_val_by_label(self, s: Series, label: str):
        idx = s.index.index(label)
        return s.values[idx]

    def test_sum_on_numeric(self):
        result = self.df.sum()
        self.assertEqual(self._series_val_by_label(result, "a"), 15)
        self.assertEqual(self._series_val_by_label(result, "b"), 150)

    def test_mean_on_numeric(self):
        result = self.df.mean()
        self.assertEqual(self._series_val_by_label(result, "a"), 3.0)
        self.assertEqual(self._series_val_by_label(result, "b"), 30.0)

    def test_median_on_numeric(self):
        result = self.df.median()
        self.assertEqual(self._series_val_by_label(result, "a"), 3.0)
        self.assertEqual(self._series_val_by_label(result, "b"), 30.0)

    def test_min_on_numeric(self):
        result = self.df.min()
        self.assertEqual(self._series_val_by_label(result, "a"), 1)

    def test_max_on_numeric(self):
        result = self.df.max()
        self.assertEqual(self._series_val_by_label(result, "b"), 50)

    def test_count(self):
        result = self.df.count()
        self.assertEqual(self._series_val_by_label(result, "a"), 5)

    def test_value_counts(self):
        df = DataFrame({"x": ["a", "b", "a", "c"]})
        counts = df.value_counts("x")
        self.assertEqual(counts["a"], 2)
        self.assertEqual(counts["b"], 1)


class TestDataFrameMergeConcat(unittest.TestCase):
    def setUp(self):
        self.left = DataFrame({"key": [1, 2], "val": ["a", "b"]})
        self.right = DataFrame({"key": [1, 3], "val2": ["x", "y"]})

    def test_merge_inner(self):
        result = self.left.merge(self.right, on="key")
        self.assertEqual(len(result), 1)
        self.assertEqual(result["val"].values[0], "a")

    def test_merge_left(self):
        result = self.left.merge(self.right, on="key", how="left")
        self.assertEqual(len(result), 2)
        self.assertIn("val2", result.columns)

    def test_merge_right(self):
        result = self.left.merge(self.right, on="key", how="right")
        self.assertEqual(len(result), 2)

    def test_merge_auto_on(self):
        df1 = DataFrame({"x": [1], "y": [10]})
        df2 = DataFrame({"x": [1], "z": [20]})
        result = df1.merge(df2)
        self.assertEqual(len(result), 1)
        self.assertIn("z", result.columns)

    def test_concat(self):
        df1 = DataFrame({"a": [1, 2]})
        df2 = DataFrame({"a": [3, 4]})
        result = DataFrame.concat([df1, df2])
        self.assertEqual(result.shape, (4, 1))

    def test_concat_empty_list(self):
        result = DataFrame.concat([])
        self.assertTrue(result.empty)

    def test_concat_different_columns(self):
        df1 = DataFrame({"a": [1]})
        df2 = DataFrame({"b": [2]})
        result = DataFrame.concat([df1, df2])
        self.assertIn("a", result.columns)
        self.assertIn("b", result.columns)


class TestDataFrameIO(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2], "b": ["x", "y"]})

    def test_to_csv_produces_output(self):
        csv_out = self.df.to_csv()
        self.assertIn("a", csv_out)
        self.assertIn("x", csv_out)

    def test_to_csv_writes_file(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            self.df.to_csv(path)
            with open(path) as f:
                content = f.read()
            self.assertIn("a,b", content)
        finally:
            os.unlink(path)

    def test_to_html_produces_output(self):
        html = self.df.to_html()
        self.assertIn("<table>", html)
        self.assertIn("<th>a</th>", html)

    def test_read_csv_static_method(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as f:
            f.write("x,y\n1,2\n3,4\n")
            path = f.name
        try:
            df = DataFrame.read_csv(path)
            self.assertEqual(df.shape, (2, 2))
            self.assertEqual(df.columns, ["x", "y"])
        finally:
            os.unlink(path)

    def test_to_json_records(self):
        js = self.df.to_json()
        parsed = json.loads(js)
        self.assertEqual(len(parsed), 2)

    def test_to_dict_records(self):
        d = self.df.to_dict()
        self.assertEqual(len(d), 2)
        self.assertEqual(d[0]["a"], 1)


class TestDataFrameMissingData(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, None, 3], "b": [None, 5, 6]})

    def test_fillna(self):
        filled = self.df.fillna(0)
        self.assertEqual(filled["a"].values, [1, 0, 3])
        self.assertEqual(filled["b"].values, [0, 5, 6])

    def test_fillna_specific_columns(self):
        filled = self.df.fillna(-1, columns=["a"])
        self.assertEqual(filled["a"].values, [1, -1, 3])
        self.assertIsNone(filled["b"].values[0])

    def test_dropna(self):
        dropped = self.df.dropna()
        self.assertEqual(len(dropped), 1)

    def test_dropna_subset(self):
        dropped = self.df.dropna(subset=["b"])
        self.assertEqual(len(dropped), 2)

    def test_dropna_axis1_raises(self):
        with self.assertRaises(DataFrameError):
            self.df.dropna(axis=1)


class TestDataFrameSample(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame({"a": list(range(100))})

    def test_sample_n(self):
        s = self.df.sample(n=10)
        self.assertEqual(len(s), 10)

    def test_sample_frac(self):
        s = self.df.sample(frac=0.1)
        self.assertEqual(len(s), 10)

    def test_sample_reproducible(self):
        s1 = self.df.sample(n=5, random_state=42)
        s2 = self.df.sample(n=5, random_state=42)
        self.assertEqual(s1["a"].values, s2["a"].values)


class TestDataFrameEdgeCases(unittest.TestCase):
    def test_empty_dataframe_shape(self):
        df = DataFrame()
        self.assertEqual(df.shape, (0, 0))
        self.assertEqual(df.size, 0)

    def test_empty_dataframe_head_tail(self):
        df = DataFrame()
        self.assertEqual(df.head().shape, (0, 0))
        self.assertEqual(df.tail().shape, (0, 0))

    def test_empty_dataframe_repr(self):
        df = DataFrame(columns=["a"])
        r = repr(df)
        self.assertIn("Empty DataFrame", r)

    def test_single_row(self):
        df = DataFrame({"a": [1]})
        self.assertEqual(df.shape, (1, 1))

    def test_iteration(self):
        df = DataFrame({"a": [1, 2], "b": [3, 4]})
        rows = list(df)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["a"], 1)

    def test_len(self):
        df = DataFrame({"a": [1, 2, 3]})
        self.assertEqual(len(df), 3)

    def test_bool_column(self):
        df = DataFrame({"a": [True, False, True]})
        self.assertEqual(df.shape, (3, 1))

    def test_setitem_new_column(self):
        df = DataFrame({"a": [1, 2]})
        df["b"] = [3, 4]
        self.assertIn("b", df.columns)
        self.assertEqual(df["b"].values, [3, 4])

    def test_setitem_scalar(self):
        df = DataFrame({"a": [1, 2]})
        df["b"] = 0
        self.assertEqual(df["b"].values, [0, 0])

    def test_join_alias(self):
        df1 = DataFrame({"id": [1], "x": [10]})
        df2 = DataFrame({"id": [1], "y": [20]})
        result = df1.join(df2, on="id")
        self.assertEqual(len(result), 1)

    def test_to_dict_list_orient(self):
        df = DataFrame({"a": [1, 2]})
        d = df.to_dict(orient="list")
        self.assertEqual(d["a"], [1, 2])

    def test_corr_matrix(self):
        df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        cm = df.corr()
        self.assertIn("a", cm.columns)

    def test_apply_map(self):
        df = DataFrame({"a": [1, 2]})
        result = df.applymap(lambda x: x * 2)
        self.assertEqual(result["a"].values, [2, 4])

    def test_map_column(self):
        df = DataFrame({"a": [1, 2, 3]})
        result = df.map("a", lambda x: x * 10)
        self.assertIsInstance(result, Series)
        self.assertEqual(result.values, [10, 20, 30])


class TestSeriesCreation(unittest.TestCase):
    def test_create_with_data(self):
        s = Series([1, 2, 3])
        self.assertEqual(len(s), 3)
        self.assertEqual(s.values, [1, 2, 3])

    def test_create_with_name(self):
        s = Series([1, 2, 3], name="col")
        self.assertEqual(s.name, "col")

    def test_create_with_index(self):
        s = Series([10, 20, 30], index=["a", "b", "c"])
        self.assertEqual(s.index, ["a", "b", "c"])

    def test_create_empty(self):
        s = Series()
        self.assertEqual(len(s), 0)
        self.assertEqual(s.values, [])

    def test_dtype_inferred(self):
        s = Series([1, 2, 3])
        self.assertEqual(s.dtype, "int64")

    def test_dtype_float(self):
        s = Series([1.5, 2.5])
        self.assertEqual(s.dtype, "float64")

    def test_dtype_string(self):
        s = Series(["a", "b"])
        self.assertEqual(s.dtype, "object")


class TestSeriesAccess(unittest.TestCase):
    def setUp(self):
        self.s = Series([10, 20, 30, 40, 50], name="nums")

    def test_getitem_by_position(self):
        self.assertEqual(self.s[0], 10)
        self.assertEqual(self.s[4], 50)

    def test_getitem_slice(self):
        sub = self.s[1:3]
        self.assertIsInstance(sub, Series)
        self.assertEqual(sub.values, [20, 30])

    def test_getitem_boolean_list(self):
        sub = self.s[[True, False, True, False, True]]
        self.assertEqual(sub.values, [10, 30, 50])

    def test_getitem_string_raises(self):
        with self.assertRaises(DataFrameError):
            self.s["invalid"]

    def test_setitem(self):
        self.s[0] = 99
        self.assertEqual(self.s[0], 99)

    def test_iteration(self):
        vals = list(self.s)
        self.assertEqual(vals, [10, 20, 30, 40, 50])

    def test_len(self):
        self.assertEqual(len(self.s), 5)


class TestSeriesArithmetic(unittest.TestCase):
    def setUp(self):
        self.a = Series([1, 2, 3])
        self.b = Series([4, 5, 6])

    def test_add(self):
        result = self.a + self.b
        self.assertEqual(result.values, [5, 7, 9])

    def test_add_scalar(self):
        result = self.a + 10
        self.assertEqual(result.values, [11, 12, 13])

    def test_sub(self):
        result = self.b - self.a
        self.assertEqual(result.values, [3, 3, 3])

    def test_mul(self):
        result = self.a * self.b
        self.assertEqual(result.values, [4, 10, 18])

    def test_truediv(self):
        result = self.a / self.b
        self.assertEqual(result.values, [0.25, 0.4, 0.5])

    def test_truediv_by_zero(self):
        result = Series([1, 2]) / Series([0, 1])
        self.assertEqual(result.values[0], float("inf"))

    def test_arith_with_none(self):
        a = Series([1, None, 3])
        b = Series([4, 5, None])
        result = a + b
        self.assertIsNone(result.values[1])
        self.assertIsNone(result.values[2])


class TestSeriesStats(unittest.TestCase):
    def setUp(self):
        self.s = Series([1, 2, 3, 4, 5], name="nums")

    def test_sum(self):
        self.assertEqual(self.s.sum(), 15)

    def test_mean(self):
        self.assertEqual(self.s.mean(), 3.0)

    def test_median_odd(self):
        self.assertEqual(self.s.median(), 3.0)

    def test_median_even(self):
        s = Series([1, 2, 3, 4])
        self.assertEqual(s.median(), 2.5)

    def test_min(self):
        self.assertEqual(self.s.min(), 1)

    def test_max(self):
        self.assertEqual(self.s.max(), 5)

    def test_std(self):
        s = Series([1, 2, 3])
        std_val = s.std()
        self.assertAlmostEqual(std_val, 1.0)

    def test_var(self):
        s = Series([1, 2, 3])
        var_val = s.var()
        self.assertAlmostEqual(var_val, 1.0)

    def test_count(self):
        s = Series([1, None, 3])
        self.assertEqual(s.count(), 2)

    def test_sum_empty_returns_0(self):
        s = Series([], name="e")
        self.assertEqual(s.sum(), 0)

    def test_mean_all_none_returns_nan(self):
        s = Series([None, None])
        self.assertTrue(math.isnan(s.mean()))

    def test_sum_non_numeric_raises(self):
        s = Series(["a", "b"])
        with self.assertRaises(DataFrameError):
            s.sum()

    def test_mean_non_numeric_raises(self):
        s = Series(["a", "b"])
        with self.assertRaises(DataFrameError):
            s.mean()


class TestSeriesTransform(unittest.TestCase):
    def setUp(self):
        self.s = Series([1, 2, 3, 4, 5], name="nums")

    def test_apply(self):
        result = self.s.apply(lambda x: x * 2)
        self.assertEqual(result.values, [2, 4, 6, 8, 10])

    def test_apply_skips_none(self):
        s = Series([1, None, 3])
        result = s.apply(lambda x: x * 2)
        self.assertEqual(result.values, [2, None, 6])

    def test_map(self):
        result = self.s.map(lambda x: x**2)
        self.assertEqual(result.values, [1, 4, 9, 16, 25])

    def test_isna(self):
        s = Series([1, None, 3])
        result = s.isna()
        self.assertEqual(result.values, [False, True, False])

    def test_dropna(self):
        s = Series([1, None, 3])
        result = s.dropna()
        self.assertEqual(result.values, [1, 3])

    def test_fillna(self):
        s = Series([1, None, 3])
        result = s.fillna(0)
        self.assertEqual(result.values, [1, 0, 3])

    def test_unique(self):
        s = Series([1, 2, 1, 3, 2])
        u = s.unique()
        self.assertEqual(len(u), 3)

    def test_value_counts(self):
        s = Series(["a", "b", "a", "c"])
        counts = s.value_counts()
        self.assertEqual(counts["a"], 2)

    def test_sort_values_ascending(self):
        s = Series([3, 1, 2])
        result = s.sort_values()
        self.assertEqual(result.values, [1, 2, 3])

    def test_sort_values_descending(self):
        s = Series([1, 3, 2])
        result = s.sort_values(ascending=False)
        self.assertEqual(result.values, [3, 2, 1])

    def test_to_list(self):
        self.assertEqual(self.s.to_list(), [1, 2, 3, 4, 5])

    def test_corr(self):
        a = Series([1, 2, 3, 4, 5])
        b = Series([2, 4, 6, 8, 10])
        c = a.corr(b)
        self.assertAlmostEqual(c, 1.0)

    def test_corr_insufficient_data(self):
        a = Series([1])
        b = Series([2])
        self.assertTrue(math.isnan(a.corr(b)))

    def test_corr_no_overlap(self):
        a = Series([None, None])
        b = Series([1, 2])
        self.assertTrue(math.isnan(a.corr(b)))

    def test_abs(self):
        s = Series([-1, 2, -3])
        result = s.abs()
        self.assertEqual(result.values, [1, 2, 3])

    def test_round(self):
        s = Series([1.234, 2.567])
        result = s.round(1)
        self.assertEqual(result.values, [1.2, 2.6])


class TestVisualization(unittest.TestCase):
    def setUp(self):
        self.x = Series([1, 2, 3, 4, 5])
        self.y = Series([2, 4, 6, 8, 10])

    def test_plot_line_returns_string(self):
        result = Plot.line(self.x, self.y)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("\u2502", result)

    def test_plot_bar_produces_output(self):
        result = Plot.bar(["a", "b", "c"], [10, 20, 15])
        self.assertIsInstance(result, str)
        self.assertIn("\u2588", result)

    def test_plot_histogram_produces_output(self):
        data = Series([1, 2, 2, 3, 3, 3, 4, 5])
        result = Plot.histogram(data)
        self.assertIsInstance(result, str)

    def test_plot_scatter_produces_output(self):
        result = Plot.scatter(self.x, self.y)
        self.assertIsInstance(result, str)
        self.assertIn("*", result)

    def test_plot_pie_produces_output(self):
        result = Plot.pie(["A", "B", "C"], [30, 50, 20])
        self.assertIsInstance(result, str)
        self.assertIn("A", result)

    def test_plot_pie_mismatched_lengths(self):
        with self.assertRaises(VisualizationError):
            Plot.pie(["A", "B"], [1, 2, 3])

    def test_plot_pie_sum_zero(self):
        with self.assertRaises(VisualizationError):
            Plot.pie(["A", "B"], [0, 0])

    def test_plot_pie_empty_data(self):
        with self.assertRaises(VisualizationError):
            Plot.pie([], [])

    def test_plot_bar_empty_data(self):
        with self.assertRaises(VisualizationError):
            Plot.bar([], [])

    def test_plot_histogram_empty_data(self):
        with self.assertRaises(VisualizationError):
            Plot.histogram(Series([None]))

    def test_plot_line_mismatched_lengths(self):
        with self.assertRaises(VisualizationError):
            Plot.line(Series([1, 2]), Series([1]))

    def test_plot_scatter_mismatched_lengths(self):
        with self.assertRaises(VisualizationError):
            Plot.scatter(Series([1, 2]), Series([1]))

    def test_set_style_changes_output(self):
        original_style = {"point": "*", "line": "\u2500"}
        set_style({"point": "@", "line": "~"})
        result = Plot.line(self.x, self.y)
        self.assertIn("@", result)
        set_style(original_style)

    def test_figure_show(self):
        fig = Figure(title="Test Chart", width=60, height=20)
        out = fig.show()
        self.assertIn("Test Chart", out)

    def test_visualization_error_exception(self):
        with self.assertRaises(VisualizationError):
            Plot.bar([], [])
        with self.assertRaises(VisualizationError):
            Plot.histogram(Series([]))
        with self.assertRaises(VisualizationError):
            Plot.pie([], [])


class TestDataInit(unittest.TestCase):
    def test_create_dataframe_factory(self):
        df = create_dataframe({"a": [1, 2]})
        self.assertIsInstance(df, DataFrame)
        self.assertEqual(df.shape, (2, 1))

    def test_create_dataframe_with_columns(self):
        df = create_dataframe([[1, 2], [3, 4]], columns=["x", "y"])
        self.assertIsInstance(df, DataFrame)
        self.assertEqual(df.columns, ["x", "y"])

    def test_module_exports(self):
        from zoya.data import __all__ as all_exports

        self.assertIn("DataFrame", all_exports)
        self.assertIn("Series", all_exports)
        self.assertIn("GroupBy", all_exports)
        self.assertIn("GroupByColumn", all_exports)
        self.assertIn("DataFrameError", all_exports)
        self.assertIn("Figure", all_exports)
        self.assertIn("Plot", all_exports)
        self.assertIn("VisualizationError", all_exports)
        self.assertIn("set_style", all_exports)
        self.assertIn("create_dataframe", all_exports)

    def test_create_dataframe_returns_dataframe(self):
        result = create_dataframe([{"x": 1}])
        self.assertIsInstance(result, DataFrame)


if __name__ == "__main__":
    unittest.main()
