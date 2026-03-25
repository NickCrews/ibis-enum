from __future__ import annotations

from typing import cast

import ibis
from ibis.expr import types as ir
import pytest

from ibis_enum import IbisEnum, __version__


def test_version():
    assert isinstance(__version__, str)


class EmailEnum(IbisEnum):
    FULL_EXACT = 0
    FULL_NEAR = 1
    LOCAL_EXACT = 2
    LOCAL_NEAR = 3
    ELSE = 4


INTEGER_SCALAR_0 = cast(ir.IntegerScalar, ibis.literal(0))
INTEGER_SCALAR_999 = cast(ir.IntegerScalar, ibis.literal(999))
FLOATING_SCALAR_0 = cast(ir.FloatingScalar, ibis.literal(0.0))
FLOATING_SCALAR_999 = cast(ir.FloatingScalar, ibis.literal(999.0))
STRING_SCALAR_FULL_EXACT = cast(ir.StringScalar, ibis.literal("FULL_EXACT"))
STRING_SCALAR_full_exact = cast(ir.StringScalar, ibis.literal("full_exact"))
STRING_SCALAR_BOGUS = cast(ir.StringScalar, ibis.literal("BOGUS"))


def test_creation():
    assert EmailEnum(1) is EmailEnum.FULL_NEAR
    assert EmailEnum(True) is EmailEnum.FULL_NEAR
    assert EmailEnum("FULL_NEAR") is EmailEnum.FULL_NEAR
    assert EmailEnum(EmailEnum.FULL_NEAR) is EmailEnum.FULL_NEAR
    with pytest.raises(TypeError):
        EmailEnum(None)
    with pytest.raises(ValueError):
        EmailEnum(100)
    with pytest.raises(ValueError):
        EmailEnum("full_near")


def test_getitem_syntax():
    assert EmailEnum["FULL_NEAR"] == EmailEnum.FULL_NEAR
    with pytest.raises(KeyError):
        assert EmailEnum["full_near"] == EmailEnum.FULL_NEAR
    with pytest.raises(KeyError):
        EmailEnum[1]  # ty:ignore[invalid-argument-type]
    with pytest.raises(KeyError):
        EmailEnum[STRING_SCALAR_FULL_EXACT]  # ty:ignore[invalid-argument-type]
    with pytest.raises(KeyError):
        EmailEnum[INTEGER_SCALAR_0]  # ty:ignore[invalid-argument-type]


def test_container_semantics():
    assert len(EmailEnum) == 5
    assert list(EmailEnum) == [
        EmailEnum.FULL_EXACT,
        EmailEnum.FULL_NEAR,
        EmailEnum.LOCAL_EXACT,
        EmailEnum.LOCAL_NEAR,
        EmailEnum.ELSE,
    ]
    assert EmailEnum.FULL_EXACT in EmailEnum
    assert "FULL_EXACT" not in EmailEnum
    assert "full_exact" not in EmailEnum
    assert 0 in EmailEnum
    assert -1 not in EmailEnum
    with pytest.raises(TypeError) as exc_info:
        ibis.literal(0) in EmailEnum
    assert "Can't check for membership of an Ibis expression in an IbisEnum." in str(
        exc_info.value
    )
    with pytest.raises(TypeError) as exc_info:
        ibis.literal("FULL_EXACT") in EmailEnum
    assert "Can't check for membership of an Ibis expression in an IbisEnum." in str(
        exc_info.value
    )


def test_eq():
    assert EmailEnum.FULL_EXACT == 0
    assert EmailEnum.FULL_EXACT == "FULL_EXACT"
    assert EmailEnum.FULL_EXACT == EmailEnum.FULL_EXACT

    assert (EmailEnum.FULL_EXACT == INTEGER_SCALAR_0).execute()
    assert not (EmailEnum.FULL_EXACT == INTEGER_SCALAR_999).execute()

    assert (EmailEnum.FULL_EXACT == STRING_SCALAR_FULL_EXACT).execute()
    assert not (EmailEnum.FULL_EXACT == STRING_SCALAR_full_exact).execute()


def test_neq():
    assert EmailEnum.FULL_EXACT != 1
    assert EmailEnum.FULL_EXACT != "full_exact"
    assert EmailEnum.FULL_EXACT != EmailEnum.FULL_NEAR

    assert (EmailEnum.FULL_EXACT != INTEGER_SCALAR_999).execute()
    assert not (EmailEnum.FULL_EXACT != INTEGER_SCALAR_0).execute()

    assert (EmailEnum.FULL_EXACT != STRING_SCALAR_full_exact).execute()
    assert not (EmailEnum.FULL_EXACT != STRING_SCALAR_FULL_EXACT).execute()


