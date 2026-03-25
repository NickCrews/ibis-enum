# ibis-enum

`ibis-enum` provides a single utility: `IbisEnum`. It is like a plain
`enum.Enum`, except it has better interoperability with [ibis](https://github.com/ibis-project/ibis).
It is modeled after ordered enums in DuckDB, PostgreSQL, and MySQL.

- They are have an ordering, eg `Priority.LOW < Priority.MEDIUM < Priority.HIGH`
- They provide useful conversion methods to convert between the string-y and int-y representations.
- They can be compared against both plain python and ibis values,
  with sane coercion that is friendly but hopefully avoids footguns.
  eg `Priority.LOW < ibis.literal("HIGH")` works as expected,
  resulting in an ibis BooleanValue expression that would execute to True.
  Note that plain string comparison of `"LOW" < "HIGH"` would evaluate to False!
- They have great type annotations!
- They are well-tested, linted, and formatted.
- MIT licensed.

I would consider this as being in Beta status. It is pretty simple,
and I would trust it's implementation to be mostly bug free, and
I don't see TOO many reasons to change the public API,
but I probably still will alittle bit. So to keep me from breaking you, use a lockfile.

## Installation

Available on [PyPI as `ibis-enum`](https://pypi.org/project/ibis-enum/).

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

## Creation

Using plain python values:

```python
assert Priority.MEDIUM == Priority("MEDIUM")
assert Priority.MEDIUM == Priority(1)
Priority("bogus") # errors
Priority(999) # errors
Priority("medium") # errors, case mismatch
```

## Conversion

You can convert python values to the int-y or string-y form using classmethods:

```python
assert Priority.to_stringy(Priority.MEDIUM) == "MEDIUM"
assert Priority.to_stringy("MEDIUM") == "MEDIUM"
assert Priority.to_stringy(1) == "MEDIUM"

assert Priority.to_integery(Priority.MEDIUM) == 1
assert Priority.to_integery("MEDIUM") == 1
assert Priority.to_integery(1) == 1
```

And you can convert ibis values, which give you back ibis StringValue and IntegerValues:

```python
assert Priority.to_stringy(ibis.literal("MEDIUM")).execute() == "MEDIUM"
assert Priority.to_stringy(ibis.literal(1)).execute() == "MEDIUM"

assert Priority.to_integery(ibis.literal("MEDIUM")).execute() == 1
assert Priority.to_integery(ibis.literal(1)).execute() == 1
```

## Comparison and Ordering

`IbisEnum` members can be compared to other `IbisEnum`s, plain python `int`s and `str`s
which give back plain `bool`s as you would expect:

```python
assert Priority.LOW < Priority.HIGH
assert Priority.LOW < "HIGH"
assert Priority.LOW < 2
```

Comparing to an ibis Value results in an ibis BooleanValue.
Any StringValue's are converted to the integer level when ordering is important!
Otherwise we avoid casting whenever we don't need it, for optimal performance.

```python
assert (Priority.LOW == ibis.literal("HIGH")).execute() is True
assert (Priority.LOW < ibis.literal(2)).execute() is True
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
