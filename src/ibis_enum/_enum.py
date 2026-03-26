from __future__ import annotations

from enum import Enum, EnumMeta, unique
from typing import Any, cast, overload

import ibis
from ibis.common.deferred import Deferred, deferrable
from ibis.expr import types as ir
from typing_extensions import Never


class ErrorOnlyStringAndNumericIbisValues:
    """Dummy type to mark the fact that IbisEnum can only be compared to string and numeric Ibis values, not other types of Ibis values."""  # noqa: E501

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
                    f"Invalid value for {clsname}.{key}: {value!r}. IbisEnum values must be `int`s."  # noqa: E501
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
        if isinstance(obj, str):
            member_names = self.__members__.keys()
            return obj in member_names
        if _is_int(obj):
            member_values = (member.value for member in self)
            return obj in member_values
        return super().__contains__(obj)


class IbisEnum(Enum, metaclass=_IbisEnumMeta):
    """Integer-backed enum with Ibis-aware comparisons and ordering.

    `IbisEnum` is close to the built-in :class:`enum.Enum`, but plain
    ``Enum`` members are not natively comparable to Ibis string or integer
    expressions. ``IbisEnum`` preserves the usual enum ergonomics while also
    allowing comparisons like ``Priority.HIGH == ibis.literal(2)``.

    Ordering is based on the integer member values, similar to orderable enums
    in SQL systems such as DuckDB, PostgreSQL, and MySQL.

    For Ibis comparisons, put the enum member on the left-hand side, eg
    ``Priority.HIGH > ibis.literal(1)``. The reverse form,
    ``ibis.literal(1) < Priority.HIGH``,
    will probably fail because Ibis dispatches its own comparison operators first.

    Examples
    --------
    >>> class Priority(IbisEnum):
    ...     LOW = 0
    ...     MEDIUM = 1
    ...     HIGH = 2
    >>> Priority(1)
    Priority.MEDIUM
    >>> Priority("HIGH")
    Priority.HIGH
    >>> Priority.HIGH == 2
    True
    >>> Priority.LOW < "HIGH"
    True
    """

    @classmethod
    def _missing_(cls, value: object) -> IbisEnum | None:
        """Resolve string names and integer values to enum members.

        This mirrors the normal enum constructor flow, but accepts both the
        integer value and the member name.

        Examples
        --------
        >>> class Priority(IbisEnum):
        ...     LOW = 0
        ...     MEDIUM = 1
        ...     HIGH = 2
        >>> Priority("HIGH")
        Priority.HIGH
        >>> Priority(0)
        Priority.LOW
        """

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
    def to_numericy(cls, value: Deferred, /) -> Deferred: ...
    @overload
    @classmethod
    def to_numericy(cls, value: str | int, /) -> int: ...
    @overload
    @classmethod
    def to_numericy(
        cls, value: ir.StringScalar | ir.NumericScalar, /
    ) -> ir.NumericScalar: ...
    @overload
    @classmethod
    def to_numericy(
        cls, value: ir.StringColumn | ir.NumericColumn, /
    ) -> ir.NumericColumn: ...
    @overload
    @classmethod
    def to_numericy(
        cls, value: ir.StringValue | ir.NumericValue, /
    ) -> ir.NumericValue: ...

    @classmethod
    def to_numericy(
        cls, value: str | int | ir.StringValue | ir.NumericValue | Deferred, /
    ) -> int | ir.NumericValue | Deferred:
        """Coerce something to a python `int` or ibis NumericValue.

        Unlike plain :class:`enum.Enum`, this also accepts Ibis string and
        numeric expressions.

        Examples
        --------
        >>> class Priority(IbisEnum):
        ...     LOW = 0
        ...     MEDIUM = 1
        ...     HIGH = 2
        >>> Priority.to_numericy("MEDIUM")
        1
        >>> import ibis
        >>> string_expr = Priority.to_numericy(ibis.literal("HIGH"))
        >>> type(string_expr)
        <class 'ibis.expr.types.numeric.IntegerScalar'>
        >>> string_expr.execute()
        2
        >>> print(string_expr.to_sql("duckdb", pretty=False))
        SELECT CASE 'HIGH' WHEN 'LOW' THEN 0 WHEN 'MEDIUM' THEN 1 WHEN 'HIGH' THEN 2 ELSE NULL END AS "Priority"
        >>> int_expr = Priority.to_numericy(ibis.literal(1))
        >>> type(int_expr)
        <class 'ibis.expr.types.numeric.IntegerScalar'>
        >>> int_expr.execute()
        1
        >>> print(int_expr.to_sql("duckdb", pretty=False))
        SELECT 1 AS "1"
        """  # noqa: E501

        if isinstance(value, Deferred):
            return _deferred_to_numericy(cls, value)
        if isinstance(value, ir.StringValue):
            mapping = {name: member.value for name, member in cls.__members__.items()}
            return cast(
                ir.IntegerValue,
                value.substitute(mapping, else_=ibis.null()).name(cls.__name__),
            )
        if isinstance(value, ir.IntegerValue):
            return value
        member = cls(value)
        return member.value

    @overload
    @classmethod
    def to_stringy(cls, value: Deferred, /) -> Deferred: ...
    @overload
    @classmethod
    def to_stringy(cls, value: str | int, /) -> str: ...
    @overload
    @classmethod
    def to_stringy(
        cls, value: ir.StringScalar | ir.IntegerScalar, /
    ) -> ir.StringScalar: ...
    @overload
    @classmethod
    def to_stringy(
        cls, value: ir.StringColumn | ir.IntegerColumn, /
    ) -> ir.StringColumn: ...
    @overload
    @classmethod
    def to_stringy(cls, value: ir.StringValue | ir.IntegerValue) -> ir.StringValue: ...

    @classmethod
    def to_stringy(
        cls, value: str | int | ir.StringValue | ir.IntegerValue | Deferred, /
    ) -> str | ir.StringValue | Deferred:
        """Convert an enum member name or value to its canonical string form.

        Unlike plain :class:`enum.Enum`, this also accepts Ibis string and
        numeric expressions.

        Examples
        --------
        >>> class Priority(IbisEnum):
        ...     LOW = 0
        ...     MEDIUM = 1
        ...     HIGH = 2
        >>> Priority.to_stringy(1)
        'MEDIUM'
        >>> import ibis
        >>> int_expr = Priority.to_stringy(ibis.literal(2))
        >>> type(int_expr)
        <class 'ibis.expr.types.strings.StringScalar'>
        >>> int_expr.execute()
        'HIGH'
        >>> print(int_expr.to_sql("duckdb", pretty=False))
        SELECT CASE 2 WHEN 0 THEN 'LOW' WHEN 1 THEN 'MEDIUM' WHEN 2 THEN 'HIGH' ELSE NULL END AS "Priority"
        >>> string_expr = Priority.to_stringy(ibis.literal("MEDIUM"))
        >>> type(string_expr)
        <class 'ibis.expr.types.strings.StringScalar'>
        >>> string_expr.execute()
        'MEDIUM'
        >>> print(string_expr.to_sql("duckdb", pretty=False))
        SELECT 'MEDIUM' AS "'MEDIUM'"
        """  # noqa: E501

        if isinstance(value, Deferred):
            return _deferred_to_stringy(cls, value)
        if isinstance(value, ir.StringValue):
            return value
        if isinstance(value, ir.IntegerValue):
            mapping = cls._canonical_value_to_name()
            return cast(
                ir.StringValue,
                value.substitute(mapping, else_=ibis.null()).name(cls.__name__),
            )
        made = cls(value)
        return made.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __str__(self) -> str:
        return self.name

    def __int__(self) -> int:
        return int(self.value)

    def _get_eq_pair(self, other: object) -> tuple[Any, Any]:
        if isinstance(other, IbisEnum):
            return self.value, other.value
        if isinstance(other, str):
            return self.name, other
        if _is_int(other):
            return self.value, other
        if isinstance(other, ir.IntegerValue):
            return self.value, other
        if isinstance(other, ir.StringValue):
            return self.name, other
        raise TypeError(f"Cannot compare {self.__class__.__name__} to {type(other)}")

    def _get_orderable_pair(self, other: object) -> tuple[Any, Any]:
        if isinstance(other, str):
            return self.value, self.to_numericy(other)
        if isinstance(other, ir.StringValue):
            return self.value, self.to_numericy(other)
        return self._get_eq_pair(other)

    @overload
    def __eq__(self, other: Deferred, /) -> Deferred: ...
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

    def __eq__(self, other: object, /) -> bool | ir.BooleanValue | Deferred:
        if isinstance(other, Deferred):
            return _deferred_eq(self, other)
        self_val, other_val = self._get_eq_pair(other)
        return self_val == other_val

    @overload
    def __ne__(self, other: Deferred, /) -> Deferred: ...
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

    def __ne__(self, other: object, /) -> bool | ir.BooleanValue | Deferred:
        if isinstance(other, Deferred):
            return _deferred_ne(self, other)
        self_val, other_val = self._get_eq_pair(other)
        return self_val != other_val

    @overload
    def __lt__(self, other: Deferred, /) -> Deferred: ...
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

    def __lt__(self, other: object) -> bool | ir.BooleanValue | Deferred:
        if isinstance(other, Deferred):
            return _deferred_lt(self, other)
        self_val, other_val = self._get_orderable_pair(other)
        return self_val < other_val

    @overload
    def __le__(self, other: Deferred, /) -> Deferred: ...
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

    def __le__(self, other: object, /) -> bool | ir.BooleanValue | Deferred:
        if isinstance(other, Deferred):
            return _deferred_le(self, other)
        self_val, other_val = self._get_orderable_pair(other)
        return self_val <= other_val

    @overload
    def __gt__(self, other: Deferred, /) -> Deferred: ...
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

    def __gt__(self, other: object, /) -> bool | ir.BooleanValue | Deferred:
        if isinstance(other, Deferred):
            return _deferred_gt(self, other)
        self_val, other_val = self._get_orderable_pair(other)
        return self_val > other_val

    @overload
    def __ge__(self, other: Deferred, /) -> Deferred: ...
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

    def __ge__(self, other: object) -> bool | ir.BooleanValue | Deferred:
        if isinstance(other, Deferred):
            return _deferred_ge(self, other)
        self_val, other_val = self._get_orderable_pair(other)
        return self_val >= other_val