def test_ordering_basic():
    assert EmailEnum.FULL_EXACT < 1
    assert EmailEnum.FULL_EXACT <= 1
    assert EmailEnum.FULL_EXACT > -1
    assert EmailEnum.FULL_EXACT >= 0

    assert 1 > EmailEnum.FULL_EXACT
    assert 1 >= EmailEnum.FULL_EXACT
    assert -1 < EmailEnum.FULL_EXACT
    assert 0 <= EmailEnum.FULL_EXACT

    assert EmailEnum.FULL_EXACT < EmailEnum.FULL_NEAR
    assert EmailEnum.FULL_EXACT <= EmailEnum.FULL_NEAR
    assert EmailEnum.FULL_NEAR > EmailEnum.FULL_EXACT
    assert EmailEnum.FULL_NEAR >= EmailEnum.FULL_EXACT


def test_ordering_vs_ibis_second():
    assert (EmailEnum.FULL_NEAR > INTEGER_SCALAR_0).execute()
    assert (EmailEnum.FULL_EXACT <= INTEGER_SCALAR_0).execute()
    assert (EmailEnum.FULL_NEAR > STRING_SCALAR_FULL_EXACT).execute()
    assert (EmailEnum.FULL_EXACT <= STRING_SCALAR_FULL_EXACT).execute()


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
# E           ibis.common.exceptions.IbisTypeError: Arguments Literal(0):int8 and Literal(FULL_NEAR):string are not comparable  # noqa: E501

# .venv/lib/python3.13/site-packages/ibis/expr/operations/logical.py:68: IbisTypeError
def test_ordering_vs_ibis_first():
    assert (INTEGER_SCALAR_0 < EmailEnum.FULL_NEAR).execute()
    assert (INTEGER_SCALAR_0 <= EmailEnum.FULL_EXACT).execute()
    assert (STRING_SCALAR_FULL_EXACT < EmailEnum.FULL_NEAR).execute()
    assert (STRING_SCALAR_FULL_EXACT <= EmailEnum.FULL_EXACT).execute()


def test_repr():
    assert (
        repr(EmailEnum)
        == "EmailEnum(FULL_EXACT=0, FULL_NEAR=1, LOCAL_EXACT=2, LOCAL_NEAR=3, ELSE=4)"  # noqa: E501
    )
    assert repr(EmailEnum.FULL_EXACT) == "EmailEnum.FULL_EXACT"


def test_str():
    assert (
        str(EmailEnum)
        == "EmailEnum(FULL_EXACT=0, FULL_NEAR=1, LOCAL_EXACT=2, LOCAL_NEAR=3, ELSE=4)"  # noqa: E501
    )
    assert str(EmailEnum.FULL_EXACT) == "FULL_EXACT"


def test_int():
    # class
    with pytest.raises(TypeError):
        int(EmailEnum)  # ty:ignore[invalid-argument-type]
    # instance
    assert int(EmailEnum.FULL_EXACT) == 0


def test_conversion():
    assert EmailEnum.FULL_NEAR.as_integer() == 1
    assert EmailEnum.FULL_NEAR.as_string() == "FULL_NEAR"

    assert EmailEnum.to_integer(1) == 1
    assert EmailEnum.to_string(1) == "FULL_NEAR"
    assert EmailEnum.to_integer(True) == 1
    assert EmailEnum.to_string(True) == "FULL_NEAR"
    assert EmailEnum.to_integer("FULL_NEAR") == 1
    assert EmailEnum.to_string("FULL_NEAR") == "FULL_NEAR"

    assert EmailEnum.to_integer(INTEGER_SCALAR_0).execute() == 0
    assert EmailEnum.to_string(STRING_SCALAR_FULL_EXACT).execute() == "FULL_EXACT"
    assert EmailEnum.to_integer(STRING_SCALAR_FULL_EXACT).execute() == 0
    assert EmailEnum.to_string(STRING_SCALAR_FULL_EXACT).execute() == "FULL_EXACT"

    with pytest.raises(ValueError):
        EmailEnum.to_integer(100)
    with pytest.raises(ValueError):
        EmailEnum.to_integer("full_near")
    with pytest.raises(ValueError):
        EmailEnum.to_string(100)
    with pytest.raises(ValueError):
        EmailEnum.to_string("full_near")


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
