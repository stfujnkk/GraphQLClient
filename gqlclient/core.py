import abc
from typing import (
    List,
    NewType,
    Union,
)

AccountNumber = NewType('AccountNumber', str)
BigInt = NewType('BigInt', str)
Byte = NewType('Byte', str)
CountryCode = NewType('CountryCode', str)
Currency = NewType('Currency', str)
Date = NewType('Date', str)
DateTime = NewType('DateTime', str)
DID = NewType('DID', str)
Duration = NewType('Duration', str)
EmailAddress = NewType('EmailAddress', str)
HexColorCode = NewType('HexColorCode', str)
Hexadecimal = NewType('Hexadecimal', str)
HSL = NewType('HSL', str)
IPv4 = NewType('IPv4', str)
IPv6 = NewType('IPv6', str)
IBAN = NewType('IBAN', str)
ISBN = NewType('ISBN', str)
JSON = NewType('JSON', str)
JSONObject = NewType('JSONObject', str)
JWT = NewType('JWT', str)
Latitude = NewType('Latitude', str)
LocalDate = NewType('LocalDate', str)
LocalEndTime = NewType('LocalEndTime', str)
LocalTime = NewType('LocalTime', str)
Locale = NewType('Locale', str)
Longitude = NewType('Longitude', str)
MAC = NewType('MAC', str)
NegativeFloat = NewType('NegativeFloat', str)
NegativeInt = NewType('NegativeInt', str)
NonEmptyString = NewType('NonEmptyString', str)
NonNegativeFloat = NewType('NonNegativeFloat', str)
NonNegativeInt = NewType('NonNegativeInt', str)
NonPositiveFloat = NewType('NonPositiveFloat', str)
NonPositiveInt = NewType('NonPositiveInt', str)
ObjectID = NewType('ObjectID', str)
PhoneNumber = NewType('PhoneNumber', str)
Port = NewType('Port', str)
PositiveFloat = NewType('PositiveFloat', str)
PositiveInt = NewType('PositiveInt', str)
PostalCode = NewType('PostalCode', str)
RegularExpression = NewType('RegularExpression', str)
RGB = NewType('RGB', str)
RGBA = NewType('RGBA', str)
RoutingNumber = NewType('RoutingNumber', str)
SafeInt = NewType('SafeInt', str)
Time = NewType('Time', str)
TimeZone = NewType('TimeZone', str)
Timestamp = NewType('Timestamp', str)
URL = NewType('URL', str)
USCurrency = NewType('USCurrency', str)
UTCOffset = NewType('UTCOffset', str)
UUID = NewType('UUID', str)
Void = NewType('Void', str)
Cuid = NewType('Cuid', str)
Ip = NewType('Ip', str)
Semver = NewType('Semver', str)

import warnings
import functools


def deprecated(reason=None, version=None):

    def wrapper(func):

        @functools.wraps(func)
        def wraped_func(*args, **kwargs):
            info = ''
            if version:
                info += f"After version {version}, "
            info += f"{func.__name__} has been deprecated."
            if reason:
                info += f"Because {reason}"
            warnings.warn(info, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wraped_func

    return wrapper


################


class _GQLConfig:
    __slots__ = ('_data', )
    _attr_from = {}

    def __init__(self) -> None:
        self._data = {}

    def __call__(self, value, **kwds):
        if isinstance(value, _GQLConfig):
            self._data = value._data.copy()
        else:
            self._data = {}
        for k, v in kwds.items():
            self._data[f'${k}'] = v

    def _key(self, attrName: str) -> str:
        if attrName.endswith('_'):
            return attrName[:-1]
        return attrName

    def _get_ctx(self, _key: str):
        _data = self._data
        _on_key = self._judge_attr_from(_key)
        if _on_key:
            _on_key = f"... on {_on_key}"
            if _on_key not in _data:
                _data[_on_key] = {}
            _data = _data[_on_key]
        return _data

    @classmethod
    def _judge_attr_from(cls, attrName: str) -> str:
        return cls._attr_from.get(attrName)

    def __setattr__(self, k: str, v):
        if k.startswith('_'):
            return super().__setattr__(k, v)
        _key = self._key(k)
        _data = self._get_ctx(_key)
        _data[_key] = v

    def __getattribute__(self, k: str):
        if k.startswith('_'):
            return super().__getattribute__(k)
        try:
            _key = self._key(k)
            _data = self._get_ctx(_key)
            if _key not in _data:
                _data[_key] = _GQLConfig()
            return _data[_key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{k}'")

    def __delattr__(self, k: str):
        if k.startswith('_'):
            return super().__delattr__(k)
        try:
            _key = self._key(k)
            _on_key = self._judge_attr_from(_key)
            if _on_key:
                if len(self._data[_on_key]) > 1:
                    del self._data[_on_key][_key]
                else:
                    del self._data[_on_key]
                return
            del self._data[_key]
        except KeyError:
            raise AttributeError(k)

# TODO 加入泛型
def parse_gql_param(config) -> str:
    if isinstance(config, _GQLConfig):
        config = config._data
    if isinstance(config, (str, float, int)):
        return str(config)
    if isinstance(config, bool):
        if config:
            return 'true'
        return 'false'
    if isinstance(config, dict):
        return f"{{{','.join({f'{k}:{parse_gql_param(v)}' for k, v in config.items()})}}}"
    return f"[{','.join(parse_gql_param(x) for x in config)}]"


def parse_gql_config(config) -> str:
    if isinstance(config, _GQLConfig):
        config = config._data
    if isinstance(config, str):
        return config
    fields = []
    parms = []
    for k, v in config.items():
        if k.startswith('$'):
            parms.append(f"{k[1:]}:{parse_gql_param(v)}")
        else:
            fields.append(f"{k} {parse_gql_config(v)}")
    rst = ''
    if parms:
        rst += f"({','.join(parms)})"
    if fields:
        rst += f"{{{' '.join(fields)}}}"
    return rst