@deferrable
def _deferred_eq(member: IbisEnum, other: object) -> bool | ir.BooleanValue:
    self_val, other_val = member._get_eq_pair(other)
    return self_val == other_val


@deferrable
def _deferred_ne(member: IbisEnum, other: object) -> bool | ir.BooleanValue:
    self_val, other_val = member._get_eq_pair(other)
    return self_val != other_val


@deferrable
def _deferred_lt(member: IbisEnum, other: object) -> bool | ir.BooleanValue:
    self_val, other_val = member._get_orderable_pair(other)
    return self_val < other_val


@deferrable
def _deferred_le(member: IbisEnum, other: object) -> bool | ir.BooleanValue:
    self_val, other_val = member._get_orderable_pair(other)
    return self_val <= other_val


@deferrable
def _deferred_gt(member: IbisEnum, other: object) -> bool | ir.BooleanValue:
    self_val, other_val = member._get_orderable_pair(other)
    return self_val > other_val


@deferrable
def _deferred_ge(member: IbisEnum, other: object) -> bool | ir.BooleanValue:
    self_val, other_val = member._get_orderable_pair(other)
    return self_val >= other_val


@deferrable
def _deferred_to_numericy(cls: type[IbisEnum], value: object) -> int | ir.NumericValue:
    return cls.to_numericy(value)  # ty:ignore[no-matching-overload]


@deferrable
def _deferred_to_stringy(cls: type[IbisEnum], value: object) -> str | ir.StringValue:
    return cls.to_stringy(value)  # ty:ignore[no-matching-overload]
