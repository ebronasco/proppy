"""
Functions for dealing with nested dictionaries and type trees (nested
dictionaries of types).
"""
from inspect import getfullargspec
from collections.abc import Iterable

from copy import deepcopy

import typing as t
from typing_extensions import TypedDict

from pydash import py_

import runtype as rt

from .types import (
    Key,
    KeyPath,
    NestedDict,
    TypeTree,
)


def nested_get(
        data: NestedDict,
        key: KeyPath,
) -> t.Any:
    """
    Retrive an element at `key` from `data` nested dict.

    **Raises:** `KeyError` if `key` is not found in `data`.

    **Examples:**
    ```python
    >>> nested_get({'a': 1}, 'a')
    1
    >>> nested_get({'a': {'b': 1}}, 'a.b')
    1
    >>> nested_get({}, 'a')
    Traceback (most recent call last):
    ...
    KeyError: 'The key "a" is not found in "{}"'

    ```
    """
    value = py_.get(data, key, default=KeyError)

    if value is KeyError:
        _error_msg = f"The key \"{key}\" is not found in \"{repr(data)}\""
        raise KeyError(_error_msg)

    return value


def nested_set(
        data: NestedDict,
        key: KeyPath,
        value: t.Any,
) -> NestedDict:
    """
    Set an element at `key` in `data` to `value`.

    **Examples:**
    ```python
    >>> data = {}
    >>> nested_set(data, 'a', 1) == {'a': 1}
    True
    >>> data == {'a': 1}
    True
    >>> nested_set(data, 'b.c', 2) == {'a': 1, 'b': {'c': 2}}
    True
    >>> data == {'a': 1, 'b': {'c': 2}}
    True
    >>> nested_set(data, 'a.d', 3)
    Traceback (most recent call last):
    ...
    AttributeError: 'int' object has no attribute 'd'

    ```
    """
    return py_.set_(data, key, value)


def keys_from_callable(
        func: t.Callable,
        start_at: t.Optional[int] = 0,
) -> t.Set[Key]:
    """
    Build an input type tree of a callable.

    Args:
        func: The callable whose input type tree is built.
        start_at: Ignore the arguments at positions before `start_at`.

    **Examples:**
    ```python
    >>> keys_from_callable(lambda x, y: x) \
    == {('x', t.Any), ('y', t.Any)}
    True
    >>> def a(s: str, b: bool):
    ...     pass
    ...
    >>> keys_from_callable(a) \
    == {('s', str), ('b', bool)}
    True

    ```
    """
    argspec = getfullargspec(func)
    args = argspec.args[start_at:]
    return set((k, argspec.annotations.get(k, t.Any)) for k in args)


def build_tree(
        elems: t.Iterable[t.Union[t.Tuple, t.Any]],
        default: t.Any = None,
) -> NestedDict:
    """
    Builds a nested dict based on `elems`.

    Elements of `elems` are `(v1,v2,...)`. then it builds a nested dict
    with keys `v1` and values `(v2,...)`. If `(v2,...)` is a singleton, then
    its replaced by `v2`.


    Args:
        elems: Iterable `elems` of `(v1,v2,...)`. Elements which are not tuples
            are replaced by the tuple `(element, default)`.
        default: Default value of the tree if only `v1` is given.

    **Raises:** `TypeError` if `elem` is not `PassAliasT`.

    **Examples:**
    ```python
    >>> build_tree({('a', int), 'b', 'c.d'}) == \
    {'a': int, 'b': None, 'c': {'d': None}}
    True
    >>> build_tree(True)
    Traceback (most recent call last):
    ...
    TypeError: The argument `elems` is of unsupported type:
    True

    ```
    """
    if isinstance(elems, Iterable) and not isinstance(elems, dict):
        key_value_pairs = []
        for elem in elems:
            if not isinstance(elem, tuple) or len(elem) == 1:
                key_value_pairs.append((elem, default))
                continue

            if len(elem) == 2:
                key_value_pairs.append((elem[0], elem[1]))
                continue

            key_value_pairs.append((elem[0], elem[1:]))

        if len(key_value_pairs) > 0:
            return py_.zip_object_deep(key_value_pairs)

        return {}

    _error_msg = "\n".join([
        "The argument `elems` is of unsupported type:",
        repr(elems)
    ])
    raise TypeError(_error_msg)


