"""
Define the types used in the type hints.

1. `KeyPath`
    - Alias for `pydash.types.PathT`.

2. `FlatDict`
    - Alias for the buil-in `dict` type.
    - Represents a flat dictionary (not nested).

2. `NestedDict`
    - Alias for the built-in `dict` type.
    - Represents a nested dictionary.

3. `TypeTree`
    - Alias for the built-in `dict` type.
    - Represents a nested dictionary where the values are types.

4. `LetItem`
    - The type of the items of the `Iterable` used to initialize `Let`.
    - Union of the types:
        - `str`: the key to be "let through",
        - `(str,)`: alias of `str`,
        - `(old: str, new: str)`: rename the key,
        - `(old: str, new: str, type: Type)`: rename the key and ensure the
            correct type.

5. `LetAlias`
    - Used to initialize `Let`.
    - Union of the types:
        - `LetItem`,
        - `Iterable[LetItem]`,
"""

from typing import (
    Any,
    Union,
    Iterable,
    Tuple,
    Type,
)

import pydash.types as py_t

Key = Any

KeyPath = py_t.PathT

FlatDict = dict

NestedDict = dict

TypeTree = dict  # nested dict with types as values

LetItem = Union[
    str,
    Tuple[str],
    Tuple[str, str],
    Tuple[str, str, Type],
]

LetAlias = Union[
    LetItem,
    Iterable[LetItem],
]
