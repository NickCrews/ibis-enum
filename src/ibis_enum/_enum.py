from __future__ import annotations

from enum import Enum, EnumMeta, unique
from typing import (
    Any,
    cast,
    overload,
)

import ibis
from ibis.expr import types as ir
from typing_extensions import Never


class ErrorOnlyStringAndNumericIbisValues:
    """Dummy type to mark the fact that LevelsEnum can only be compared to string and numeric Ibis values, not other types of Ibis values."""  # noqa: E501

    def __bool__(self: Never) -> Never:
        raise TypeError("Only string and numeric Ibis values are accepted.")


def _is_int(v: object) -> bool:
    """Is int but not bool?"""
    return isinstance(v, int) and not isinstance(v, bool)


class _IbisEnumMeta(EnumMeta):
    def __new__(mcls, clsname, bases, classdict, **kwds):
        for key, value in classdict.items():
            if key.startswith("_"):
                continue
            if callable(value) or isinstance(
                value, (classmethod, staticmethod, property)
            ):
                continue
            if not _is_int(value):
                raise TypeError(
                    f"Invalid value for {clsname}.{key}: {value!r}. MatchLevel values must be `int`s."  # noqa: E501
                )
        cls = super().__new__(mcls, clsname, bases, classdict, **kwds)
        unique_cls = unique(cls)  # ty:ignore[invalid-argument-type]
        return unique_cls

    def __repr__(cls) -> str:
        members = cast(dict[str, IbisEnum], cls.__members__)
        pairs = (f"{k}={v.value}" for k, v in members.items())
        return f"{cls.__name__}({', '.join(pairs)})"

    def __contains__(self: type[Any], obj: object) -> bool:
        if isinstance(obj, ibis.Value):
            raise TypeError(
                "Can't check for membership of an Ibis expression in an IbisEnum."
            )
        return super().__contains__(obj)


