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

4. `PassItem`
    - The type of the items of the `Iterable` used to initialize `Pass`.
    - Union of the types:
        - `str`: the key to be "passed through",
        - `(str,)`: alias of `str`,
        - `(old: str, new: str)`: rename the key,
        - `(old: str, new: str, type: Type)`: rename the key and ensure the
            correct type.

5. `PassAlias`
    - Used to initialize `Pass`.
    - Union of the types:
        - `PassItem`,
        - `Iterable[PassItem]`,
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

PassItem = Union[
    str,
    Tuple[str],
    Tuple[str, str],
    Tuple[str, str, Type],
]

PassAlias = Union[
    PassItem,
    Iterable[PassItem],
]
