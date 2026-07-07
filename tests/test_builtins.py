from __future__ import annotations

import math
import random

import pytest

from zoya.builtins import (
    DICT_METHODS,
    LIST_METHODS,
    STRING_METHODS,
    zoya_abs,
    zoya_bin,
    zoya_bool,
    zoya_dict,
    zoya_float,
    zoya_hex,
    zoya_int,
    zoya_len,
    zoya_list,
    zoya_max,
    zoya_min,
    zoya_print,
    zoya_random,
    zoya_round,
    zoya_sleep,
    zoya_str,
    zoya_sum,
    zoya_type,
)


class TestZoyaPrint:
    def test_print_basic(self) -> None:
        zoya_print("hello")

    def test_print_sep_end(self) -> None:
        zoya_print("a", "b", sep=",", end="!")
        zoya_print("done")


class TestZoyaLen:
    def test_len_list(self) -> None:
        assert zoya_len([1, 2, 3]) == 3

    def test_len_string(self) -> None:
        assert zoya_len("hello") == 5

    def test_len_dict(self) -> None:
        assert zoya_len({"a": 1}) == 1


class TestZoyaType:
    def test_type_int(self) -> None:
        assert zoya_type(42) == "int"

    def test_type_str(self) -> None:
        assert zoya_type("hello") == "str"


class TestZoyaConversions:
    def test_int(self) -> None:
        assert zoya_int("42") == 42

    def test_float(self) -> None:
        assert zoya_float("3.14") == 3.14

    def test_str(self) -> None:
        assert zoya_str(42) == "42"

    def test_bool(self) -> None:
        assert zoya_bool(1) is True
        assert zoya_bool(0) is False


class TestZoyaRange:
    def test_range_one_arg(self) -> None:
        from zoya.builtins import zoya_range

        assert zoya_range(5) == [0, 1, 2, 3, 4]


class TestZoyaAbs:
    def test_abs_positive(self) -> None:
        assert zoya_abs(5) == 5

    def test_abs_negative(self) -> None:
        assert zoya_abs(-5) == 5


class TestZoyaRound:
    def test_round_basic(self) -> None:
        assert zoya_round(3.14159, 2) == 3.14

    def test_round_default_ndigits(self) -> None:
        assert zoya_round(3.5) == 4.0


class TestZoyaMin:
    def test_min_basic(self) -> None:
        assert zoya_min(3, 1, 2) == 1

    def test_min_no_args(self) -> None:
        with pytest.raises(TypeError):
            zoya_min()


class TestZoyaMax:
    def test_max_basic(self) -> None:
        assert zoya_max(1, 3, 2) == 3

    def test_max_no_args(self) -> None:
        with pytest.raises(TypeError):
            zoya_max()


class TestZoyaRandom:
    def test_random_no_args(self) -> None:
        val = zoya_random()
        assert 0 <= val < 1

    def test_random_one_arg(self) -> None:
        val = zoya_random(10)
        assert 0 <= val < 10

    def test_random_two_args(self) -> None:
        val = zoya_random(5, 10)
        assert 5 <= val <= 10


class TestZoyaSleep:
    def test_sleep(self) -> None:
        zoya_sleep(0.001)


class TestZoyaList:
    def test_list_no_args(self) -> None:
        assert zoya_list() == []

    def test_list_from_iterable(self) -> None:
        assert zoya_list("abc") == ["a", "b", "c"]


class TestZoyaDict:
    def test_dict_no_args(self) -> None:
        assert zoya_dict() == {}

    def test_dict_kwargs(self) -> None:
        assert zoya_dict(a=1, b=2) == {"a": 1, "b": 2}

    def test_dict_from_pairs(self) -> None:
        assert zoya_dict([("a", 1)]) == {"a": 1}


class TestZoyaSum:
    def test_sum_basic(self) -> None:
        assert zoya_sum([1, 2, 3]) == 6

    def test_sum_empty(self) -> None:
        assert zoya_sum([]) == 0


class TestZoyaHex:
    def test_hex(self) -> None:
        assert zoya_hex(255) == "0xff"


class TestZoyaBin:
    def test_bin(self) -> None:
        assert zoya_bin(10) == "0b1010"


class TestStringMethods:
    def test_upper(self) -> None:
        assert STRING_METHODS["upper"]("hello") == "HELLO"

    def test_lower(self) -> None:
        assert STRING_METHODS["lower"]("HELLO") == "hello"

    def test_strip(self) -> None:
        assert STRING_METHODS["strip"]("  hi  ") == "hi"

    def test_strip_with_chars(self) -> None:
        assert STRING_METHODS["strip"]("..hi..", ".") == "hi"

    def test_replace(self) -> None:
        assert STRING_METHODS["replace"]("a b a", "a", "c") == "c b c"

    def test_split(self) -> None:
        assert STRING_METHODS["split"]("a b c") == ["a", "b", "c"]

    def test_startswith(self) -> None:
        assert STRING_METHODS["startswith"]("hello", "he") is True

    def test_endswith(self) -> None:
        assert STRING_METHODS["endswith"]("hello", "lo") is True

    def test_contains(self) -> None:
        assert STRING_METHODS["contains"]("hello", "ell") is True


class TestListMethods:
    def test_append(self) -> None:
        lst = [1, 2]
        result = LIST_METHODS["append"](lst, 3)
        assert result == [1, 2, 3]

    def test_remove(self) -> None:
        lst = [1, 2, 3]
        result = LIST_METHODS["remove"](lst, 2)
        assert result == [1, 3]

    def test_pop(self) -> None:
        lst = [1, 2, 3]
        val = LIST_METHODS["pop"](lst)
        assert val == 3
        assert lst == [1, 2]

    def test_clear(self) -> None:
        lst = [1, 2]
        result = LIST_METHODS["clear"](lst)
        assert result == []

    def test_length(self) -> None:
        assert LIST_METHODS["length"]([1, 2, 3]) == 3

    def test_copy(self) -> None:
        lst = [1, 2]
        cpy = LIST_METHODS["copy"](lst)
        assert cpy == [1, 2]
        assert cpy is not lst


class TestDictMethods:
    def test_keys(self) -> None:
        assert DICT_METHODS["keys"]({"a": 1, "b": 2}) == ["a", "b"]

    def test_values(self) -> None:
        assert DICT_METHODS["values"]({"a": 1, "b": 2}) == [1, 2]

    def test_items(self) -> None:
        assert DICT_METHODS["items"]({"a": 1}) == [("a", 1)]

    def test_contains(self) -> None:
        assert DICT_METHODS["contains"]({"a": 1}, "a") is True

    def test_get(self) -> None:
        assert DICT_METHODS["get"]({"a": 1}, "a") == 1
        assert DICT_METHODS["get"]({"a": 1}, "b") is None

    def test_copy(self) -> None:
        d = {"a": 1}
        cpy = DICT_METHODS["copy"](d)
        assert cpy == d
        assert cpy is not d
