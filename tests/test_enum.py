from __future__ import annotations

from typing import cast

import ibis
from ibis.expr import types as ir
import pytest

from ibis_enum import IbisEnum, __version__


def test_version():
    assert isinstance(__version__, str)


class Priority(IbisEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2


INTEGER_SCALAR_0 = cast(ir.IntegerScalar, ibis.literal(0))
INTEGER_SCALAR_1 = cast(ir.IntegerScalar, ibis.literal(1))
INTEGER_SCALAR_999 = cast(ir.IntegerScalar, ibis.literal(999))
FLOATING_SCALAR_0 = cast(ir.FloatingScalar, ibis.literal(0.0))
FLOATING_SCALAR_999 = cast(ir.FloatingScalar, ibis.literal(999.0))
STRING_SCALAR_MEDIUM = cast(ir.StringScalar, ibis.literal("MEDIUM"))
STRING_SCALAR_medium = cast(ir.StringScalar, ibis.literal("medium"))
STRING_SCALAR_BOGUS = cast(ir.StringScalar, ibis.literal("BOGUS"))


def test_creation():
    assert Priority(1) is Priority.MEDIUM
    assert Priority(True) is Priority.MEDIUM
    assert Priority("MEDIUM") is Priority.MEDIUM
    assert Priority(Priority.MEDIUM) is Priority.MEDIUM
    with pytest.raises(TypeError):
        Priority(None)
    with pytest.raises(ValueError):
        Priority(100)
    with pytest.raises(ValueError):
        Priority("medium")


def test_getitem_syntax():
    assert Priority["MEDIUM"] == Priority.MEDIUM
    with pytest.raises(KeyError):
        assert Priority["medium"]
    with pytest.raises(KeyError):
        Priority[1]  # ty:ignore[invalid-argument-type]
    with pytest.raises(KeyError):
        Priority[STRING_SCALAR_MEDIUM]  # ty:ignore[invalid-argument-type]
    with pytest.raises(KeyError):
        Priority[INTEGER_SCALAR_0]  # ty:ignore[invalid-argument-type]


def test_container_semantics():
    assert len(Priority) == 3
    assert list(Priority) == [
        Priority.LOW,
        Priority.MEDIUM,
        Priority.HIGH,
    ]
    assert Priority.LOW in Priority
    assert "LOW" in Priority
    assert "MEDIUM" in Priority
    assert "medium" not in Priority
    assert "bogus" not in Priority
    assert 0 in Priority
    assert 1 in Priority
    assert -1 not in Priority
    with pytest.raises(TypeError) as exc_info:
        ibis.literal(0) in Priority
    assert "Can't check for membership of an Ibis expression in an IbisEnum." in str(
        exc_info.value
    )
    with pytest.raises(TypeError) as exc_info:
        ibis.literal("MEDIUM") in Priority
    assert "Can't check for membership of an Ibis expression in an IbisEnum." in str(
        exc_info.value
    )


def test_eq():
    assert Priority.LOW == 0
    assert Priority.LOW == "LOW"
    assert Priority.LOW == Priority.LOW
    assert (Priority.MEDIUM == STRING_SCALAR_MEDIUM).execute()
    assert (Priority.MEDIUM == INTEGER_SCALAR_1).execute()

    assert not Priority.LOW == 1
    assert not Priority.LOW == "MEDIUM"
    assert not Priority.LOW == "low"
    assert not Priority.LOW == Priority.MEDIUM
    assert not (Priority.MEDIUM == STRING_SCALAR_BOGUS).execute()
    assert not (Priority.MEDIUM == STRING_SCALAR_medium).execute()


def test_neq():
    assert Priority.LOW != 1
    assert Priority.LOW != "MEDIUM"
    assert Priority.LOW != "low"
    assert Priority.LOW != Priority.MEDIUM
    assert (Priority.LOW != INTEGER_SCALAR_999).execute()
    assert (Priority.LOW != STRING_SCALAR_medium).execute()

    assert not Priority.LOW != 0
    assert not Priority.LOW != "LOW"
    assert not Priority.LOW != Priority.LOW
    assert not (Priority.MEDIUM != STRING_SCALAR_MEDIUM).execute()
    assert not (Priority.MEDIUM != INTEGER_SCALAR_1).execute()


def test_ordering_basic():
    assert Priority.LOW < 1
    assert Priority.LOW <= 1
    assert Priority.LOW > -1
    assert Priority.LOW >= 0

    assert 1 > Priority.LOW
    assert 1 >= Priority.LOW
    assert -1 < Priority.LOW
    assert 0 <= Priority.LOW

    assert Priority.LOW < "MEDIUM"
    assert Priority.LOW <= "MEDIUM"
    assert Priority.MEDIUM > "LOW"
    assert Priority.MEDIUM >= "LOW"

    assert "MEDIUM" > Priority.LOW
    assert "MEDIUM" >= Priority.LOW
    assert "LOW" < Priority.MEDIUM
    assert "LOW" <= Priority.MEDIUM

    assert Priority.LOW < Priority.MEDIUM
    assert Priority.LOW <= Priority.MEDIUM
    assert Priority.MEDIUM > Priority.LOW
    assert Priority.MEDIUM >= Priority.LOW


def test_ordering_errors():
    with pytest.raises(ValueError) as exc_info:
        Priority.LOW < "BOGUS"
    assert (
        str(exc_info.value)
        == "'BOGUS' is not a valid Priority. Valid names are: ['LOW', 'MEDIUM', 'HIGH']"
    )
    with pytest.raises(ValueError) as exc_info:
        Priority.LOW < "medium"
    assert (
        str(exc_info.value)
        == "'medium' is not a valid Priority. Valid names are: ['LOW', 'MEDIUM', 'HIGH']"  # noqa: E501
    )


def test_ordering_vs_ibis_second():
    assert (Priority.HIGH > INTEGER_SCALAR_0).execute()
    assert (Priority.HIGH > STRING_SCALAR_MEDIUM).execute()
    assert (Priority.HIGH >= INTEGER_SCALAR_0).execute()
    assert (Priority.HIGH >= STRING_SCALAR_MEDIUM).execute()
    assert (Priority.LOW < INTEGER_SCALAR_1).execute()
    assert (Priority.LOW < STRING_SCALAR_MEDIUM).execute()
    assert (Priority.LOW <= INTEGER_SCALAR_1).execute()
    assert (Priority.LOW <= STRING_SCALAR_MEDIUM).execute()


@pytest.mark.xfail(
    reason="ibis.Value.__lt__ is called first before IbisEnum.__gt__, and ibis doesn't incorrectly errors instead of returning NotImplemented"  # noqa: E501
)  # noqa: E501
#     def __init__(self, left, right):
#         """Construct a comparison operation between `left` and `right`.

#         Casting rules for type promotions (for resolving the output type) may
#         depend on the target backend.

#         TODO: how are overflows handled? Can we provide anything useful in
#         Ibis to help the user avoid them?
#         """
#         if not rlz.comparable(left, right):
# >           raise IbisTypeError(
#                 f"Arguments {rlz.arg_type_error_format(left)} and "
#                 f"{rlz.arg_type_error_format(right)} are not comparable"
#             )
# E           ibis.common.exceptions.IbisTypeError: Arguments Literal(0):int8 and Literal(MEDIUM):string are not comparable  # noqa: E501

# .venv/lib/python3.13/site-packages/ibis/expr/operations/logical.py:68: IbisTypeError
def test_ordering_vs_ibis_first():
    assert (INTEGER_SCALAR_0 < Priority.MEDIUM).execute()
    assert (INTEGER_SCALAR_0 <= Priority.LOW).execute()
    assert (STRING_SCALAR_MEDIUM < Priority.MEDIUM).execute()
    assert (STRING_SCALAR_MEDIUM <= Priority.LOW).execute()


def test_repr():
    assert repr(Priority) == "Priority(LOW=0, MEDIUM=1, HIGH=2)"
    assert repr(Priority.LOW) == "Priority.LOW"


def test_str():
    assert str(Priority) == "Priority(LOW=0, MEDIUM=1, HIGH=2)"
    assert str(Priority.LOW) == "LOW"


def test_int():
    # class
    with pytest.raises(TypeError):
        int(Priority)  # ty:ignore[invalid-argument-type]
    # instance
    assert int(Priority.LOW) == 0


def test_conversion():
    assert Priority.to_numericy(1) == 1
    assert Priority.to_stringy(1) == "MEDIUM"
    assert Priority.to_numericy(True) == 1
    assert Priority.to_stringy(True) == "MEDIUM"
    assert Priority.to_numericy("MEDIUM") == 1
    assert Priority.to_stringy("MEDIUM") == "MEDIUM"

    assert Priority.to_numericy(INTEGER_SCALAR_0).execute() == 0
    assert Priority.to_stringy(INTEGER_SCALAR_0).execute() == "LOW"
    assert Priority.to_numericy(STRING_SCALAR_MEDIUM).execute() == 1
    assert Priority.to_stringy(STRING_SCALAR_MEDIUM).execute() == "MEDIUM"

    with pytest.raises(ValueError):
        Priority.to_numericy(100)
    with pytest.raises(ValueError):
        Priority.to_numericy("medium")
    with pytest.raises(ValueError):
        Priority.to_stringy(100)
    with pytest.raises(ValueError):
        Priority.to_stringy("medium")


def test_non_numeric_enum():
    with pytest.raises(TypeError):

        class NonNumeric(IbisEnum):
            X = "foo"


def test_duplicate_enum():
    with pytest.raises(ValueError) as exc_info:

        class DuplicateEnum(IbisEnum):
            X = 1
            Y = 1

    assert "duplicate values found in DuplicateEnum(X=1, Y=1): Y -> X" in str(
        exc_info.value
    )
