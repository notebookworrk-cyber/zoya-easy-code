import csv
import json
import math
import random
from collections import Counter
from collections.abc import Callable, Iterator
from typing import Any, Union


class DataFrameError(Exception):
    pass


def _infer_type(values) -> str:
    vals = [v for v in values if v is not None]
    if not vals:
        return "object"
    types_seen = set()
    for v in vals:
        if isinstance(v, bool):
            types_seen.add("bool")
        elif isinstance(v, int):
            types_seen.add("int")
        elif isinstance(v, float):
            types_seen.add("float")
        elif isinstance(v, str):
            types_seen.add("string")
        else:
            types_seen.add("object")
    if "object" in types_seen:
        return "object"
    if "bool" in types_seen:
        return "bool"
    if "int" in types_seen and "float" not in types_seen:
        return "int64"
    if "float" in types_seen or "int" in types_seen:
        return "float64"
    if "string" in types_seen:
        return "object"
    return "object"


def _coerce_type(values, target_type: str):
    if target_type == "float64":
        return [float(v) if v is not None else None for v in values]
    if target_type == "int64":
        return [int(v) if v is not None else None for v in values]
    if target_type == "bool":
        return [bool(v) if v is not None else None for v in values]
    return list(values)


def _parse_query_expr(expr: str, row: dict) -> bool:
    expr = expr.strip()
    for op in [">=", "<=", "!=", "==", ">", "<"]:
        if op in expr:
            parts = expr.split(op, 1)
            col = parts[0].strip()
            val = parts[1].strip().strip("'\"")
            if col not in row:
                return False
            row_val = row[col]
            if row_val is None:
                return False
            try:
                num_val = float(val)
                num_row = float(row_val)
                if op == ">=":
                    return num_row >= num_val
                if op == "<=":
                    return num_row <= num_val
                if op == "!=":
                    return num_row != num_val
                if op == "==":
                    return num_row == num_val
                if op == ">":
                    return num_row > num_val
                if op == "<":
                    return num_row < num_val
            except (ValueError, TypeError):
                str_row = str(row_val)
                str_val = str(val)
                if op == "==":
                    return str_row == str_val
                if op == "!=":
                    return str_row != str_val
                if op == ">=":
                    return str_row >= str_val
                if op == "<=":
                    return str_row <= str_val
                if op == ">":
                    return str_row > str_val
                if op == "<":
                    return str_row < str_val
    return False


