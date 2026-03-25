# ibis-enum

`ibis-enum` provides a single utility: `IbisEnum`. It is like a plain
`enum.Enum`, except it has better interoperability with [ibis](https://github.com/ibis-project/ibis).

`IbisEnum` are modeled after ordered enums in DuckDB, PostgreSQL, and MySQL.
- They are have an ordering, eg `Priority.LOW < Priority.MEDIUM < Priority.HIGH`
- They provide useful conversion methods to convert between the string-y and int-y representations.
- They can be compared against both plain python and ibis values,
  with sane coercion that is friendly but hopefully avoids footguns.
  eg `Priority.LOW < ibis.literal("HIGH")` works as expected,
  resulting in an ibis BooleanValue expression that would execute to True.
  Note that plain string comparison of `"LOW" < "HIGH"` would evaluate to False!
- They have great type annotations!
- They are well-tested, linted, and formatted.

## Installation

```bash
uv add ibis-enum
```

## Quick Start

```python
from ibis_enum import IbisEnum

class Priority(IbisEnum):
	# Values must be ints. The order of the members is determined by the ints.
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    URGENT = 3
	# Names are case sensitive:
	# low = 5 would result in a distinct enum value
	
	# Member values MUST be unique.
	# ALSO_MEDIUM = 1 # This would error
```

## Creation and Conversion


```python
assert Priority.to_stringy(priority_code).execute() == "HIGH"
assert Priority.to_integery(priority_name).execute() == 2
```

## Comparison and Ordering

`IbisEnum` members can be compared to plain python ints, strings, and `IbisEnum`s:

```python
assert Priority.LOW < Priority.MEDIUM
assert Priority.HIGH > Priority.MEDIUM
assert Priority.URGENT >= 3

# Note that with string comparison, "HIGH" < "LOW"
assert "LOW" < Priority.HIGH
```

Comparing to an ibis Value results in an ibis BooleanValue.
Any StringValue's are converted to the integer level when ordering is important!
Otherwise we avoid casting whenever we don't need it, for optimal performance.

```python
assert (Priority.HIGH == ibis.literal("HIGH")).execute() is True
assert (Priority.HIGH == ibis.literal(2)).execute() is True
assert (Priority.LOW < ibis.literal("HIGH")).execute() is True
```

### Comparison Warning

For comparisons with Ibis values, the enum member MUST be on the left-hand side:

```python
Priority.HIGH == ibis.literal(1)
Priority.HIGH > ibis.literal(1)
# etc
```

The reverse form may fail:

```python
ibis.literal(1) == Priority.HIGH
ibis.literal(1) < Priority.HIGH
# etc
```

This is due a limitation of Ibis that we don't have control over.
When python sees `X == Y`, it first calls `X.__eq__(Y)`, then if that
returns `NotImplemented` then it falls back to `Y.__eq__(X)`.
`ibis.Value.__eq__(self, <enum value>)` throws an error
instead of returning a NotImplemented as it probably should.
So, we need instead for `Enum.__eq__(self, <ibis value>)` to be the comparison
operator caled first.
To guarantee this, the enum needs to be on the left hand side of the comparison.

## Why Not Plain Enum?

Built-in `enum.Enum` is fine for Python-only comparisons, but it does not know
how to compare itself to Ibis expressions.

```python
import enum
import ibis

class PlainPriority(enum.Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    URGENT = 3

# This would error!
Priority.HIGH == ibis.literal(2)
```