class IbisEnum(Enum, metaclass=_IbisEnumMeta):
    @classmethod
    def _missing_(cls, value: object) -> IbisEnum | None:
        if isinstance(value, str):
            # case-sensitive
            for member in cls:
                if member.name == value:
                    return member
            raise ValueError(
                f"{value!r} is not a valid {cls.__name__}. Valid names are: {[m.name for m in cls]}"  # noqa: E501
            )
        elif _is_int(value):
            for member in cls:
                if member.value == value:
                    return member
            raise ValueError(
                f"{value!r} is not a valid {cls.__name__}. Valid values are: {[m.value for m in cls]}"  # noqa: E501
            )
        raise TypeError(
            f"object of type {type(value).__name__} cannot be converted to {cls.__name__}"  # noqa: E501
        )

    @classmethod
    def _canonical_value_to_name(cls) -> dict[int, str]:
        out: dict[int, str] = {}
        for name, member in cls.__members__.items():
            if member.value not in out:
                out[member.value] = name
        return out

    @overload
    @classmethod
    def to_integer(cls, value: str | int) -> int: ...
    @overload
    @classmethod
    def to_integer(cls, value: ir.StringValue | ir.NumericValue) -> ir.NumericValue: ...

    @classmethod
    def to_integer(
        cls, value: str | int | ir.StringValue | ir.NumericValue
    ) -> int | ir.NumericValue:
        if isinstance(value, ir.StringValue):
            mapping = {name: member.value for name, member in cls.__members__.items()}
            return cast(
                ir.NumericValue,
                value.substitute(mapping, else_=ibis.null()).name(cls.__name__),
            )
        if isinstance(value, ir.NumericValue):
            return value
        member = cls(value)
        return member.value

    @overload
    @classmethod
    def to_string(cls, value: str | int) -> str: ...
    @overload
    @classmethod
    def to_string(cls, value: ir.StringValue | ir.NumericValue) -> ir.StringValue: ...

    @classmethod
    def to_string(
        cls, value: str | int | ir.StringValue | ir.NumericValue
    ) -> str | ir.StringValue:
        if isinstance(value, ir.StringValue):
            return value
        if isinstance(value, ir.NumericValue):
            mapping = cls._canonical_value_to_name()
            return cast(
                ir.StringValue,
                value.substitute(mapping, else_=ibis.null()).name(cls.__name__),
            )
        made = cls(value)
        return made.name

    def as_integer(self) -> int:
        return self.value

    def as_string(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __str__(self) -> str:
        return self.name

    def __int__(self) -> int:
        return int(self.value)

    def _get_comparable_pair(self, other: object) -> tuple[Any, Any]:
        if isinstance(other, IbisEnum):
            return self.value, other.value
        if isinstance(other, str):
            return self.name, other
        if _is_int(other):
            return self.value, other
        if isinstance(other, ir.NumericValue):
            return ibis.literal(self.value), other
        if isinstance(other, ir.StringValue):
            return ibis.literal(self.name), other
        raise TypeError(f"Cannot compare MatchLevel to {type(other)}")

    @overload
    def __eq__(
        self, other: ir.NumericScalar | ir.StringScalar, /
    ) -> ir.BooleanScalar: ...
    @overload
    def __eq__(
        self, other: ir.NumericColumn | ir.StringColumn, /
    ) -> ir.BooleanColumn: ...
    @overload
    def __eq__(self, other: ir.Value, /) -> ErrorOnlyStringAndNumericIbisValues: ...
    @overload
    def __eq__(self, other: object, /) -> bool: ...

    def __eq__(self, other: object, /) -> bool | ir.BooleanValue:
        self_val, other_val = self._get_comparable_pair(other)
        return self_val == other_val

    @overload
    def __ne__(
        self, other: ir.NumericScalar | ir.StringScalar, /
    ) -> ir.BooleanScalar: ...
    @overload
    def __ne__(
        self, other: ir.NumericColumn | ir.StringColumn, /
    ) -> ir.BooleanColumn: ...
    @overload
    def __ne__(self, other: ir.Value, /) -> ErrorOnlyStringAndNumericIbisValues: ...
    @overload
    def __ne__(self, other: object, /) -> bool: ...

    def __ne__(self, other: object, /) -> bool | ir.BooleanValue:
        self_val, other_val = self._get_comparable_pair(other)
        return self_val != other_val

    @overload
    def __lt__(
        self, other: ir.NumericScalar | ir.StringScalar, /
    ) -> ir.BooleanScalar: ...
    @overload
    def __lt__(
        self, other: ir.NumericColumn | ir.StringColumn, /
    ) -> ir.BooleanColumn: ...
    @overload
    def __lt__(self, other: ir.Value, /) -> ErrorOnlyStringAndNumericIbisValues: ...
    @overload
    def __lt__(self, other: object, /) -> bool: ...

    def __lt__(self, other: object) -> bool | ir.BooleanValue:
        self_val, other_val = self._get_comparable_pair(other)
        return self_val < other_val

    @overload
    def __le__(
        self, other: ir.NumericScalar | ir.StringScalar, /
    ) -> ir.BooleanScalar: ...
    @overload
    def __le__(
        self, other: ir.NumericColumn | ir.StringColumn, /
    ) -> ir.BooleanColumn: ...
    @overload
    def __le__(self, other: ir.Value, /) -> ErrorOnlyStringAndNumericIbisValues: ...
    @overload
    def __le__(self, other: object, /) -> bool: ...

    def __le__(self, other: object, /) -> bool | ir.BooleanValue:
        self_val, other_val = self._get_comparable_pair(other)
        return self_val <= other_val

    @overload
    def __gt__(
        self, other: ir.NumericScalar | ir.StringScalar, /
    ) -> ir.BooleanScalar: ...
    @overload
    def __gt__(
        self, other: ir.NumericColumn | ir.StringColumn, /
    ) -> ir.BooleanColumn: ...
    @overload
    def __gt__(self, other: ir.Value, /) -> ErrorOnlyStringAndNumericIbisValues: ...
    @overload
    def __gt__(self, other: object, /) -> bool: ...

    def __gt__(self, other: object, /) -> bool | ir.BooleanValue:
        self_val, other_val = self._get_comparable_pair(other)
        return self_val > other_val

    @overload
    def __ge__(
        self, other: ir.NumericScalar | ir.StringScalar, /
    ) -> ir.BooleanScalar: ...
    @overload
    def __ge__(
        self, other: ir.NumericColumn | ir.StringColumn, /
    ) -> ir.BooleanColumn: ...
    @overload
    def __ge__(self, other: ir.Value, /) -> ErrorOnlyStringAndNumericIbisValues: ...
    @overload
    def __ge__(self, other: object, /) -> bool: ...

    def __ge__(self, other: object) -> bool | ir.BooleanValue:
        self_val, other_val = self._get_comparable_pair(other)
        return self_val >= other_val