class Series:
    def __init__(self, data: list = None, name: str = "", index: list = None):
        self._data = list(data) if data is not None else []
        self._name = name
        self._index = index if index is not None else list(range(len(self._data)))

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def values(self) -> list:
        return self._data

    @property
    def index(self) -> list:
        return self._index

    @property
    def dtype(self) -> str:
        return _infer_type(self._data)

    def __getitem__(self, key) -> Any:
        if isinstance(key, slice):
            return Series(self._data[key], name=self._name, index=self._index[key])
        if isinstance(key, int):
            return self._data[key]
        if isinstance(key, (list, Series)):
            if isinstance(key, Series):
                key = key.values
            return Series(
                [self._data[i] for i, k in enumerate(key) if k], name=self._name
            )
        if isinstance(key, str):
            raise DataFrameError("String key not supported on Series")
        if isinstance(key, Series):
            return Series(
                [v for v, k in zip(self._data, key.values, strict=False) if k],
                name=self._name,
            )
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        n = len(self._data)
        lines = [f"Series: {self._name} (dtype: {self.dtype})"]
        lines.append(f"Length: {n}")
        for i in range(min(n, 10)):
            lines.append(f"{self._index[i]:>5}  {self._data[i]}")
        if n > 10:
            lines.append("     ...")
        return "\n".join(lines)

    def _arith(self, other, op):
        if isinstance(other, Series):
            result = [
                op(a, b) if a is not None and b is not None else None
                for a, b in zip(self._data, other._data, strict=False)
            ]
        else:
            result = [op(v, other) if v is not None else None for v in self._data]
        return Series(result, name=self._name, index=self._index)

    def __add__(self, other) -> "Series":
        return self._arith(other, lambda a, b: a + b)

    def __sub__(self, other) -> "Series":
        return self._arith(other, lambda a, b: a - b)

    def __mul__(self, other) -> "Series":
        return self._arith(other, lambda a, b: a * b)

    def __truediv__(self, other) -> "Series":
        return self._arith(other, lambda a, b: a / b if b != 0 else float("inf"))

    def sum(self):
        vals = [v for v in self._data if v is not None]
        if not vals:
            return 0
        if all(isinstance(v, (int, float)) for v in vals):
            return sum(vals)
        raise DataFrameError("sum requires numeric data")

    def mean(self):
        vals = [v for v in self._data if v is not None]
        if not vals:
            return float("nan")
        if all(isinstance(v, (int, float)) for v in vals):
            return sum(vals) / len(vals)
        raise DataFrameError("mean requires numeric data")

    def median(self):
        vals = sorted([v for v in self._data if v is not None])
        if not vals:
            return float("nan")
        n = len(vals)
        mid = n // 2
        if n % 2 == 0:
            return (vals[mid - 1] + vals[mid]) / 2
        return vals[mid]

    def min(self):
        vals = [v for v in self._data if v is not None]
        if not vals:
            return None
        return min(vals)

    def max(self):
        vals = [v for v in self._data if v is not None]
        if not vals:
            return None
        return max(vals)

    def std(self):
        vals = [v for v in self._data if v is not None]
        if len(vals) < 2:
            return float("nan")
        m = sum(vals) / len(vals)
        var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
        return math.sqrt(var)

    def var(self):
        vals = [v for v in self._data if v is not None]
        if len(vals) < 2:
            return float("nan")
        m = sum(vals) / len(vals)
        return sum((x - m) ** 2 for x in vals) / (len(vals) - 1)

    def count(self):
        return len([v for v in self._data if v is not None])

    def apply(self, func: Callable) -> "Series":
        return Series(
            [func(v) if v is not None else None for v in self._data],
            name=self._name,
            index=self._index,
        )

    def map(self, func: Callable) -> "Series":
        return self.apply(func)

    def isna(self) -> "Series":
        return Series(
            [v is None for v in self._data], name=self._name, index=self._index
        )

    def dropna(self) -> "Series":
        return Series([v for v in self._data if v is not None], name=self._name)

    def fillna(self, value) -> "Series":
        return Series(
            [v if v is not None else value for v in self._data],
            name=self._name,
            index=self._index,
        )

    def unique(self) -> list:
        seen = set()
        result = []
        for v in self._data:
            if v not in seen:
                seen.add(v)
                result.append(v)
        return result

    def value_counts(self) -> dict:
        counts = Counter(self._data)
        return dict(counts.most_common())

    def sort_values(self, ascending: bool = True) -> "Series":
        pairs = list(zip(self._index, self._data, strict=False))
        pairs.sort(key=lambda x: (x[1] is None, x[1]), reverse=not ascending)
        sorted_idx = [p[0] for p in pairs]
        sorted_data = [p[1] for p in pairs]
        return Series(sorted_data, name=self._name, index=sorted_idx)

    def abs(self) -> "Series":
        return self.apply(lambda x: abs(x) if isinstance(x, (int, float)) else x)

    def round(self, decimals: int = 0) -> "Series":
        return self.apply(lambda x: round(x, decimals) if isinstance(x, float) else x)

    def to_list(self) -> list:
        return list(self._data)

    def corr(self, other: "Series") -> float:
        pairs = [
            (a, b)
            for a, b in zip(self._data, other._data, strict=False)
            if a is not None and b is not None
        ]
        n = len(pairs)
        if n < 2:
            return float("nan")
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mx = sum(xs) / n
        my = sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
        den = math.sqrt(sum((x - mx) ** 2 for x in xs)) * math.sqrt(
            sum((y - my) ** 2 for y in ys)
        )
        if den == 0:
            return float("nan")
        return num / den

    def _repr_html_(self) -> str:
        rows = [
            f"<tr><td>{i}</td><td>{v}</td></tr>"
            for i, v in zip(self._index[:10], self._data[:10], strict=False)
        ]
        more = "<tr><td>...</td><td>...</td></tr>" if len(self._data) > 10 else ""
        return f"<table><thead><tr><th></th><th>{self._name}</th></tr></thead><tbody>{''.join(rows)}{more}</tbody></table>"


