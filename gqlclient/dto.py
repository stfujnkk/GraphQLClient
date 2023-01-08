from collections.abc import Iterable
from typing_extensions import SupportsIndex


class Dto:
    """Base class of data transmission object.

    Used to automatically wrap build-in list or dict objects for the better code hints.

    Note:
        You should not directly inherit this class, but should inherit DtoDict or DtoList

    """
    __slots__ = ()

    def __new__(cls, v):
        if isinstance(v, Dto):
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            if issubclass(cls, dict):
                return cls(v)
            return DtoDict(v)
        if isinstance(v, Iterable):
            if issubclass(cls, list):
                return cls(v)
            return DtoList(v)
        return v


class DtoDict(dict, Dto):
    """dict-like data transmission object.

    Zero cost compatible dict.You can get the key value of the dict through the object property.
    This class can make the object's attribute and key value of dict consistent forever.
    You can use this class as base classes for complex objects defined in the interface file.

    Note:
        Some special properties can't be obtained through object properties, but only through dict's method.
        Such as get, copy, items, etc. Similarly, they can only be modified by the dict's method.

    Test:
        >>> d = DtoDict({"a":1,"b":[],'c':{}})
        >>> d == {'a': 1, 'b': [], 'c': {}}
        True
        >>> (d.a,d.b,d.c)==(1, [], {})
        True
        >>> d.c = {'x':'hello'}
        >>> d == {'a': 1, 'b': [], 'c': {'x': 'hello'}}
        True
        >>> d.c.x = False
        >>> d == {'a': 1, 'b': [], 'c': {'x': False}}
        True
        >>> d['c']['x'] = 1
        >>> d == {'a': 1, 'b': [], 'c': {'x': 1}}
        True
        >>> d.b=[1]
        >>> d == {'a': 1, 'b': [1], 'c': {'x': 1}}
        True
        >>> d.b[0]={"x":1}
        >>> d == {'a': 1, 'b': [{'x': 1}], 'c': {'x': 1}}
        True
        >>> d.b.append({"y":0})
        >>> d == {'a': 1, 'b': [{'x': 1}, {'y': 0}], 'c': {'x': 1}}
        True
        >>> d.b[0].x = d.b[1].y = 0
        >>> d == {'a': 1, 'b': [{'x': 0}, {'y': 0}], 'c': {'x': 1}}
        True
    """
    __slots__ = ()

    def __init__(self, data: dict = None):
        if data == None:
            return super().__init__()
        if data is self:
            return
        if isinstance(data, DtoDict):
            return super().__init__(data)
        if not isinstance(data, dict):
            raise TypeError(
                f'expected dict-like, but got {data.__class__.__name__}')
        for k, v in data.items():
            self[k] = Dto.__new__(self.__class__, v)

    def _key(self, attrName: str) -> str:
        """
        Map the attribute name to the key of dict
        """
        return attrName

    @classmethod
    def _is_iattr(cls, k: str, *, strict=False):
        code, msg = 0, [
            'Attribute that begin with an underscore',
            'The method of dict',
        ]
        if k.startswith('_'):
            code = 1
        elif k in {
                'clear', 'copy', 'fromkeys', 'get', 'items', 'keys', 'pop',
                'popitem', 'setdefault', 'update', 'values'
        }:
            code = 2
        if code > 0 and strict:
            raise AttributeError(f"{msg[code-1]} is read only")
        return code

    def __setattr__(self, k: str, v):
        if DtoDict._is_iattr(k, strict=True):
            return super().__setattr__(k, v)
        super().__setitem__(self._key(k), Dto.__new__(self.__class__, v))

    def __getattribute__(self, k: str):
        if DtoDict._is_iattr(k):
            return super().__getattribute__(k)
        try:
            return super().__getitem__(self._key(k))
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{k}'")

    def __delattr__(self, k: str):
        if DtoDict._is_iattr(k, strict=True):
            return super().__delattr__(k)
        try:
            return super().__delitem__(self._key(k))
        except KeyError:
            raise AttributeError(k)


class DtoList(list, Dto):
    """list-like data transmission object.

    Zero cost compatible list.
    Ensure all dict-like items of the list are wrapped by DtoDict or it's subclass.

    """
    __slots__ = ()

    def __init__(self, it: Iterable = None):
        if it == None:
            return super().__init__()
        if it is self:
            return
        if isinstance(it, DtoList):
            return super().__init__(it)
        if isinstance(it, Iterable) and not isinstance(
                it, dict) and not isinstance(it, str):
            return super().__init__(Dto.__new__(self.__class__, a) for a in it)
        raise TypeError(f'expected list-like, but got {it.__class__.__name__}')

    def __setitem__(self, i: SupportsIndex, o):
        return super().__setitem__(i, Dto.__new__(self.__class__, o))

    def append(self, o):
        super().append(Dto.__new__(self.__class__, o))

    def extend(self, it: Iterable):
        super().extend(Dto.__new__(self.__class__, it))

    def insert(self, i: SupportsIndex, o):
        super().insert(i, Dto.__new__(self.__class__, o))

    def __iadd__(self, it: Iterable):
        return super().__iadd__(Dto.__new__(self.__class__, it))

    def __add__(self, arr: list):
        return super().__add__(Dto.__new__(self.__class__, arr))
