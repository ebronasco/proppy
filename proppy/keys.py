"""Contains the `CustomKey` superclass and the `Typed` subclass."""
from abc import ABC, abstractmethod

import typing as t

import runtype as rt


Key = t.Union[str, "CustomKey"]


class CustomKey(ABC):
    """Abstract base class for custom key types."""

    @abstractmethod
    def match(self, other: t.Optional[Key]) -> bool:
        """
        Check that the set of of accepted values for the key `other` is a
        subset of the set of accepted values for the key `self`.
        """
        _error_msg = "The method `match` must be implemented by the subclass."
        raise NotImplementedError(_error_msg)

    @abstractmethod
    def __str__(self) -> str:
        _error_msg = \
            "The method `__str__` must be implemented by the subclass."
        raise NotImplementedError(_error_msg)

    @abstractmethod
    def __eq__(self, other) -> bool:
        _error_msg = \
            "The method `__eq__` must be implemented by the subclass."
        raise NotImplementedError(_error_msg)

    @abstractmethod
    def __hash__(self) -> int:
        _error_msg = \
            "The method `__hash__` must be implemented by the subclass."
        raise NotImplementedError(_error_msg)


class Typed(CustomKey):
    """A custom key that accepts values of a specific type."""

    def __init__(
            self,
            name: str,
            type_=t.Any,
            default=None,
    ):
        self.name = name
        self.type_ = type_

        if not rt.isa(defualt, type_):
            _error_msg = \
                f"The default value must be of type {type_}. Got {default}."
            raise TypeError(_error_msg)

        self.default = default

    def __repr__(self):
        return f"{self.name}: {self.type_} = {self.default}"

    def __str__(self):
        return self.name

    def get_type(self):
        """Return the type of the key."""

        return self.type_

    def get_default(self):
        """Return the default value of the key."""

        return self.default

    def match(self, other):
        """
        Check that the type of `other` is a subtype of `self.type_`.
        If `other` is `None`, check that `self.type_` accepts `None`.
        If `other` is a string, treat is as a key that accepts `typing.Any`.

        Throws a `TypeError` if `other` is not a string or an instance of
        `Typed`.

        **Examples:**
        ```python
        >>> k1 = Typed("x", t.Optional[int])
        >>> k1.match(Typed("x", int))
        True
        >>> k1.match(Typed("x", float))
        False
        >>> k1.match(None)
        True
        >>> k1.match("x")
        False
        >>> k2 = Typed("x", t.Any)
        >>> k2.match(Typed("x", int))
        True
        >>> k2.match(Typed("y", int))
        False
        >>> k2.match(None)
        False
        >>> k2.match("x")
        True
        >>> k2.match(1)
        Traceback (most recent call last):
        ...
        TypeError: The argument `other` must be a string or an \
instance of `Typed`.

        ```
        """

        if other is None:
            return rt.is_subtype(type(None), self.type_) \
                and self.type_ is not t.Any

        if isinstance(other, str):
            return self.name == other \
                and self.type_ is t.Any

        if isinstance(other, Typed):
            return (self.name == other.name) \
                and (rt.is_subtype(other.type_, self.type_))

        _error_msg = \
            "The argument `other` must be a string or an instance of `Typed`."
        raise TypeError(_error_msg)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return (self.name == other.name) and (self.type_ == other.type_)

    def __hash__(self):
        return hash((self.name, self.type_))