class GroupBy:
    def __init__(self, df: "DataFrame", keys: list[str]):
        self._df = df
        self._keys = keys
        self._groups = {}
        for i, row in enumerate(df._data):
            key = tuple(row[k] for k in keys)
            if key not in self._groups:
                self._groups[key] = []
            self._groups[key].append(i)

    @property
    def groups(self) -> dict:
        return {k: list(v) for k, v in self._groups.items()}

    @property
    def ngroups(self) -> int:
        return len(self._groups)

    def __getattr__(self, name: str) -> "GroupByColumn":
        if name in self._df.columns:
            return GroupByColumn(self, name)
        raise AttributeError(f"No column '{name}'")

    def __getitem__(self, key) -> "GroupByColumn":
        return GroupByColumn(self, key)

    def aggregate(self, funcs: dict[str, str]) -> "DataFrame":
        result = []
        for key, indices in self._groups.items():
            row = dict(zip(self._keys, key, strict=False))
            for col, func_name in funcs.items():
                col_vals = [
                    self._df._data[i][col]
                    for i in indices
                    if self._df._data[i][col] is not None
                ]
                if not col_vals:
                    row[f"{col}_{func_name}"] = None
                else:
                    row[f"{col}_{func_name}"] = self._apply_func(col_vals, func_name)
            result.append(row)
        return DataFrame(result)

    def _apply_func(self, vals: list, func_name: str):
        if func_name == "sum":
            return sum(vals)
        if func_name == "mean":
            return sum(vals) / len(vals)
        if func_name == "median":
            svals = sorted(vals)
            n = len(svals)
            mid = n // 2
            if n % 2 == 0:
                return (svals[mid - 1] + svals[mid]) / 2
            return svals[mid]
        if func_name == "min":
            return min(vals)
        if func_name == "max":
            return max(vals)
        if func_name == "count":
            return len(vals)
        if func_name == "std":
            if len(vals) < 2:
                return float("nan")
            m = sum(vals) / len(vals)
            return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
        if func_name == "var":
            if len(vals) < 2:
                return float("nan")
            m = sum(vals) / len(vals)
            return sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
        if func_name == "first":
            return vals[0]
        if func_name == "last":
            return vals[-1]
        raise DataFrameError(f"Unknown function: {func_name}")

    def _agg_all(self, func_name: str) -> "DataFrame":
        cols = [c for c in self._df.columns if c not in self._keys]
        funcs = dict.fromkeys(cols, func_name)
        return self.aggregate(funcs)

    def sum(self) -> "DataFrame":
        return self._agg_all("sum")

    def mean(self) -> "DataFrame":
        return self._agg_all("mean")

    def median(self) -> "DataFrame":
        return self._agg_all("median")

    def min(self) -> "DataFrame":
        return self._agg_all("min")

    def max(self) -> "DataFrame":
        return self._agg_all("max")

    def count(self) -> "DataFrame":
        return self._agg_all("count")

    def std(self) -> "DataFrame":
        return self._agg_all("std")

    def var(self) -> "DataFrame":
        return self._agg_all("var")

    def first(self) -> "DataFrame":
        return self._agg_all("first")

    def last(self) -> "DataFrame":
        return self._agg_all("last")

    def apply(self, func: Callable) -> "DataFrame":
        result = []
        for key, indices in self._groups.items():
            sub_df = DataFrame([self._df._data[i] for i in indices])
            applied = func(sub_df)
            if isinstance(applied, DataFrame):
                for row in applied._data:
                    agg_row = dict(zip(self._keys, key, strict=False))
                    agg_row.update(row)
                    result.append(agg_row)
            else:
                agg_row = dict(zip(self._keys, key, strict=False))
                agg_row["result"] = applied
                result.append(agg_row)
        return DataFrame(result)

    def get_group(self, key) -> "DataFrame":
        key = tuple(key) if isinstance(key, tuple) else (key,)
        if key not in self._groups:
            raise DataFrameError(f"Group {key} not found")
        indices = self._groups[key]
        return DataFrame([self._df._data[i] for i in indices])


class GroupByColumn:
    def __init__(self, groupby: GroupBy, column: str):
        self._groupby = groupby
        self._column = column

    def aggregate(self, func_name: str) -> "DataFrame":
        return self._groupby.aggregate({self._column: func_name})

    def sum(self) -> "DataFrame":
        return self.aggregate("sum")

    def mean(self) -> "DataFrame":
        return self.aggregate("mean")

    def median(self) -> "DataFrame":
        return self.aggregate("median")

    def min(self) -> "DataFrame":
        return self.aggregate("min")

    def max(self) -> "DataFrame":
        return self.aggregate("max")

    def count(self) -> "DataFrame":
        return self.aggregate("count")

    def std(self) -> "DataFrame":
        return self.aggregate("std")

    def var(self) -> "DataFrame":
        return self.aggregate("var")

    def first(self) -> "DataFrame":
        return self.aggregate("first")

    def last(self) -> "DataFrame":
        return self.aggregate("last")

    def apply(self, func: Callable) -> "DataFrame":
        result = []
        for key, indices in self._groupby._groups.items():
            vals = [self._groupby._df._data[i][self._column] for i in indices]
            result.append(
                {
                    **dict(zip(self._groupby._keys, key, strict=False)),
                    self._column: func(vals),
                }
            )
        return DataFrame(result)