def build_tree_of(obj: NestedDict):
    """
    Build a type tree of an object.

    ***!!! `obj` is changed.***

    Args:
        obj: The object whose type tree is built.

    **Examples:**
    ```python
    >>> build_tree_of({'a': 1, 'b': {'c': "Hello"}})
    {'a': <class 'int'>, 'b': {'c': <class 'str'>}}

    ```
    """

    py_.map_values_deep(obj, type)
    return obj


def type_tree_union(
        obj: TypeTree,
        source: TypeTree,
        minimize: bool = False,
) -> TypeTree:
    """
    Take the union of two type trees. The result is written to `obj`
    and returned.

    **!!! `obj` is changed.**

    Args:
        obj: Type tree that is changed.
        source: Type tree that is "added" to `obj`.
        minimize: Decide what to do when both type trees have the same key. If
            `True`, take the smaller type as the value. Otherwise, take the
            bigger type.

    **Raises:** `TypeError` for the cases when both type trees have the
        same key, but the values are not comparable.

    **Examples:**
    ```python
    >>> t1 = {'a': int, 'b': str, 'c': dict}
    >>> type_tree_union(t1,
    ...     {'c': {'d': t.Any}, 'e': {'f': bool}}
    ... ) == {'a': int, 'b': str, 'c': dict, 'e': {'f': bool}}
    True
    >>> t1 == {'a': int, 'b': str, 'c': dict, 'e': {'f': bool}}
    True
    >>> type_tree_union(
    ...    {'a': int, 'b': str, 'c': dict},
    ...    {'c': {'d': t.Any}, 'e': {'f': bool}},
    ...    minimize=True
    ... ) == {'a': int, 'b': str, 'c': {'d': t.Any}, 'e': {'f': bool}}
    True
    >>> type_tree_union({'a': bool}, {'a': str})
    Traceback (most recent call last):
    ...
    TypeError: The key a with value <class 'str'> of
    {'a': <class 'str'>}
    couldn't be added to
    {'a': <class 'bool'>}

    ```
    """
    for key, value in source.items():
        if key not in obj:
            obj[key] = value
            continue

        if isinstance(obj[key], dict) and isinstance(value, dict):
            try:
                type_tree_union(obj[key], value, minimize=minimize)
            except TypeError as e:
                _error_msg = [f"The key \"{key}\" with value \"{value}\" of\n",
                              repr(source), "\n",
                              "couldn't be added to\n",
                              repr(obj)]
                raise TypeError("".join(_error_msg)) from e
            continue

        if issubtype(obj[key], value):
            if not minimize:
                obj[key] = value
            continue

        if issubtype(value, obj[key]):
            if minimize:
                obj[key] = value
            continue

        raise TypeError(f"The key {key} with value {value} of\n" +
                        f"{source}\ncouldn't be added to\n{obj}")

    return obj


def type_tree_difference(
        obj: TypeTree,
        source: TypeTree,
        compare_types: bool = True,
        keep_bigger: bool = True,
) -> TypeTree:
    """
    Take the difference between two type trees.

    Args:
        obj: The big type tree.
        source: The type tree subtracted from `obj`.
        compare_types: If `False`, the type trees are compared only key-wise,
            disregarding the types. If `True`, add the type from `obj` to
            the difference if it is bigger.
        keep_bigger: If `True`, keep the bigger type in `obj` if the types
            are compared.

    **Raises:** `TypeError` for the cases when both type trees have the
        same key, but the values are not comparable.

    **Examples:**
    ```python
    >>> t1 = {'a': int, 'b': {'c': str, 'd': bool}, 'e': dict}
    >>> type_tree_difference(t1,
    ...     {'a': int, 'b': {'c': str}}
    ... ) == {'b': {'d': bool}, 'e': dict}
    True
    >>> type_tree_difference(t1,
    ...     {'b': dict, 'e': {'f': int}}
    ... ) == {'a': int, 'e': dict}
    True
    >>> type_tree_difference(t1,
    ...     {'b': dict, 'e': {'f': int}},
    ...     compare_types=False
    ... ) == {'a': int}
    True
    >>> type_tree_difference(
    ...     {'a': int, 'b': str},
    ...     {'a': str}
    ... )
    Traceback (most recent call last):
    ...
    TypeError: Couldn't compute type tree difference of
    {'a': <class 'int'>, 'b': <class 'str'>}
    and
    {'a': <class 'str'>}
    at key-value:
    "a" -- "<class 'int'>".

    ```
    """
    diff = {}
    for key, value in obj.items():
        if key not in source:
            diff[key] = value
            continue

        if isinstance(value, dict) and isinstance(source[key], dict):
            try:
                diff[key] = type_tree_difference(value, source[key])
            except TypeError as e:
                _error_msg = [f"The key \"{key}\" with value \"{value}\" of\n",
                              repr(obj), "\n",
                              "is bigger than\n",
                              repr(source[key]), "\n",
                              "of\n",
                              repr(source)]
                raise TypeError("".join(_error_msg)) from e
            continue

        if not compare_types:
            continue

        if issubtype(value, source[key]):
            continue

        if issubtype(source[key], value):
            if keep_bigger:
                diff[key] = value

            continue

        _error_msg = ["Couldn't compute type tree difference of\n",
                      repr(obj), "\n",
                      "and\n",
                      repr(source), "\n",
                      "at key-value:\n",
                      f"\"{key}\" -- \"{value}\"."]
        raise TypeError("".join(_error_msg))

    return diff