class DataFrame:
    def __init__(self, data=None, columns: list[str] = None):
        self._data = []
        if data is None:
            if columns:
                self._columns = list(columns)
            else:
                self._columns = []
            return

        if isinstance(data, list):
            if not data:
                self._columns = list(columns) if columns else []
                return
            if isinstance(data[0], dict):
                self._data = [dict(row) for row in data]
                self._columns = list(data[0].keys()) if not columns else list(columns)
            elif isinstance(data[0], list):
                if not columns:
                    self._columns = [f"col{i}" for i in range(len(data[0]))]
                else:
                    self._columns = list(columns)
                self._data = [
                    dict(zip(self._columns, row, strict=False)) for row in data
                ]
                for row in self._data:
                    for c in self._columns:
                        if c not in row:
                            row[c] = None
            else:
                if columns:
                    self._columns = list(columns)
                    self._data = [dict(zip(columns, data, strict=False))]
                else:
                    self._columns = ["col0"]
                    self._data = [{"col0": v} for v in data]
        elif isinstance(data, dict):
            self._columns = list(data.keys()) if not columns else list(columns)
            if self._columns:
                n = max((len(v) for v in data.values()), default=0)
                self._data = []
                for i in range(n):
                    row = {}
                    for c in self._columns:
                        vals = data.get(c, [])
                        row[c] = vals[i] if i < len(vals) else None
                    self._data.append(row)

    @property
    def columns(self) -> list[str]:
        return self._columns

    @columns.setter
    def columns(self, value: list[str]):
        if len(value) != len(self._columns):
            raise DataFrameError("New columns must match current number of columns")
        self._columns = list(value)

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self._data), len(self._columns))

    @property
    def dtypes(self) -> dict[str, str]:
        return {c: _infer_type(self[c].values) for c in self._columns}

    @property
    def empty(self) -> bool:
        return len(self._data) == 0

    @property
    def size(self) -> int:
        return len(self._data) * len(self._columns)

    def __getitem__(self, key) -> Union["DataFrame", Series]:
        if isinstance(key, str):
            return self._get_column(key)
        if isinstance(key, list):
            return DataFrame(
                [{k: row[k] for k in key} for row in self._data], columns=key
            )
        if isinstance(key, Series):
            bools = key.values
            return DataFrame(
                [row for row, b in zip(self._data, bools, strict=False) if b],
                columns=self._columns,
            )
        raise DataFrameError(f"Invalid key type: {type(key)}")

    def _get_column(self, name: str) -> Series:
        if name not in self._columns:
            raise DataFrameError(f"Column '{name}' not found")
        data = [row[name] for row in self._data]
        return Series(data, name=name)

    def __setitem__(self, key, value):
        if isinstance(value, Series):
            value = value.values
        if isinstance(value, list) and len(value) == len(self._data):
            for i, row in enumerate(self._data):
                row[key] = value[i]
        elif not isinstance(value, list):
            for row in self._data:
                row[key] = value
        if key not in self._columns:
            self._columns.append(key)

    def __getattr__(self, name: str) -> Series:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._columns:
            return self._get_column(name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    @property
    def iloc(self):
        class _ILocIndexer:
            def __init__(self, df):
                self._df = df

            def __getitem__(self, key):
                if isinstance(key, int):
                    row = dict(self._df._data[key])
                    return Series(
                        [row[c] for c in self._df._columns], index=self._df._columns
                    )
                if isinstance(key, slice):
                    rows = self._df._data[key]
                    return DataFrame(rows, columns=self._df._columns)
                if isinstance(key, list):
                    rows = [self._df._data[i] for i in key]
                    return DataFrame(rows, columns=self._df._columns)
                raise DataFrameError(f"Invalid iloc key: {key}")

        return _ILocIndexer(self)

    @property
    def loc(self):
        class _LocIndexer:
            def __init__(self, df):
                self._df = df

            def __getitem__(self, key):
                if isinstance(key, Series):
                    bools = key.values
                    return DataFrame(
                        [
                            row
                            for row, b in zip(self._df._data, bools, strict=False)
                            if b
                        ],
                        columns=self._df._columns,
                    )
                if callable(key):
                    return DataFrame(
                        [row for row in self._df._data if key(row)],
                        columns=self._df._columns,
                    )
                raise DataFrameError("loc requires a boolean Series or callable")

        return _LocIndexer(self)

    def head(self, n: int = 5) -> "DataFrame":
        return DataFrame(self._data[:n], columns=self._columns)

    def tail(self, n: int = 5) -> "DataFrame":
        return DataFrame(self._data[-n:], columns=self._columns)

    def sample(
        self, n: int = None, frac: float = None, random_state: int = None
    ) -> "DataFrame":
        rng = random.Random(random_state) if random_state is not None else random
        total = len(self._data)
        if n is not None:
            k = min(n, total)
        elif frac is not None:
            k = int(total * frac)
        else:
            k = total
        indices = rng.sample(range(total), k)
        return DataFrame([self._data[i] for i in indices], columns=self._columns)

    def filter(self, condition: Callable) -> "DataFrame":
        return DataFrame(
            [row for row in self._data if condition(row)], columns=self._columns
        )

    def query(self, expr: str) -> "DataFrame":
        return DataFrame(
            [row for row in self._data if _parse_query_expr(expr, row)],
            columns=self._columns,
        )

    def isin(self, column: str, values: list) -> "DataFrame":
        val_set = set(values)
        return DataFrame(
            [row for row in self._data if row.get(column) in val_set],
            columns=self._columns,
        )

    def between(self, column: str, low, high) -> "DataFrame":
        return DataFrame(
            [row for row in self._data if low <= row.get(column) <= high],
            columns=self._columns,
        )

    def dropna(self, axis: int = 0, subset: list[str] = None) -> "DataFrame":
        if axis == 0:
            cols = subset or self._columns
            return DataFrame(
                [
                    row
                    for row in self._data
                    if all(row.get(c) is not None for c in cols)
                ],
                columns=self._columns,
            )
        raise DataFrameError("axis=1 dropna not supported")

    def fillna(self, value, columns: list[str] = None) -> "DataFrame":
        cols = columns or self._columns
        new_data = []
        for row in self._data:
            new_row = dict(row)
            for c in cols:
                if new_row.get(c) is None:
                    new_row[c] = value
            new_data.append(new_row)
        return DataFrame(new_data, columns=self._columns)

    def sort_values(self, by: str | list[str], ascending: bool = True) -> "DataFrame":
        keys = [by] if isinstance(by, str) else list(by)

        def sort_key(row):
            return tuple((row[k] if row[k] is not None else "") for k in keys)

        sorted_data = sorted(self._data, key=sort_key, reverse=not ascending)
        return DataFrame(sorted_data, columns=self._columns)

    def group_by(self, by: str | list[str]) -> GroupBy:
        keys = [by] if isinstance(by, str) else list(by)
        return GroupBy(self, keys)

    def aggregate(self, agg_dict: dict[str, str]) -> "DataFrame":
        result = {}
        for col, func_name in agg_dict.items():
            vals = [row[col] for row in self._data if row[col] is not None]
            if func_name == "sum":
                result[col] = sum(vals)
            elif func_name == "mean":
                result[col] = sum(vals) / len(vals) if vals else None
            elif func_name == "median":
                svals = sorted(vals)
                n = len(svals)
                mid = n // 2
                if n % 2 == 0 and n > 0:
                    result[col] = (svals[mid - 1] + svals[mid]) / 2
                else:
                    result[col] = svals[mid] if vals else None
            elif func_name == "min":
                result[col] = min(vals) if vals else None
            elif func_name == "max":
                result[col] = max(vals) if vals else None
            elif func_name == "count":
                result[col] = len(vals)
            elif func_name == "std":
                if len(vals) < 2:
                    result[col] = None
                else:
                    m = sum(vals) / len(vals)
                    result[col] = math.sqrt(
                        sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
                    )
            elif func_name == "var":
                if len(vals) < 2:
                    result[col] = None
                else:
                    m = sum(vals) / len(vals)
                    result[col] = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
            else:
                raise DataFrameError(f"Unknown function: {func_name}")
        return DataFrame([result])

    def apply(self, func: Callable, axis: int = 0) -> "DataFrame":
        if axis == 0:
            result = {}
            for c in self._columns:
                vals = [row[c] for row in self._data]
                applied = func(vals)
                if isinstance(applied, list):
                    result[c] = applied
                else:
                    result[c] = applied
            if result and isinstance(list(result.values())[0], list):
                n = len(list(result.values())[0])
                return DataFrame(
                    [{c: result[c][i] for c in self._columns} for i in range(n)],
                    columns=self._columns,
                )
            return DataFrame([result])
        elif axis == 1:
            return DataFrame(
                [
                    (
                        func(row)
                        if isinstance(func(row), dict)
                        else {c: func(row[c]) for c in self._columns}
                    )
                    for row in self._data
                ],
                columns=self._columns,
            )
        raise DataFrameError(f"Invalid axis: {axis}")

    def applymap(self, func: Callable) -> "DataFrame":
        new_data = []
        for row in self._data:
            new_data.append({c: func(v) for c, v in row.items()})
        return DataFrame(new_data, columns=self._columns)

    def map(self, column: str, func: Callable) -> Series:
        return self[column].apply(func)

    def rename(self, columns: dict[str, str]) -> "DataFrame":
        mapping = dict(columns.items())
        new_cols = [mapping.get(c, c) for c in self._columns]
        new_data = []
        for row in self._data:
            new_row = {mapping.get(k, k): v for k, v in row.items()}
            new_data.append(new_row)
        return DataFrame(new_data, columns=new_cols)

    def drop(self, columns: list[str] = None, index: list[int] = None) -> "DataFrame":
        new_data = list(self._data)
        if index is not None:
            idx_set = set(index)
            new_data = [row for i, row in enumerate(new_data) if i not in idx_set]
        if columns is not None:
            col_set = set(columns)
            new_cols = [c for c in self._columns if c not in col_set]
            new_data = [
                {k: v for k, v in row.items() if k not in col_set} for row in new_data
            ]
            return DataFrame(new_data, columns=new_cols)
        return DataFrame(new_data, columns=self._columns)

    def reset_index(self, drop: bool = False) -> "DataFrame":
        new_data = []
        for i, row in enumerate(self._data):
            new_row = {"index": i, **row} if not drop else dict(row)
            new_data.append(new_row)
        new_cols = (["index"] + self._columns) if not drop else list(self._columns)
        return DataFrame(new_data, columns=new_cols)

    def set_index(self, column: str) -> "DataFrame":
        if column not in self._columns:
            raise DataFrameError(f"Column '{column}' not found")
        return DataFrame(
            [{k: v for k, v in row.items() if k != column} for row in self._data],
            columns=[c for c in self._columns if c != column],
        )

    def describe(self) -> "DataFrame":
        stats = {}
        for c in self._columns:
            vals = [
                row[c] for row in self._data if isinstance(row.get(c), (int, float))
            ]
            if vals:
                n = len(vals)
                s = sum(vals)
                m = s / n
                svals = sorted(vals)
                mid = n // 2
                median = svals[mid] if n % 2 == 1 else (svals[mid - 1] + svals[mid]) / 2
                var = sum((x - m) ** 2 for x in vals) / (n - 1) if n > 1 else 0
                std = math.sqrt(var)
                stats[c] = {
                    "count": n,
                    "mean": m,
                    "std": std,
                    "min": min(vals),
                    "25%": svals[n // 4] if n > 0 else None,
                    "50%": median,
                    "75%": svals[3 * n // 4] if n > 0 else None,
                    "max": max(vals),
                }
        rows = []
        stat_names = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
        for sname in stat_names:
            row = {"stat": sname}
            for c in self._columns:
                if c in stats and sname in stats[c]:
                    row[c] = stats[c][sname]
                else:
                    row[c] = None
            rows.append(row)
        return DataFrame(rows, columns=["stat"] + self._columns)

    def sum(self) -> Series:
        result = []
        for c in self._columns:
            vals = [
                row[c] for row in self._data if isinstance(row.get(c), (int, float))
            ]
            result.append(sum(vals) if vals else 0)
        return Series(result, name="sum", index=self._columns)

    def mean(self) -> Series:
        result = []
        for c in self._columns:
            vals = [
                row[c] for row in self._data if isinstance(row.get(c), (int, float))
            ]
            result.append(sum(vals) / len(vals) if vals else float("nan"))
        return Series(result, name="mean", index=self._columns)

    def median(self) -> Series:
        result = []
        for c in self._columns:
            vals = sorted(
                [row[c] for row in self._data if isinstance(row.get(c), (int, float))]
            )
            if not vals:
                result.append(float("nan"))
            else:
                n = len(vals)
                mid = n // 2
                if n % 2 == 0:
                    result.append((vals[mid - 1] + vals[mid]) / 2)
                else:
                    result.append(vals[mid])
        return Series(result, name="median", index=self._columns)

    def min(self) -> Series:
        result = []
        for c in self._columns:
            vals = [row[c] for row in self._data if row.get(c) is not None]
            result.append(min(vals) if vals else None)
        return Series(result, name="min", index=self._columns)

    def max(self) -> Series:
        result = []
        for c in self._columns:
            vals = [row[c] for row in self._data if row.get(c) is not None]
            result.append(max(vals) if vals else None)
        return Series(result, name="max", index=self._columns)

    def std(self) -> Series:
        result = []
        for c in self._columns:
            vals = [
                row[c] for row in self._data if isinstance(row.get(c), (int, float))
            ]
            if len(vals) < 2:
                result.append(float("nan"))
            else:
                m = sum(vals) / len(vals)
                result.append(
                    math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
                )
        return Series(result, name="std", index=self._columns)

    def var(self) -> Series:
        result = []
        for c in self._columns:
            vals = [
                row[c] for row in self._data if isinstance(row.get(c), (int, float))
            ]
            if len(vals) < 2:
                result.append(float("nan"))
            else:
                m = sum(vals) / len(vals)
                result.append(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
        return Series(result, name="var", index=self._columns)

    def count(self) -> Series:
        result = []
        for c in self._columns:
            result.append(sum(1 for row in self._data if row.get(c) is not None))
        return Series(result, name="count", index=self._columns)

    def corr(self) -> "DataFrame":
        num_cols = [c for c in self._columns if self._is_numeric(c)]
        len(num_cols)
        corr_data = {c: [] for c in num_cols}
        for c1 in num_cols:
            for c2 in num_cols:
                pairs = [
                    (row[c1], row[c2])
                    for row in self._data
                    if isinstance(row.get(c1), (int, float))
                    and isinstance(row.get(c2), (int, float))
                ]
                if len(pairs) < 2:
                    corr_data[c1].append(float("nan"))
                else:
                    xs = [p[0] for p in pairs]
                    ys = [p[1] for p in pairs]
                    mx = sum(xs) / len(xs)
                    my = sum(ys) / len(ys)
                    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
                    den = math.sqrt(sum((x - mx) ** 2 for x in xs)) * math.sqrt(
                        sum((y - my) ** 2 for y in ys)
                    )
                    corr_data[c1].append(num / den if den != 0 else float("nan"))
        return DataFrame(corr_data, columns=num_cols)

    def cov(self) -> "DataFrame":
        num_cols = [c for c in self._columns if self._is_numeric(c)]
        len(num_cols)
        cov_data = {c: [] for c in num_cols}
        for c1 in num_cols:
            for c2 in num_cols:
                pairs = [
                    (row[c1], row[c2])
                    for row in self._data
                    if isinstance(row.get(c1), (int, float))
                    and isinstance(row.get(c2), (int, float))
                ]
                if len(pairs) < 2:
                    cov_data[c1].append(float("nan"))
                else:
                    xs = [p[0] for p in pairs]
                    ys = [p[1] for p in pairs]
                    mx = sum(xs) / len(xs)
                    my = sum(ys) / len(ys)
                    cov_data[c1].append(
                        sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
                        / (len(xs) - 1)
                    )
        return DataFrame(cov_data, columns=num_cols)

    def _is_numeric(self, column: str) -> bool:
        return self.dtypes.get(column) in ("int64", "float64")

    def value_counts(self, column: str) -> dict:
        return Counter(row[column] for row in self._data if row.get(column) is not None)

    def unique(self, column: str) -> list:
        seen = set()
        result = []
        for row in self._data:
            v = row.get(column)
            if v not in seen:
                seen.add(v)
                result.append(v)
        return result

    def nunique(self, column: str) -> int:
        return len(
            {row.get(column) for row in self._data if row.get(column) is not None}
        )

    def merge(
        self, right: "DataFrame", on: str = None, how: str = "inner"
    ) -> "DataFrame":
        if on is None:
            common = [c for c in self._columns if c in right._columns]
            if not common:
                raise DataFrameError("No common columns to merge on")
            on = common[0]
        result = []
        right_lookup = {}
        for rrow in right._data:
            key = rrow[on]
            if key not in right_lookup:
                right_lookup[key] = []
            right_lookup[key].append(rrow)

        left_keys = set()
        for lrow in self._data:
            key = lrow[on]
            left_keys.add(key)
            matches = right_lookup.get(key, [])
            if matches:
                for rrow in matches:
                    merged = dict(lrow)
                    for c, v in rrow.items():
                        if c != on:
                            merged[c] = v
                    result.append(merged)
            elif how in ("left", "outer"):
                merged = dict(lrow)
                for c in right._columns:
                    if c != on:
                        merged[c] = None
                result.append(merged)

        if how in ("right", "outer"):
            for key, rrows in right_lookup.items():
                if key not in left_keys:
                    for rrow in rrows:
                        merged = {}
                        for c in self._columns:
                            merged[c] = rrow.get(c) if c == on else None
                        for c, v in rrow.items():
                            if c != on:
                                merged[c] = v
                        result.append(merged)

        all_cols = list(self._columns)
        for c in right._columns:
            if c not in all_cols:
                all_cols.append(c)
        return DataFrame(result, columns=all_cols)

    def join(
        self, right: "DataFrame", on: str = None, how: str = "left"
    ) -> "DataFrame":
        return self.merge(right, on=on, how=how)

    @staticmethod
    def concat(dfs: list["DataFrame"], axis: int = 0) -> "DataFrame":
        if not dfs:
            return DataFrame()
        if axis == 0:
            all_cols = []
            seen = set()
            for df in dfs:
                for c in df._columns:
                    if c not in seen:
                        all_cols.append(c)
                        seen.add(c)
            all_data = []
            for df in dfs:
                for row in df._data:
                    new_row = {}
                    for c in all_cols:
                        new_row[c] = row.get(c)
                    all_data.append(new_row)
            return DataFrame(all_data, columns=all_cols)
        raise DataFrameError("axis=1 concat not supported")

    def to_csv(self, path: str = None) -> str:
        import io

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self._columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(self._data)
        result = buf.getvalue()
        if path:
            with open(path, "w", newline="") as f:
                f.write(result)
        return result

    def to_json(self, path: str = None, orient: str = "records") -> str:
        if orient == "records":
            result = json.dumps(self._data, default=str, indent=2)
        elif orient == "list":
            result = json.dumps(
                {c: [row[c] for row in self._data] for c in self._columns},
                default=str,
                indent=2,
            )
        elif orient == "split":
            result = json.dumps(
                {
                    "columns": self._columns,
                    "index": list(range(len(self._data))),
                    "data": [[row[c] for c in self._columns] for row in self._data],
                },
                default=str,
                indent=2,
            )
        else:
            result = json.dumps(self._data, default=str, indent=2)
        if path:
            with open(path, "w") as f:
                f.write(result)
        return result

    def to_dict(self, orient: str = "records") -> list[dict]:
        if orient == "records":
            return [dict(row) for row in self._data]
        if orient == "list":
            return {c: [row[c] for row in self._data] for c in self._columns}
        raise DataFrameError(f"Unsupported orient: {orient}")

    def to_html(self) -> str:
        rows_html = []
        for row in self._data:
            cells = "".join(f"<td>{row.get(c, '')}</td>" for c in self._columns)
            rows_html.append(f"<tr>{cells}</tr>")
        header = "".join(f"<th>{c}</th>" for c in self._columns)
        return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows_html)}</tbody></table>"

    @staticmethod
    def read_csv(path: str) -> "DataFrame":
        with open(path) as f:
            reader = csv.DictReader(f)
            data = [dict(row) for row in reader]
        return DataFrame(data)

    @staticmethod
    def read_json(path: str) -> "DataFrame":
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return DataFrame(data)
        if isinstance(data, dict):
            return DataFrame(data)
        raise DataFrameError("Invalid JSON format for DataFrame")

    def __iter__(self) -> Iterator[dict]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        nrows = len(self._data)
        ncols = len(self._columns)
        if nrows == 0:
            return f"Empty DataFrame\nColumns: {self._columns}"
        result = [f"DataFrame ({nrows} rows x {ncols} cols)"]
        result.append(f"Columns: {', '.join(self._columns)}")
        result.append("")
        col_widths = [max(len(str(c)), 5) for c in self._columns]
        for row in self._data[:10]:
            cells = []
            for c, w in zip(self._columns, col_widths, strict=False):
                val = str(row.get(c, ""))
                cells.append(val.ljust(w)[:w])
            result.append("  ".join(cells))
        if nrows > 10:
            result.append(f"... ({nrows - 10} more rows)")
        return "\n".join(result)

    def _repr_html_(self) -> str:
        rows_html = []
        for row in self._data[:100]:
            cells = "".join(f"<td>{row.get(c, '')}</td>" for c in self._columns)
            rows_html.append(f"<tr>{cells}</tr>")
        header = "".join(f"<th>{c}</th>" for c in self._columns)
        n = len(self._data)
        more = (
            f"<tr><td colspan='{len(self._columns)}'>... {n - 100} more rows</td></tr>"
            if n > 100
            else ""
        )
        return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows_html)}{more}</tbody></table>"