def type_tree_match(
        obj: TypeTree,
        source: TypeTree,
) -> bool:
    """
    Check if a `dict` that matches the type tree `obj` also matches the
    type tree `source`.

    **Examples:**
    ```python
    >>> type_tree_match(
    ...     {'a': int, 'b': {'c': str}, 'd': bool},
    ...     {'a': t.Union[int, str], 'b': dict}
    ... )
    True
    >>> type_tree_match(
    ...     {'a': t.Union[int, str], 'b': {'c': str}, 'd': bool},
    ...     {'a': int}
    ... )
    False

    ```
    """
    obj = deepcopy(obj)
    source_defaults = deepcopy(source)

    py_.map_values_deep(source_defaults, lambda v, k: type(None))
    py_.defaults_deep(obj, source_defaults)

    return py_.is_match_with(
        obj,
        source,
        issubtype,
    )


def to_typed_dict(
        root_name: str,
        type_tree: TypeTree,
) -> t.Type:
    """Wrap keys in TypedDict named `root_name` recursively."""

    try:
        tree_items = type_tree.items()
    except AttributeError as e:
        _error_msg = ["The argument `type_tree` must be a `dict`. ",
                      "Value of `type_tree`:\n",
                      repr(type_tree)]
        raise AttributeError("".join(_error_msg)) from e

    typed_subdicts = {}

    for k, v in tree_items:
        if isinstance(v, dict):
            typed_subdicts[k] = to_typed_dict(str(k), v)
        else:
            typed_subdicts[k] = v

    return TypedDict(root_name, typed_subdicts)  # type: ignore


def issubtype(
        t1: t.Union[dict, t.Type],
        t2: t.Type,
) -> bool:
    """
    Check if type `t1` is a subtype of `t2`. Warning:
    ! We consider instances of `dict` to be subtypes of the `dict`
    type.
    ! We consider `NoneType` to NOT be a subtype of `Any`.
    ! Both `t1` and `t2` cannot be `dict`s. To compare two type
    trees, use `type_tree_match`.

    **Examples:**
    ```python
    >>> issubtype(str, t.Any)
    True
    >>> issubtype(type(None), t.Any)
    False
    >>> issubtype({'a': int}, dict)
    True
    >>> issubtype(dict, {'a': int})
    False
    >>> issubtype(int, t.Union[int, str]) and issubtype(str, t.Union[int, str])
    True
    >>> issubtype(t.Union[int, str], int)
    False
    >>> issubtype(t.Union[int, str], t.Union[int, str, bool])
    True
    >>> issubtype(int, t.Union[int, None]) \
    and issubtype(type(None), t.Union[int, None])
    True
    >>> issubtype(str, t.Optional[str]) \
    and issubtype(type(None), t.Optional[str])
    True

    ```
    """

    if t2 is t.Any:
        return t1 is not type(None)

    if isinstance(t2, dict):
        return False

    if rt.isa(t1, dict):
        return rt.isa(t1, t2)

    return rt.is_subtype(t1, t2)


def get_type(obj):
    """
    Return the type of `obj`. If `obj` is a function, return `typing.Callable`.

    **Examples:**
    ```python
    >>> get_type(1)
    <class 'int'>
    >>> get_type(lambda x: x)
    typing.Callable
    >>> get_type({'a': 1})
    <class 'dict'>

    ```
    """

    if callable(obj):
        return t.Callable

    return type(obj)
